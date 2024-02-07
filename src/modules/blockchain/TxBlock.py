from modules.blockchain.BlockChain import CBlock
from modules.blockchain.Signature import sign, verify
from cryptography.hazmat.primitives import hashes, serialization
from modules.io.io_pool import (
    store_transactions_in_memory,
    clear_pool_file,
)
from modules.io.io_blockchain import store_block_in_file
from modules.database.Userbase import get_username_by_public_key
import time
import secrets
from InquirerPy import inquirer
from modules.networking.miner_network.miner_client import Request


REWARD_VALUE = 50.0
leading_zeros = 2
next_char_limit = 120
REWARD = 1


class TxBlock(CBlock):
    def __init__(self, timestamp, previousBlock=None):
        self.nonce = "A random nonce"
        self.flags = {"valid_flags": [], "invalid_flags": []}
        self.valid = False
        self.miner_signature = None
        self.miner_public_key = None
        self.total_fees = 0
        super(TxBlock, self).__init__([], timestamp, previousBlock)

    def addTx(self, Tx_in):
        self.data.append(Tx_in)

    def add_flag(self, private):
        public_key = private.public_key()
        public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        # Check if miner is not trying to add flag
        if verify(self.block_hash, self.miner_signature, public_key):
            print("Miner cannot add flag")
            input("Press a key to continue...")
            return
        # Check if block is valid
        print("Adding a new flag to block 🚩")
        print("\nChecking if block is valid for adding flag...\n")
        if self.is_valid():
            # Check if flag is already in the block flags list
            for signature in self.flags["valid_flags"]:
                if verify(self.block_hash, signature, public_key):
                    print("You already added a flag to this block")
                    input("Press a key to continue...")
                    return
            self.flags["valid_flags"].append(sign(self.block_hash, private))
        else:
            # Check if flag is already in the block flags list
            for signature in self.flags["invalid_flags"]:
                if verify(self.block_hash, signature, public_key):
                    print("You already added a flag to this block")
                    input("Press a key to continue...")
                    return
            self.flags["invalid_flags"].append(sign(self.block_hash, private))

    def is_valid(self):
        # Check the validity of the superblock.
        if not super(TxBlock, self).is_valid():
            print("Invalid superblock\n")
            return False
        else:
            print("Valid superblock\n")

        # Check the validity of the current block.
        print(f"Checking validity of block {self.id}...")

        for tx in self.data:
            if not tx.is_valid():
                print("Block is not valid ⛔")
                self.valid = False
                return False

        # If the block has a specific number of valid flags, it's considered valid.
        if len(self.flags["valid_flags"]) == 3:
            print(f"Block {self.id} is valid 🧱✅")
            self.valid = True
            return True
        return True

    def computeHash(self):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(bytes(str(self.data), "utf8"))
        digest.update(bytes(str(self.previous_hash), "utf8"))
        digest.update(bytes(str(self.timestamp), "utf-8"))
        digest.update(bytes(str(self.nonce), "utf8"))
        return digest.finalize()

    def good_nonce(self):
        return self.block_hash == self.computeHash()

    def find_nonce(self):
        self.nonce = secrets.randbelow(2**256)
        self.block_hash = self.computeHash()
        while not self.block_hash.hex().startswith("0000"):
            self.nonce = secrets.randbelow(2**256)
            self.block_hash = self.computeHash()
        return self.nonce

    def mine(self, miner_public_key, miner_private_key):
        start = time.time()
        while True:
            self.find_nonce()
            self.block_hash = self.calculate_hash()
            print("\nHashing... : ", self.block_hash)
            print("Block hash: ", self.block_hash)
            self.miner_signature = sign(self.block_hash, miner_private_key)
            self.miner_public_key = miner_public_key
            if self.good_nonce():
                print("Found nonce: ", self.nonce)
                self.block_hash = self.calculate_hash()
                print("Block hash: ", self.block_hash)
                print("\n")
                break

        end = time.time()

        print("Block mined in: ", end - start, " seconds ⌛")

        if end - start < 10:
            print("Mining is taking too fast ! 🔥🔥🔥")
            print("Mining is taking less than 10 seconds")

        elif end - start > 20:
            print("Mining is taking too long ! 🐌🐌🐌")
            print("Mining is taking more than 20 seconds")

    def add(self):
        if self.is_valid():
            store_block_in_file(self)

    def select_and_add_transactions(self, tx_pool, miner_address):
        clear_pool_file()
        print("\nGenerating block... ⚙️\n")

        print("Checking if transactions are valid... 🔎\n")
        tx_pool_copy = tx_pool

        valid_txs = [tx for tx in tx_pool if tx.is_valid() and not tx.flag]

        print("\nChecking Reward transactions... 🔎\n")
        reward_txs = [tx for tx in tx_pool if tx.is_valid() and tx.type == REWARD]
        total_txs = len(valid_txs) + len(reward_txs)

        if self.previous_block is None and total_txs < 1:
            if total_txs < 1:
                print("Not enough transactions to create a block. ⛔🧱")
                store_transactions_in_memory(tx_pool)
                input("Press a key to continue...")
                return
        elif self.previous_block is not None and total_txs < 5:
            print("Not enough transactions to create a block. ⛔🧱")
            store_transactions_in_memory(tx_pool)
            input("Press a key to continue...")
            return

        if reward_txs:
            max_reward_txs = 10 - len(self.data)
            reward_txs = reward_txs[:max_reward_txs]
            print(
                f"{len(reward_txs)} Reward transactions found. Adding them to the block. 🧾")
            for tx in reward_txs:
                self.addTx(tx)
                tx_pool.remove(tx)
                valid_txs.remove(tx)

        max_additional_txs = 10 - len(self.data)
        valid_txs = valid_txs[:max_additional_txs]

        choices = [
            {
                "name": f"Transaction: {', '.join([(get_username_by_public_key(in_addr) if get_username_by_public_key(in_addr) is not None else 'REWARD') + ' send ' + str(amount) for in_addr, amount in tx.inputs])} to {', '.join([(get_username_by_public_key(out_addr) if get_username_by_public_key(out_addr) is not None else 'UNKNOWN') + ' receive ' + str(amount) for out_addr, amount in tx.outputs])} (Fee: {round(tx.transaction_fee(),2)})",
                "value": tx,
            }
            for tx in valid_txs
        ]

        try:
            selected_txs = []
            if not choices:
                print(" No additional transactions available for selection.")
                if not reward_txs:
                    print(
                        "No transactions (including rewards) to add to the block. Returning to the menu."
                    )
                    store_transactions_in_memory(tx_pool)
                    return
                else:
                    selected_txs = reward_txs

            if choices:
                if self.previous_block is None:
                    selected_txs = inquirer.select(
                        message="Select transactions to add to the block (use spacebar to select, 'Esc' to quit):",
                        choices=choices,
                        multiselect=True,
                        transformer=lambda result: f"{len(result)} transaction{'s' if len(result) > 1 else ''} selected",
                        max_height="50%",
                        validate=lambda result: 0 <= len(result),
                        invalid_message="It's genesis block, select transactions to continue or press 'Esc' to quit",
                        keybindings={
                            "skip": [{"key": "escape"}],  # Press 'Esc' to quit
                            "toggle": [
                                {"key": "space"},  # Use spacebar to toggle selection
                            ],
                        },
                        mandatory=False,
                    ).execute()

                    if selected_txs is None:
                        # No transactions were selected, or the user aborted the selection process.
                        print(
                            "No transactions selected or operation cancelled. Returning to the menu."
                        )
                        store_transactions_in_memory(tx_pool)
                        return
                else:
                    selected_txs = inquirer.select(
                        message="Select transactions to add to the block (use spacebar to select, 'Esc' to quit):",
                        choices=choices,
                        multiselect=True,
                        transformer=lambda result: f"{len(result)} transaction{'s' if len(result) > 1 else ''} selected",
                        max_height="50%",
                        validate=lambda result: 5 - len(self.data)
                        <= len(result)
                        <= 10 - len(self.data),
                        invalid_message=f"Select between {5- len(self.data)} and {10- len(self.data)} transactions to continue or press 'Esc' to quit",
                        keybindings={
                            "skip": [{"key": "escape"}],  # Press 'Esc' to quit
                            "toggle": [
                                {"key": "space"},  # Use spacebar to toggle selection
                            ],
                        },
                        mandatory=False,
                    ).execute()

                    if selected_txs is None:
                        # No transactions were selected, or the user aborted the selection process.
                        print(
                            "No transactions selected or operation cancelled. Returning to the menu."
                        )
                        store_transactions_in_memory(tx_pool)
                        return

                    ### TODO sum of all selected_fees

                self.total_fees = sum(tx.transaction_fee() for tx in selected_txs)

                for tx in selected_txs:
                    self.addTx(tx)
                    tx_pool.remove(tx)

            print("Selected transactions have been added to the block.")
            print(f"Total fees from selected transactions: {self.total_fees}")
            store_transactions_in_memory(tx_pool)

        except KeyboardInterrupt:
            print("Operation cancelled. Saving the pool and returning to the menu.")
            store_transactions_in_memory(tx_pool_copy)
            return

    def block_must_contain_5_10_transactions(self):
        if self.previous_block is None:
            print("\n It's Genesis block, can be mined ✅ ⛏️")
            return True
        else:
            if len(self.data) >= 5 and len(self.data) <= 10:
                print("\n✅ Block contains : ", len(self.data), " transactions 🧾")
                print("✅ Block could be mined ⛏️")
                return True
            else:
                print(
                    "\n❌❌❌ Block contains : ",
                    len(self.data),
                    " transactions, not enough transactions 🧾",
                )
                print("Block could not be mined ❌⛏️")
                Request.broadcast_miningstop()
                return False

    def block_must_be_mine_until_3_min(self):
        time = self.timestamp - self.previous_block.timestamp

        if time >= 180:
            print("\n Block could be mined 🕢")
            return True

        else:
            print(
                "Block could not be mined, you have to wait : ",
                180 - time,
                " seconds ⏳ ",
            )
        input("Press a key to continue...")
        return False
