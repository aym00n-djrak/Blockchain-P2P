import json, os, socket
from modules.networking.wallet_network.wallet_client import Request
from modules.networking.constants import *
from modules.io.io_blockchain import load_block_from_file
from modules.io.io_pool import get_transactions_from_memory
import pickle

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
STORAGE_DIR = os.path.join(PROJECT_DIR, "data")
FILENAME = os.path.join(STORAGE_DIR, "node_list.json")

class NodeList:
    def __init__(self):
        self.nodes = self.read_node_list(FILENAME)

    def add_node(self, ip):
        self.nodes.add(ip)
        self.write_node_list(FILENAME, self.nodes)

    def remove_node(self, ip):
        self.nodes.discard(ip)
        self.write_node_list(FILENAME, self.nodes)

    def is_node_active(self, ip, port=WALLET_TCP_PORT):
        active = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(TIMEOUT)
                s.connect((ip, port))
                active = True
        except socket.error:
            pass
        return active

    def start_node(self, my_ip):
        if my_ip not in self.nodes:
            self.add_node(my_ip)
            for ip in self.nodes:
                if ip != my_ip:
                   Request.send_node_list_update(ip, my_ip)
        self.sync_block(my_ip)
        self.sync_pool(my_ip)
        self.sync_db(my_ip)

    def check_nodes(self):
        for ip in list(self.nodes):
            if not self.is_node_active(ip):
                self.remove_node(ip)

    def read_node_list(self, file_path):
        if not os.path.isfile(file_path):
            print("Node list file not found, creating a new one.")
            open(file_path, "w").close()
            return set()
        try:
            with open(file_path, 'r') as file:
                node_list = json.load(file)
                return set(node_list)
        except (EOFError, json.JSONDecodeError):
            print("Node list file is empty or corrupted.")
            return set()

    def write_node_list(self, file_path, node_list):
        with open(file_path, 'w') as file:
            json.dump(list(node_list), file)

    def add_to_node_list(self, my_ip):
        if my_ip not in self.nodes:
            self.add_node(my_ip)
            self.write_node_list(FILENAME, self.nodes)
            for ip in self.nodes:
                if ip != my_ip:
                   Request.send_node_list_update(ip, my_ip)

    def check_and_clean_node_list(self):
        for ip in list(self.nodes):
            if not self.is_node_active(ip):
                self.remove_node(ip)
        self.write_node_list(FILENAME, self.nodes)

    def sync_block(self, my_ip):
        for ip in self.nodes:
            if ip != my_ip:
                Request.get_remote_chain(ip)

    def sync_pool(self, my_ip):
        for ip in self.nodes:
            if ip != my_ip:
                Request.get_remote_pool(ip)
    
    def sync_db(self, my_ip):
        for ip in self.nodes:
            if ip != my_ip:
                Request.get_remote_db(ip)


