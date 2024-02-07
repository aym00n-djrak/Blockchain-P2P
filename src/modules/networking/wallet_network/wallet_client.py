import socket
import pickle
from modules.networking.constants import WALLET_TCP_PORT, MINER_TCP_PORT, SERVER_IP, TIMEOUT

class Request:
    def __init__(self, type, data):
        self.type = type
        self.data = data

    @staticmethod
    def send_request(ip_addr, header, data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(TIMEOUT)
                s.connect((ip_addr, WALLET_TCP_PORT))
                request = Request(header, data)
                serialized_request = pickle.dumps(request)
                s.sendall(serialized_request)
        except socket.error as e:
            print(f"Error sending request to {ip_addr}: {e}")

    def send_request_to_miner_server(ip_addr, header, data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(TIMEOUT)
                s.connect((ip_addr, MINER_TCP_PORT))
                request = Request(header, data)
                serialized_request = pickle.dumps(request)
                s.sendall(serialized_request)
        except socket.error as e:
            print(f"Error sending request to {ip_addr}: {e}")

    @staticmethod
    def broadcast_to_nodes(header, data):
        from modules.networking.nodelist import NodeList

        node_list = NodeList().nodes
        for ip_addr in node_list:
            if ip_addr != SERVER_IP:
                Request.send_request(ip_addr, header, data)

    def broadcast_to_miner_server(header, data):
        from modules.networking.nodelist import NodeList

        node_list = NodeList().nodes
        for ip_addr in node_list:
            if ip_addr != SERVER_IP:
                Request.send_request_to_miner_server(ip_addr, header, data)

    @staticmethod
    def send_user_registration(ip_addr, user):
        Request.send_request(ip_addr, "ADD_USER", user)

    @staticmethod
    def broadcast_user_registration(user):
        Request.broadcast_to_nodes("ADD_USER", user)

    @staticmethod
    def send_transaction(ip_addr, transaction):
        Request.send_request_to_miner_server(ip_addr, "SEND_TRANSACTION", transaction)

    @staticmethod
    def broadcast_transaction(transaction):
        Request.broadcast_to_miner_server("SEND_TRANSACTION", transaction)

    @staticmethod
    def send_updated_pool(ip_addr, pool):
        Request.broadcast_to_miner_server(ip_addr, "UPDATE_POOL", pool)

    @staticmethod
    def sync_pool(ip_addr, pool):
        Request.send_request_to_miner_server(ip_addr, "SYNC_POOL", pool)

    @staticmethod
    def sync_block(ip_addr, block):
        Request.send_request_to_miner_server(ip_addr, "SYNC_BLOCK", block)

    @staticmethod
    def sync_db(ip_addr, db):
        Request.send_request(ip_addr, "SYNC_DB", db)

    @staticmethod
    def broadcast_updated_pool(pool):
        Request.broadcast_to_miner_server("UPDATE_POOL", pool)

    @staticmethod
    def send_node_list_update(ip_addr, new_ip):
        Request.send_request(ip_addr, "UPDATE_NODE_LIST", new_ip)

    @staticmethod
    def broadcast_node_list_update(new_ip):
        Request.broadcast_to_nodes("UPDATE_NODE_LIST", new_ip)

    @staticmethod
    def broadcast_update_password(user):
        Request.broadcast_to_nodes("UPDATE_PASSWORD", user)

    @staticmethod
    def broadcast_delete_user(user):
        Request.broadcast_to_nodes("DELETE_USER", user)

    @staticmethod
    def get_remote_chain(ip_addr):
        Request.send_request_to_miner_server(ip_addr, "GET_CHAIN", None)

    @staticmethod
    def get_remote_pool(ip_addr):
        Request.send_request_to_miner_server(ip_addr, "GET_POOL", None)

    @staticmethod
    def get_remote_db(ip_addr):
        Request.send_request(ip_addr, "GET_DB", None)

    @staticmethod
    def get_connected_users(ip_addr, user):
        Request.send_request(ip_addr, "GET_CONNECTED_USERS", user)

    @staticmethod
    def broadcast_connected_users(user):
        Request.broadcast_to_nodes("GET_CONNECTED_USERS", user)

    @staticmethod
    def send_disconnected_users(ip_addr, user):
        Request.send_request(ip_addr, "DISCONNECTED_USERS", user)

    @staticmethod
    def broadcast_disconnected_users(user):
        Request.broadcast_to_nodes("DISCONNECTED_USERS", user)