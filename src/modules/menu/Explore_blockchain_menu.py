from InquirerPy import inquirer
from InquirerPy.base.control import Choice
import os

from modules.user.Node import Node
from modules.menu.Block_details_menu_node import block_details_menu_node
from InquirerPy.validator import EmptyInputValidator


def explore_blockchain_menu(node: Node):
    os.system("cls" if os.name == "nt" else "clear")
    print(
        "📚 Blockchain Explorer\n"
        "=====================\n"
        "This is the blockchain explorer. Here you can view the blockchain and\n"
        "inspect the data contained in each block.\n"
    )
    print(f"📏 Number of blocks: {node.length}")
    print(f"💱 Total number of transactions: {node.total_transactions}\n")
    choice = inquirer.select(
        message="Select an action:",
        choices=[
            Choice(value="1", name="🔗 Print blockchain"),
            Choice(value="2", name="🏷️ Print block data"),
            Choice(value="3", name="🔙 Back"),
        ],
        default=None,
    ).execute()

    if choice == "1":
        node.print_blockchain()
        input("Press a key to continue...")
    elif choice == "2":
        block_index = inquirer.number(
            message="Enter integer:",
            min_allowed=0,
            max_allowed=node.length - 1,
            validate=EmptyInputValidator(),
        ).execute()
        block_details_menu_node(node, block_index)
    elif choice == "3":
        return

    explore_blockchain_menu(node)
