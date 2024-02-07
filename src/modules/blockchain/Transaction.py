from modules.io.io_blockchain import load_block_from_file
from modules.io.io_pool import store_transactions_in_memory
from modules.io.io_pool import get_transactions_from_memory
from modules.blockchain.Signature import *

from collections import defaultdict
from modules.database.Userbase import get_username_by_public_key
from modules.networking.wallet_network.wallet_client import Request
import datetime
import os

REWARD_VALUE = 25.0
SUBSCRIBE_REWARD_VALUE = 50.0
NORMAL = 0
REWARD = 1


class Tx:
    def __init__(self, type=NORMAL):
        self.type = type
        self.inputs = []
        self.outputs = []
        self.sigs = []
        self.reqd = []
        self.flag = False
        self.hash = None
        self.timestamp = datetime.datetime.now()

    def calculate_hash(self):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(bytes(str(self.inputs), "utf8"))
        digest.update(bytes(str(self.outputs), "utf8"))
        digest.update(bytes(str(self.reqd), "utf8"))
        digest.update(bytes(str(self.sigs), "utf8"))
        digest.update(bytes(str(self.flag), "utf8"))
        digest.update(bytes(str(self.type), "utf8"))
        digest.update(bytes(str(self.timestamp), "utf8"))
        return digest.finalize()

    def add_input(self, from_addr, amount):
        self.inputs.append((from_addr, amount))

    def add_output(self, to_addr, amount):
        self.outputs.append((to_addr, amount))

    # UPDATE INPUT AND OUTPUT

    def update_input(self, index, from_addr, amount):
        if 0 <= index < len(self.inputs):
            self.inputs[index] = (from_addr, amount)
        else:
            print("Index out of range for inputs!")

    def update_output(self, index, to_addr, amount):
        if 0 <= index < len(self.outputs):
            self.outputs[index] = (to_addr, amount)
        else:
            print("Index out of range for outputs!")

    # REMOVE INPUT AND OUTPUT

    def remove_input(self, index):
        if 0 <= index < len(self.inputs):
            del self.inputs[index]
        else:
            print("Index out of range for inputs!")

    def remove_output(self, index):
        if 0 <= index < len(self.outputs):
            del self.outputs[index]
        else:
            print("Index out of range for outputs!")

    def add_flag(self, flag):
        self.flag = flag

    def add_reqd(self, addr):
        self.reqd.append(addr)

    def sign(self, private):
        message = self.__gather()
        newsig = sign(message, private)
        self.sigs.append(newsig)

    # TODO before giving flag check also if funds are enough (use verify_funds())
    def is_valid_tx(self):
        if self.is_valid():
            self.flag = False
            print("Transaction is valid, flag removed")
            return True
        else:
            self.flag = True
            print("Transaction is invalid, flag added")
            return False

    def is_valid(self):
        print(f"\nVerifying transaction ...")
        if self.type == REWARD:
            if len(self.inputs) != 0 and len(self.outputs) != 1:
                print("Reward tx should have no inputs and one output ⛔")
                return False
            print("Reward tx is valid ✔️")
            return True

        if len(self.inputs) == 0 or len(self.outputs) == 0:
            print("Invalid Input or Output ☁️")
            return False

        total_in = 0
        total_out = 0
        message = self.__gather()
        for addr, amount in self.inputs:
            found = False
            for s in self.sigs:
                if verify(message, s, addr):
                    found = True
            if not found:
                print("No good sig found for " + str(message) + " 👎")
                return False
            if amount < 0:
                print("Inputs cannot be negative 👎")
                return False
            total_in = total_in + amount
        for addr in self.reqd:
            found = False
            for s in self.sigs:
                if verify(message, s, addr):
                    found = True
            if not found:
                print("No good sig found for " + str(message) + " 👎")
                return False
        for addr, amount in self.outputs:
            if amount < 0:
                print("Outputs cannot be negative 👎")
                return False
            total_out = total_out + amount

        if total_out > total_in:
            print("Outputs exceed inputs 👎")
            return False

        if total_out == 0:
            print("Outputs cannot be 0 👎")
            return False

        if total_in == 0:
            print("Inputs cannot be 0 👎")
            return False
        
        print("Tx is valid ✔️")
        return True

    # check if address from input have enough funds to send
    def aggregate_amounts(data):
        aggregated_values = defaultdict(int)
        for addr, amt in data:
            aggregated_values[addr] += amt
        result_list = list(aggregated_values.items())
        return result_list

    def verify_funds(self):
        os.system("cls" if os.name == "nt" else "clear")
        if self.inputs and self.inputs[0]:
            sender_username = get_username_by_public_key(self.inputs[0][0])
        else:
            sender_username = "Reward"

        if self.outputs and self.outputs[0] and self.outputs[0][0] is not None:
            receiver_username = get_username_by_public_key(self.outputs[0][0])
        else:
            receiver_username = 'reward'

        print(f"New transaction from {sender_username} to {receiver_username}")
       
        print(f"\nVerifying funds ...\n")
        
        for addr, amt in self.inputs:
            confirmed_balance = self.check_balance(addr)
            unconfirmed_balance = self.check_pool_balance(addr)

            print("Confirmed Balance 🍀: ", round(float(confirmed_balance),2))
            print("Unconfirmed Balance ⛔: ", round(float(unconfirmed_balance),2))

            total_balance = confirmed_balance + unconfirmed_balance

            print("Total Balance 💯: ", round(float(total_balance),2))
            print("Amount 💲: ", amt)
            if total_balance < amt:
                return False
        return True

    def verify_funds_update(self, transactions):
        for addr, amt in self.inputs:
            confirmed_balance = self.check_balance(addr)

            # Exclure la transaction actuelle du calcul du solde non confirmé.
            unconfirmed_balance = self.check_pool_balance_update(
                [tx for tx in transactions if tx != self], addr
            )

            print("Confirmed Balance: ", confirmed_balance)
            print("Unconfirmed Balance: ", unconfirmed_balance)

            total_balance = confirmed_balance + unconfirmed_balance

            print("Total Balance: ", round(float(total_balance),2))
            print("Amount: ", amt)

            # Le solde total doit être égal ou supérieur au montant requis pour l'input.
            if total_balance < amt:
                return False
        return True

    # check balance of address in blockchain
    def check_balance(self, addr):
        balance = 0
        blockchain = load_block_from_file()
        while blockchain:
            for tx in blockchain.data:
                for addr_in, amt in tx.inputs:
                    if addr_in == addr:
                        balance = balance - amt
                for addr_out, amt in tx.outputs:
                    if addr_out == addr:
                        balance = balance + amt
            blockchain = blockchain.previous_block
        print("Balance in blockchain: ", balance)
        return balance

    def check_pool_balance(self, addr):
        balance = 0
        transactions = get_transactions_from_memory()

        for tx in transactions:
            for addr_in, amt in tx.inputs:
                if addr_in == addr:
                    balance = balance - amt

        print("Balance in pool: ", round(float(balance),2))
        return balance

    def check_pool_balance_update(self, transactions, addr):
        balance = 0

        for tx in transactions:
            for addr_in, amt in tx.inputs:
                if addr_in == addr:
                    balance = balance - amt

        print("Balance in pool: ", balance)
        return balance

    def add_to_pool(self):
        self.hash = self.calculate_hash()
        transactions = get_transactions_from_memory()

        if any(tx.hash == self.hash for tx in transactions):
            return False

        if not self.is_valid():
            print("Invalid transaction")
            return False
        if not self.verify_funds():
            print("Insufficient funds")
            return False

        transactions.append(self)
        store_transactions_in_memory(transactions)

        print("\nTransaction added to pool")
        Request.broadcast_transaction(self)
        #input("Press a key to continue...")


    def add_to_pool_sync(self):
        transactions = get_transactions_from_memory()

        if any(tx.hash == self.hash for tx in transactions):
            return False

        if not self.is_valid():
            print("Invalid transaction")
            return False
        if not self.verify_funds():
            print("Insufficient funds")
            return False

        transactions.append(self)
        store_transactions_in_memory(transactions)

        print("\nTransaction added to pool")
        Request.broadcast_transaction(self)

    def add_to_pool_update(self, transactions):
        if not self.is_valid():
            print("Invalid transaction")
            return False
        if not self.verify_funds_update(transactions):
            print("Insufficient funds")
            return False
        store_transactions_in_memory(transactions)
        print("Transaction added to pool")
        Request.broadcast_updated_pool(transactions)

    def transaction_fee(self):
        if self.type == REWARD:
            return 0
        total_input = sum([amt for _, amt in self.inputs])
        total_output = sum([amt for _, amt in self.outputs])

        fee = total_input - total_output
        return fee

    def __gather(self):
        data = []
        data.append(self.inputs)
        data.append(self.outputs)
        data.append(self.reqd)
        return data

    def register_transaction(public_key, private_key):
        tx = Tx(type=REWARD)
        Tx.add_output(public_key, 50.0)
        Tx.sign(private_key)

        if Tx.is_valid_tx():
            print("Reward transaction is valid")
            Tx.add_to_pool()

    def __repr__(self):
        repr_str = "INPUTS:\n"
        for addr, amt in self.inputs:
            repr_str = repr_str + str(amt) + "from" + str(addr) + "\n"

        repr_str += "OUTPUTS:\n"
        for addr, amt in self.outputs:
            repr_str = repr_str + str(amt) + "to" + str(addr) + "\n"

        repr_str += "EXTRA REQUIRED SIGNATURES:\n"
        for req_sig in self.reqd:
            repr_str = repr_str + str(req_sig) + "\n"

        repr_str += "SIGNATURES:\n"
        for sig in self.sigs:
            repr_str = repr_str + str(sig) + "\n"

        repr_str += "END\n"

        return repr_str
