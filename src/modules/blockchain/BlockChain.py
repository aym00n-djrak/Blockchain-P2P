from datetime import datetime
from cryptography.hazmat.primitives import hashes
from modules.database.Userbase import get_username_by_public_key
from modules.blockchain.Transaction import Tx
from modules.io import io_blockchain
from modules.networking.miner_network.miner_client import Request

now = datetime.now()
ts = datetime.timestamp(now)

REWARD = 1
REWARD_VALUE = 50.0

class CBlock:
    def __init__(self, data, timestamp, previous_block):
        self.data = data
        self.block_hash = None
        self.timestamp = timestamp
        self.previous_block = previous_block
        self.previous_hash = None
        if previous_block != None:
            self.previous_hash = previous_block.calculate_hash()
        
    @property
    def id(self):
        if self.previous_block == None:
            return 0
        else:
            return self.previous_block.id + 1

    def calculate_hash(self):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(bytes(str(self.data), "utf8"))
        digest.update(bytes(str(self.previous_hash), "utf8"))
        digest.update(bytes(str(self.timestamp), "utf8"))
        digest.update(bytes(str(self.nonce), "utf8"))

        return digest.finalize()

    def is_valid(self):
        previous_block_computed_hash = (
            self.previous_block.calculate_hash()
            if self.previous_block != None
            else None
        )

        if self.previous_block == None:
            if self.block_hash == self.calculate_hash():
                return True
            else:
                self.valid = False
                return False
        else:
            current_block_validity = self.block_hash == self.calculate_hash()
            print(f"\nBlock {self.id} Integrity ✅: ", current_block_validity)
            if current_block_validity == False:
                self.valid = False
            previous_block_validity = self.previous_block.is_valid()

            if previous_block_computed_hash != self.previous_hash:
                previous_block_validity = False
                self.valid = False
                
            print(f"Block {self.previous_block.id} validity ✅: ", previous_block_validity)
            return current_block_validity and previous_block_validity

    def block_must_be_verified(self, user_public_key, user_private_key): 

        if self.valid == False:
            if user_public_key != self.miner_public_key:
                if self.is_valid():
                    print("🚩 Flags : ", len(self.flags['valid_flags']))
                    self.add_flag(user_private_key)
                    io_blockchain.clear_block_file()
                    io_blockchain.store_block_in_file(self)
                    if len(self.flags['valid_flags']) == 3:
                        self.valid = True
                        print("Block is valid 🧱✅")
                        print("💰💰💰 Adding Reward transaction to pool for miner : ", get_username_by_public_key(self.miner_public_key))
                        reward_tx = Tx(REWARD)
                        reward_tx.add_output(self.miner_public_key, REWARD_VALUE + self.total_fees)
                        if reward_tx.is_valid_tx():
                            reward_tx.add_to_pool()
                            print("\nReward transaction added to pool 💰💾\n")

                        io_blockchain.clear_block_file()
                        io_blockchain.store_block_in_file(self)
                        Request.broadcast_block(self)
                    else:
                        print("Valid Flag added to block ➕🚩")
                        io_blockchain.clear_block_file()
                        io_blockchain.store_block_in_file(self)
                        Request.broadcast_block(self)
                else:
                    print("Block is not valid ⛔")
                    self.add_flag(user_private_key)
                    io_blockchain.clear_block_file()
                    io_blockchain.store_block_in_file(self) 
                    Request.broadcast_block(self)

                    print("🏴‍☠️ Flags : ", len(self.flags['invalid_flags']))

                    if len(self.flags['invalid_flags']) >= 3:
                        print("Block is invalid ⛔")
                        print("Patching the chain...")
                        self.check_block_validity_patch()                      
            else:
                print("The miner can't verify his own block ! ✋")
        else:
            print("Block is already valid ✊👌")
        return self.valid

        
        
    def check_block_validity_patch(self):
        from modules.user.Node import LoggedInNodeUser as Node
        from modules.io.io_blockchain import load_block_from_file, store_block_in_file
        
        block = load_block_from_file()

        is_block_valid = block.is_valid()

        print(f"Block {block.id} validity: {is_block_valid}")
        store_block_in_file(block)
        Request.broadcast_block(block)

        if not is_block_valid:
            last_valid_block = Node.update_blocks_after_last_valid_block(block)

            input("Going to delete blocks after last valid block. Press a key to continue...")

            if last_valid_block is not None:
                current_block = load_block_from_file()  
                while current_block is not None and current_block.id > last_valid_block.id:
                    Node.delete_current_block(current_block.id)
                    current_block = current_block.previous_block
            else:
                current_block = load_block_from_file()  
                while current_block is not None and current_block.id >=0:
                    Node.delete_current_block(current_block.id)
                    current_block = current_block.previous_block

                return last_valid_block
        else:
            return True