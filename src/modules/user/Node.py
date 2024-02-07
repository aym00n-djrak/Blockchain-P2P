from modules.blockchain.TxBlock import TxBlock
from cryptography.hazmat.primitives import serialization
from modules.io.io_pool import *
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.table import Table
from InquirerPy.validator import EmptyInputValidator
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from modules.io.io_blockchain import (
    store_block_in_file,
    load_block_from_file,
    is_empty_file,
    clear_block_file,
)
from modules.blockchain.Transaction import Tx
from modules.database.Userbase import get_user_by_credentials, register_user
from datetime import datetime
import os

from InquirerPy import inquirer

from modules.ui.ui_utils import (
    print_block,
    print_block_details,
    print_user_transactions_table,
    get_block_with_id,
)

from modules.networking.miner_network.miner_client import Request
from modules.networking.wallet_network.wallet_client import Request as WalletRequest
from modules.networking.miner_network.miner_state import MinerState


REWARD = 1


class Node:

    @property
    def blockchain(self):
        return load_block_from_file()

    @property
    def length(self):
        length = 0
        block = self.blockchain
        while block is not None:
            length += 1
            block = block.previous_block
        return length

    @property
    def total_transactions(self):
        total_transactions = 0
        block = self.blockchain
        while block is not None:
            total_transactions += len(block.data)
            block = block.previous_block
        return total_transactions

    def initialize_blockchain():
        if is_empty_file():
            print("File is empty ☁️\n")
            print("Creating genesis block ✍🏼")
            genesis = TxBlock(datetime.timestamp(datetime.now()), None)
            timestamp_before_storage = genesis.timestamp
            data_before_storage = genesis.data
            previous_hash_before_storage = genesis.previous_hash
            nonce_before_storage = genesis.nonce
            block_hash_before_storage = genesis.block_hash
            previous_block_before_storage = genesis.previous_block
            return genesis, 0
        else:
            print("File is not empty - loading last block from file 🧱 \n")
            current_block = load_block_from_file()  # valid
            return current_block, 1

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            if not self.is_block_valid(self.chain[i], self.chain[i - 1]):
                return False
        return True

    def print_blockchain(self):
        current_block = self.blockchain
        blocks_list = []
        while current_block is not None:
            blocks_list.append(current_block)
            current_block = current_block.previous_block
        for block in reversed(blocks_list):
            print_block(block)

    def print_block_data(self, block_index):
        block = get_block_with_id(block_index)
        if block is None:
            print(f"Block with id {block_index} not found")
            return
        print_block_details(block)

    def register_user_node(username, password):
        if register_user(username, password):
            print(f"User {username} has been successfully registered")
            print("Loading user ....")
            user_from_db = get_user_by_credentials(username, password)
            print("Initiliazing the wallet with a 50 coins reward transaction")
            tx = Tx(type=REWARD)
            tx.add_output(user_from_db.public_key, 50.0)
            tx.sign(user_from_db.private_key)

            if tx.is_valid_tx():
                print("Reward transaction is valid")
                tx.add_to_pool()

        else:
            print(f"User {username} has not been registered")


