import socket
import pickle
import threading
from modules.networking.constants import MINER_TCP_PORT, BUFFER_SIZE, SERVER_IP
from modules.database.Userbase import add_user
from modules.io.io_blockchain import load_block_from_file, store_block_in_file, clear_block_file
from modules.io.io_pool import store_transactions_in_memory, get_transactions_from_memory, clear_pool_file
from modules.user.Node import LoggedInNodeUser
from modules.networking.miner_network.miner_state import MinerState
from modules.networking.wallet_network.wallet_client import Request
from modules.database.Userbase import * 
import select, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler('application.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.propagate = False

def newConnection(ip_addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip_addr, MINER_TCP_PORT))
    s.listen()
    return s

def recvObj(client_socket):
    all_data = b''
    while True:
        data = client_socket.recv(BUFFER_SIZE)
        if not data:
            break
        all_data += data

    if all_data:
        return pickle.loads(all_data)
    else:
        return Request("NO_DATA", None)


def handle_client(new_sock, addr):
    from modules.networking.nodelist import NodeList

    logger.info(f"MINER : [NEW CONNECTION] {addr} connected.")

    try:
            ready_to_read, ready_to_write, in_error = select.select([new_sock,], [], [new_sock], 20)

            if len(ready_to_read):
                received_obj = recvObj(new_sock)
        
                if received_obj.type == "SEND_BLOCK":
                    logger.info("Received block")
                    clear_block_file()
                    store_block_in_file(received_obj.data)
                    MinerState.stop_mining()

                elif received_obj.type == "MINING_START":
                    logger.info("Received mining start request")
                    MinerState.start_mining()

                elif received_obj.type == "MINING_STOP":
                    logger.info("Received mining stop request")
                    MinerState.stop_mining()

                elif received_obj.type == "SEND_TRANSACTION":
                    logger.info("Received transaction")
                    if received_obj.data.is_valid_tx():
                        received_obj.data.add_to_pool()

                elif received_obj.type == "UPDATE_POOL":
                    logger.info("Received updated pool")
                    clear_pool_file()
                    store_transactions_in_memory(received_obj.data)

                elif received_obj.type == "GET_CHAIN":
                    logger.info("Received get remote chain request")
                    block = load_block_from_file()
                    Request.sync_block(addr[0], block)

                elif received_obj.type == "GET_POOL":
                    logger.info("Received get remote pool request")
                    pool = get_transactions_from_memory()
                    Request.sync_pool(addr[0], pool)

                elif received_obj.type == "SYNC_POOL":
                    logger.info("Received sync pool request")
                    if received_obj.data is not None:
                        local_pool = get_transactions_from_memory()
                        local_block = load_block_from_file()

                        for tx in received_obj.data:
                            if tx not in local_block.data and tx not in local_pool:
                                tx.add_to_pool_sync()

                        local_pool1 = get_transactions_from_memory()
                        local_block1 = load_block_from_file()
                        across_chain_sync(local_block1, local_pool1)

                        for tx in local_pool1:
                            for tx1 in local_pool1:
                                if tx.hash == tx1.hash and tx != tx1:
                                    print("Tx remove")
                                    local_pool1.remove(tx1)      

                        store_transactions_in_memory(local_pool1)   
         
                    else:
                        logger.info("No transactions received for syncing the pool.")

                elif received_obj.type == "SYNC_BLOCK":
                    logger.info("Received sync block request")
                    if received_obj.data is not None:
                        local_block = load_block_from_file()
                        if local_block is None or received_obj.data.timestamp >= local_block.timestamp:
                            clear_block_file()
                            store_block_in_file(received_obj.data)
                    else:
                        logger.info("No block received for syncing.")
            else:
                logger.info("Connection timeout")
    except Exception as e:
        logger.info(f"Exception : {e}")

    finally:
        new_sock.close()
        logger.info(f"MINER : [CONNECTION CLOSED] {addr} disconnected.")

def across_chain_sync(block, pool):
    if block is None:
        return  

    for tx_in_block in block.data:
        for tx_in_pool in pool:
            if tx_in_block.hash == tx_in_pool.hash:
                pool.remove(tx_in_pool)
                break

    across_chain_sync(block.previous_block, pool)




def start_miner_server():
    from modules.networking.nodelist import NodeList

    node_list = NodeList()
    node_list.start_node(SERVER_IP)
    server_socket = newConnection(SERVER_IP) 
    logger.info("Miner Server initialization...")

    while True:
        try:
            new_sock, addr = server_socket.accept()
            node_list.add_to_node_list(addr[0])
            client_thread = threading.Thread(target=handle_client, args=(new_sock, addr))
            client_thread.start()
        except KeyboardInterrupt:
            print("Server shutting down.")
            server_socket.close()
            node_list.check_and_clean_node_list()
            break

        