from cryptography.hazmat.primitives import serialization
from modules.blockchain.Transaction import Tx
import pickle, os

class Wallet:
    def __init__(self, username, private_key, public_key):
        self.username = username
        self.private_key = private_key
        self.public_key = public_key

    def create_transaction(self, outputs):
        New_Tx = Tx()
        summarized_outputs_amount = 0
        for output in outputs:
            summarized_outputs_amount = summarized_outputs_amount + output[1]

        New_Tx.add_input(self.public_key, summarized_outputs_amount)
        for output in outputs:
            New_Tx.add_output(output[0], output[1])
        New_Tx.sign(self.private_key)
        return Tx

    def check_balance(self, blockchain):
        balance = 0
        current_block = blockchain
        while current_block is not None:
            for tx in current_block.data:
                for addr, amt in tx.inputs:
                    if addr == self.public_key:
                        balance = balance - amt
                for addr, amt in tx.outputs:
                    if addr == self.public_key:
                        balance = balance + amt

            current_block = current_block.previous_block
        return balance

    def save_to_file(self, filename):
        private_serialized = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption())

        keys = (private_serialized, self.public_key)

        if not os.path.exists('keys'):
            os.makedirs('keys')

        with open(os.path.join('keys', filename), 'wb') as file:
            pickle.dump(keys, file)
    
    def create_wallet_with_name(name):
    
        private_key, public_key = generate_keys()
        
        wallet = Wallet(name, private_key=private_key, public_key=public_key)
        wallet.save_to_file(f"{name}.keys")
        
        return wallet

    def load_wallet_with_name(username, password):
        user = get_user_by_credentials(username, password)

        if not user:
            raise Exception("User not found, please register first")

        wallet = Wallet(username=user.username, private_key=user.private_key, public_key=user.public_key)
        return user, wallet

    def get_all_wallets_except_current(current_username):
        session = Session()
        
        all_users_except_current = get_all_users_except_current(current_username)
        
        wallets = []
        for user in all_users_except_current:
            user_wallet = Wallet(username=user.username, 
                                 private_key=serialization.load_pem_private_key(user.private_key, password=None),
                                 public_key=user.public_key)
            wallets.append(user_wallet)
        
        session.close()
        return wallets

        
def initialize_wallet(name):
    private_key, public_key = generate_keys()

    return Wallet(name,
        private_key=private_key,
        public_key=public_key,
    )




