import socket
import pickle
import threading
from modules.networking.constants import WALLET_TCP_PORT, BUFFER_SIZE, SERVER_IP
from modules.database.Userbase import add_user
from modules.io.io_blockchain import load_block_from_file, store_block_in_file, clear_block_file
from modules.io.io_pool import store_transactions_in_memory, get_transactions_from_memory, clear_pool_file
from modules.user.Node import LoggedInNodeUser
from modules.networking.miner_network.miner_state import MinerState
from modules.networking.wallet_network.wallet_client import Request
from modules.database.Userbase import * 
import select
from modules.networking.connected_users import ConnectedUsers
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler('application.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.propagate = False

def newConnection(ip_addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip_addr, WALLET_TCP_PORT))
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

    logger.info(f"WALLET : [NEW CONNECTION] {addr} connected.")

    try:
        ready_to_read, ready_to_write, in_error = select.select([new_sock,], [], [new_sock], 20)

        if len(ready_to_read):
            received_obj = recvObj(new_sock)

            if received_obj.type == "NO_DATA":
                logger.info("Someone pinged the server")
               
            if received_obj.type == "ADD_USER":
                logger.info("Received user registration")
                logger.info(received_obj.data)
                logger.info(f"User : {received_obj.data.username} added to userbase")
                add_user(received_obj.data)

            elif received_obj.type == "UPDATE_NODE_LIST":
                logger.info("Received node list update")
                node_list = NodeList()
                node_list.add_node(received_obj.data)  # Ajouter le nouveau nœud à la liste
                node_list.check_nodes()

            elif received_obj.type == "GET_DB":
                logger.info("Received get remote db request")
                users = get_all_users()
                if users:
                    Request.sync_db(addr[0], users)

            elif received_obj.type == "SYNC_DB":
                logger.info("Received sync db request")
                remote_users = received_obj.data

                if remote_users is not None:
                    for remote_user in remote_users:
                        if not user_exists(remote_user):
                            add_user(remote_user)

            elif received_obj.type == "UPDATE_PASSWORD":
                logger.info("Received update password request")
                update_password(received_obj.data)

            elif received_obj.type == "DELETE_USER":
                logger.info("Received delete user request")
                delete_user(received_obj.data)

            elif received_obj.type == "GET_CONNECTED_USERS":
                logger.info("Received get connected users request")
                ConnectedUsers.add_user(received_obj.data)

            elif received_obj.type == "DISCONNECTED_USERS":
                logger.info("Received disconnected users request")
                ConnectedUsers.remove_user(received_obj.data)

        else:
            logger.info("Connection timeout")
        
    except Exception as e:
        logger.info(f"Exception : {e}")

    finally:
        new_sock.close()
        logger.info(f"WALLET : [CONNECTION CLOSED] {addr} disconnected.")

def start_wallet_server():
    from modules.networking.nodelist import NodeList

    node_list = NodeList()
    server_socket = newConnection(SERVER_IP) 
    logger.info("Wallet Server initialization...")

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
            