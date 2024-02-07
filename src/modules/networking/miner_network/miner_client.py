import socket
import pickle
from modules.networking.constants import MINER_TCP_PORT, SERVER_IP, TIMEOUT

class Request:
    def __init__(self, type, data):
        self.type = type
        self.data = data

    @staticmethod
    def send_request(ip_addr, header, data):
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

    @staticmethod
    def send_block(ip_addr, block):
        Request.send_request(ip_addr, "SEND_BLOCK", block)

    @staticmethod
    def broadcast_block(block):
        Request.broadcast_to_nodes("SEND_BLOCK", block)

    @staticmethod
    def broadcast_miningstart():
        Request.broadcast_to_nodes("MINING_START", None)

    @staticmethod
    def broadcast_miningstop():
        Request.broadcast_to_nodes("MINING_STOP", None)

