from math import e
import os
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from InquirerPy.validator import EmptyInputValidator
from modules.io.io_blockchain import load_block_from_file, clear_block_file, store_block_in_file

from modules.user.Node import Node
from modules.networking.miner_network.miner_client import Request

node_choices = [
    Choice(value="1", name="⏮️ Previous Block"),
    Choice(value="2", name="⏭️ Next Block"),
    Choice(value="3", name="🔢 Enter Block Index"),
    Separator(),
    Choice(value="4", name="✔️ Check block validity"),
    Choice(value="5", name="🚩 Flag block"),
    
    Separator(),
    Choice(value="6", name="🔙 Back"),
]

public_choices = [
    Choice(value="1", name="⏮️ Previous Block"),
    Choice(value="2", name="⏭️ Next Block"),
    Choice(value="3", name="🔢 Enter Block Index"),
    Separator(),
    Choice(value="6", name="🔙 Back"),
]


def block_details_menu_node(node: Node, block_index: int = 0):
    block_index = block_index
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        node.print_block_data(block_index)
        block_index = int(block_index)
        choices = node_choices if hasattr(node, "name") else public_choices
        choice = inquirer.select(
            message="Select an action:",
            choices=choices,
            default=None,
        ).execute()

        if choice == "1":
            if block_index != 0:
                block_index -= 1

        elif choice == "2":
            if block_index != node.length - 1:
                block_index += 1

        elif choice == "3":
            block_index = inquirer.number(
                message="Enter integer:",
                min_allowed=0,
                max_allowed=node.length - 1,
                validate=EmptyInputValidator(),
            ).execute()
        elif choice == "4":
            block = load_block_from_file()
            node.check_block_validity(block, block_index)
            clear_block_file()
            store_block_in_file(block)
            Request.broadcast_block(block)
            input("Press a key to continue...")
        elif choice == "5":
            block = load_block_from_file()
            node.flag_block(block, block_index)
            clear_block_file()
            store_block_in_file(block)
            Request.broadcast_block(block)
            input("Press a key to continue...")
        elif choice == "6":
            break
    return