class LoggedInNodeUser(Node):
    def __init__(self, private_key, public_key, name, notification):
        super().__init__()
        self.name = name
        self.private_key = private_key
        self.public_key = public_key
        self.notifications = notification
        self.notification_one = True

    def flag_block(self, block, block_index):
        if block is None:
            print(f"Block with id {block} not found")
            return

        if block.id == block_index:
            block.add_flag(self.private_key)
            print(f"Block with id {block.id} has been flagged")

        self.flag_block(block.previous_block, block_index)

    def add_notification(self, message):
        self.notifications.append(message)

    def display_notifications(self):
        if self.notification_one:
            self.notification_one = False
            if self.notifications:
                print("🔔 Notifications:")
                for notification in self.notifications:
                    print(f"- {notification}")
                self.notifications.clear()

    def notify_block_status(self):
        block = load_block_from_file()
        if block:
            if block.block_must_be_verified(self.public_key, self.private_key):
                notification_message = f"Block {block.block_hash.hex()} is verified \n"
                self.add_notification(notification_message)
                os.system("cls" if os.name == "nt" else "clear")

            else:
                notification_message = (
                    f"Block {block.block_hash.hex()} is not verified \n"
                )
                self.add_notification(notification_message)
                print(f"Notification: {notification_message}")
                input("Press a key to continue...")
                os.system("cls" if os.name == "nt" else "clear")
        else:
            notification_message = "There is no block to verify \n"
            self.add_notification(notification_message)
            print(f"Notification: {notification_message}")

    @property
    def loaded_private_key(self):
        key = load_pem_private_key(self.private_key, password=None)
        return key

    def delete_block(self, block_index):
        block = get_block_with_id(block_index)
        if block.valid == True:
            print("Block is valid, cannot be deleted")
            return
        elif len(block.flags['invalid_flags']) >= 3: 
            if block is None:
                print(f"Block with id {block_index} not found")
                return
            print("Deleting block from file 🗑️")
            clear_block_file()

            if block.previous_block != None:
                print("block : ", block.previous_block.id)
                store_block_in_file(block.previous_block)
                tx = block.data   
            else:
                tx = block.data
            for transaction in tx:
                if transaction.is_valid_tx():
                    transaction.add_to_pool()
        else:
            print("Need more invalid flags 🏴‍☠️ to delete the block")

    def delete_current_block(block_index):
        block = get_block_with_id(block_index)
        if block.valid == True:
            print("Block is valid, cannot be deleted")
            return
        else:
            if block is None:
                print(f"Block with id {block_index} not found")
                return
            print("Deleting block from file 🗑️")
            clear_block_file()
            Request.broadcast_block(block.previous_block)

            if block.previous_block != None:
                print("block : ", block.previous_block.id)
                store_block_in_file(block.previous_block)
                Request.broadcast_block(block.previous_block)
            #     tx = block.data   
            # else:
            #     tx = block.data
            # for transaction in tx:
            #     if transaction.is_valid_tx():
            #         transaction.add_to_pool()

    def check_block_validity(self, block, block_index):
        if block is None:
            print(f"Block with id {block_index} not found")
            return None
        if block.id == block_index:
            is_block_valid = block.is_valid()
            if is_block_valid:
                print(f"Block {block_index} validity: {is_block_valid}")
                block.valid = True
                return True
            
        self.check_block_validity(block.previous_block, block_index)



    def update_blocks_after_last_valid_block(block):
        last_valid_block = None

        while block is not None:
            if block.valid:
                last_valid_block = block
                break
            else:
                block.valid = False
            block = block.previous_block

        return last_valid_block

    @property
    def user_transactions(self):
        block = self.blockchain
        transactions = []
        while block:
            for tx in block.data:
                if (
                    tx.inputs[0][0] == self.public_key
                    or tx.outputs[0][0] == self.public_key
                ):
                    transactions.append(tx)
            block = block.previous_block

    @property
    def wallet_balance(self):
        # block = load_block_from_file()
        # if block == None : 
        #     return 0
        summary_balance = self.check_balance() + self.check_pool_balance()
        return summary_balance

    def check_balance(self):
        balance = 0
        current_block = load_block_from_file()

        if current_block is not None:
            if len(current_block.flags['valid_flags']) >= 3:
                for tx in current_block.data:
                    for addr_in, amt in tx.inputs:
                        if addr_in == self.public_key:
                            balance -= amt
                    for addr_out, amt in tx.outputs:
                        if addr_out == self.public_key:
                            balance += amt
            else:
                for tx in current_block.data:
                    for addr_out, amt in tx.inputs:
                        if addr_out == self.public_key:
                            balance -= amt

            block = current_block.previous_block
            while block:
                for tx in block.data:
                    for addr_in, amt in tx.inputs:
                        if addr_in == self.public_key:
                            balance -= amt
                    for addr_out, amt in tx.outputs:
                        if addr_out == self.public_key:
                            balance += amt
                block = block.previous_block
        else:
            print("")
        return balance


    def check_pool_balance(self):
        balance = 0
        transactions = get_transactions_from_memory()

        for tx in transactions:
            for addr_in, amt in tx.inputs:
                if addr_in == self.public_key:
                    balance = balance - amt

        return balance

    def see_balance(self):
        print(f"Wallet Balance: {self.wallet_balance}")

    def mine_block(self):
            pool = get_transactions_from_memory()
            current_block, id = Node.initialize_blockchain()

            if current_block.previous_block is None and id == 0:
                print("Current block is the genesis block 🏁")
                print("Mining on genesis block ⛏️")
                current_block.select_and_add_transactions(pool, self.public_key)
                if current_block.block_must_contain_5_10_transactions():
                    print("Genesis block can be mined ✅")
                    current_block.mine(self.public_key, self.private_key)

                    print("Block_hash: ", current_block.block_hash)
                    print("Calculated block_hash: ", current_block.calculate_hash().hex())
                    print("Storing")
                    store_block_in_file(current_block)
                    Request.broadcast_block(current_block)
                    WalletRequest.broadcast_updated_pool(pool)
                    Request.broadcast_miningstop()
                else:
                    print("Mining cannot start on genesis block ⛔⛔⛔")
                    Request.broadcast_miningstop()
            else:
                print("🚩 Flags : ", len(current_block.flags["valid_flags"]))
                if current_block.valid == True:
                    new_block = TxBlock(datetime.timestamp(datetime.now()), current_block)
                    if new_block.block_must_be_mine_until_3_min():
                        print("Mining on a new block following the previous block ⛏️")
                        save_pool = pool.copy()
                        new_block.select_and_add_transactions(pool, self.public_key)
                        if new_block.block_must_contain_5_10_transactions():
                            print("New block contains 5-10 transactions ✅")
                            print("Mining can start on new block ⚡⚡⚡")
                            new_block.mine(self.public_key, self.private_key)
                            proceed = inquirer.confirm(
                                message="Do you want to send the block to the chain ?",
                                default=True,
                            ).execute()

                            local_block = load_block_from_file()

                            if len(local_block.flags['valid_flags']) >= 3:
                                Request.broadcast_miningstart()
                                if proceed:
                                    print("Block added to the chain ✅")
                                    store_block_in_file(new_block)
                                    Request.broadcast_block(new_block)
                                    WalletRequest.broadcast_updated_pool(pool)
                                    input("Press a key to continue...")
                                    Request.broadcast_miningstop()
                                else:
                                    print("Block not added to the chain ⛔")
                                    pool = save_pool.copy()
                                    store_transactions_in_memory(pool)
                                    print("Transaction pool has been restored ⚠️")
                                    Request.broadcast_miningstop()
                            else:
                                print("Block already added to the chain ⛔")
                                input("Press a key to continue...")
                        else:
                            print("New block does not contain 5-10 transactions ⛔")
                            print("Mining cannot start on new block ⛔")
                            store_transactions_in_memory(save_pool)
                            input("Press a key to continue...")

                else:
                    print("A block is waiting for verification ✋")
                    input("Press a key to continue...")

    def see_transaction_history(self):
        print_user_transactions_table(self)

    def see_transaction_pool(self):
        pool = get_transactions_from_memory()
        print_pool(pool)

    def see_profile(self):
        profile_table = Table(
            title="Profile of " + str(self.name),
            show_header=True,
            header_style="bold magenta",
        )

        profile_table.add_column("Property", style="cyan")
        profile_table.add_column("Value", style="green")

        private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        profile_table.add_row("Private Key", private_key_pem.decode("utf-8"))
        profile_table.add_row("Public Key", self.public_key.decode("utf-8"))
        profile_table.add_row("Wallet Balance", str(self.wallet_balance))

        console = Console()
        console.print(profile_table)

    def see_keys(self):
        print(f"Private Key: {self.private_key}")
        print(f"Public Key: {self.public_key}")
        pass

    def transfer_coins(self):
        try:
            users = get_all_users_except_current(self.name)

            if not users:
                print("No users available for a transfer.")
                return

            # if balance is 0, no transfer can be made and return
            if self.wallet_balance == 0:
                print("You have no coins to transfer.")
                return

            choices = [Choice(user, name=f"{user.username}") for user in users]

            print()
            recipients = inquirer.fuzzy(
                message="Who would you like to transfer money to? (Use spacebar to select multiple recipients, 'Esc' to quit)",
                choices=choices,
                multiselect=True,
                transformer=lambda result: f"{len(result)} recipient{'s' if len(result) > 1 else ''} selected",
                max_height="50%",
                validate=lambda result: len(result) >= 1,
                invalid_message="select at least 1 recipient to continue or press 'Esc' to quit",
                keybindings={
                    "skip": [{"key": "escape"}],
                    "toggle": [
                        {"key": "space"},
                    ],
                },
                mandatory=False,
            ).execute()

            if not recipients or None in recipients:
                return

            transaction_data = []
            print()
            max_allowed = self.wallet_balance

            for recipient in recipients:
                while True:
                    try:
                        amount = inquirer.number(
                            message=f"How many coins would you like to send to {recipient.username}?",
                            min_allowed=float(0),
                            max_allowed=max_allowed,
                            float_allowed=True,
                            validate=EmptyInputValidator(),
                            invalid_message="provided value is incorrect",
                        ).execute()
                        max_allowed -= float(amount)
                        transaction_data.append((recipient, float(amount)))
                        break
                    except ValueError as e:
                        print("Invalid input, please try again.")

            if max_allowed >= 0:
                fee = inquirer.number(
                    message=f"How high is the transfer fee?",
                    min_allowed=float(0),
                    max_allowed=max_allowed,
                    float_allowed=True,
                    validate=EmptyInputValidator(),
                ).execute()
            else:
                print("Insufficient balance to cover transfer fees.")
                return

            input_amount = sum(amount for _, amount in transaction_data) + float(fee)

            Tx2 = Tx()
            Tx2.add_input(self.public_key, input_amount)
            for recipient, amount in transaction_data:
                Tx2.add_output(recipient.public_key, amount)
            Tx2.sign(self.private_key)
            Tx2.add_to_pool()

        except Exception as e:
            print(f"An error occured: {e}")
        finally:
            input("Press a key to continue...")

    def see_notification(self):
        print("Listening for incoming connections...")

    def print_notification(self, message):
        os.system("echo {}".format(message))

    def update_transaction(self):
        update_pool_for_user(self.public_key, self.private_key, self.notifications)


    def print_transaction_pool(self):
        pool = get_transactions_from_memory()
        print_pool(pool)
