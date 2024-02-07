import os
from modules.database.Userbase import get_user_by_credentials
from modules.user.Node import Node
from modules.database.Userbase import User
from modules.menu.Node_menu import node_menu
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from modules.menu.Explore_blockchain_menu import explore_blockchain_menu
from modules.menu.Settings_menu import settings_menu
from modules.networking.wallet_network.wallet_client import Request
from modules.networking.connected_users import ConnectedUsers

from modules.networking.wallet_network.wallet_server import start_wallet_server
from modules.networking.miner_network.miner_server import start_miner_server


def public_menu(user: User):
    node = Node()
    notification = []
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # Clear the screen
        print(
            f"🌐 Welcome to Goodchain!\n"
            "=========================\n"
            "Goodchain is a blockchain-based coin system that allows you to send and receive coins from other users.\n"
            "Goodchain is a decentralized system, which means that there is no central authority that controls the system.\n"
            "The system is controlled by the users themselves.\n"
        )

        choice = inquirer.select(
            message="Select an action:",
            choices=[
                Choice(value="1", name="🔑 Login"),
                Choice(value="2", name="🔗 Explore the blockchain"),
                Choice(value="3", name="🔐 Sign up"),
                Choice(value="4", name="⚙️ Settings"),
                Choice(value="5", name="👋 Exit"),
            ],
            default=None,
        ).execute()

        if choice == "1":
            os.system("cls" if os.name == "nt" else "clear")
            print("🔑 Login\n=====================\n")
            username = inquirer.text(message="Enter your username:").execute()
            password = inquirer.secret(
                message="Enter desired password:",
                # validate=PasswordValidator(length=8, cap=True, special=True, number=True),
                # transformer=lambda _: "[hidden]",
                # long_instruction="Password require length of 8, 1 cap char, 1 special char and 1 number char.",
            ).execute()

            user_from_db = get_user_by_credentials(username, password)

            if user_from_db:
                user.login(user_from_db)
                if ConnectedUsers.is_user_active(user.username):
                    print("You are already logged in!")
                    input("Press a key to continue...")
                else:
                    ConnectedUsers.add_user(user.username)
                    Request.broadcast_connected_users(user.username)
                    node_menu(user, notification)
            else:
                print("Invalid credentials!")
                input("Press a key to continue...")

        elif choice == "2":
            os.system("cls" if os.name == "nt" else "clear")
            explore_blockchain_menu(node)

        elif choice == "3":
            os.system("cls" if os.name == "nt" else "clear")
            print("🔐 Sign up\n=====================\n")
            username = inquirer.text(message="Enter your username:").execute()
            password = inquirer.secret(
                message="Enter desired password:",
                # validate=PasswordValidator(length=8, cap=True, special=True, number=True),
                # transformer=lambda _: "[hidden]",
                # long_instruction="Password require length of 8, 1 cap char, 1 special char and 1 number char.",
            ).execute()

            if Node.register_user_node(username, password):
                print("Successfully registered!")

            input("Press a key to continue...")

        elif choice == "4":
            os.system("cls" if os.name == "nt" else "clear")
            settings_menu()

        elif choice == "5":
            os.system("cls" if os.name == "nt" else "clear")
            print("Goodbye! 👋")
            print("Exiting...")
            exit(0)

        else:
            os.system("cls" if os.name == "nt" else "clear")
            print("You didn't choose a valid option.")
            input("Press a key to continue...")
