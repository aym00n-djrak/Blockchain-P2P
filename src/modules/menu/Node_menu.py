from modules.database.Userbase import User
import os
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from modules.user.Node import LoggedInNodeUser
from modules.menu.Settings_menu import settings_menu
from modules.menu.Explore_blockchain_menu_node import explore_blockchain_menu_node
from modules.networking.wallet_network.wallet_client import Request
from modules.networking.connected_users import ConnectedUsers
from modules.networking.wallet_network.wallet_client import Request
from modules.networking.miner_network.miner_client import Request as MinerRequest
def node_menu(user: User, notification):
    node = LoggedInNodeUser(
        private_key=user.private_key,
        public_key=user.public_key,
        name=user.username,
        notification=notification,
    )

    node.notify_block_status()

    try:
        while True:
            os.system("cls" if os.name == "nt" else "clear")  # Clear the screen

            print(
                f"🌐 Welcome to Goodchain: {user.username}!\n",
                "===========================================\n",
            )
            print(f"⚖️  Your balance is: {round(node.wallet_balance, 2)} 💲\n")
            print(f"Blockchain 🔗 Info:")
            print(f"📏 Number of blocks: {node.length} 🧱")
            print(f"💱 Total number of transactions: {node.total_transactions} 🧾\n")

            node.display_notifications()

            choice = inquirer.select(
                message="Select an action:",
                choices=[
                    Choice(value="1", name="🏊 Check Transaction Pool"),
                    Choice(value="2", name="💸 Transfer Coins"),
                    Choice(value="3", name="⛏️ Mine a Block"),
                    Choice(value="4", name="✏️ Update Transaction"),
                    Choice(value="5", name="📜 View Transaction History"),
                    Choice(value="6", name="🔗 View Chain"),
                    Choice(value="7", name="👧 Profile"),
                    Choice(value="8", name="🚪 Logout"),
                ],
                default=None,
            ).execute()

            if choice == "1":
                os.system("cls" if os.name == "nt" else "clear")
                node.see_transaction_pool()
                input("\nPress a key to continue...")

            elif choice == "2":
                os.system("cls" if os.name == "nt" else "clear")
                print(
                    "💸 Transfer Coins \n"
                    "=====================\n"
                    "This is the transfer coins menu. Here you can transfer coins to other users.\n"
                )

                node.transfer_coins()

            elif choice == "3":
                os.system("cls" if os.name == "nt" else "clear")
                print(
                    "⛏️  Mine a Block : "
                    "=====================\n"
                    "This is the mine a block menu. Here you can choose transactions you want to add to a block and mine the block.\n"
                )

                node.mine_block()



            elif choice == "4":
                os.system("cls" if os.name == "nt" else "clear")
                print(
                    "✏️ Update Transaction : "
                    "=====================\n"
                    "This is the update transaction menu. Here you can update transactions that are in the transaction pool.\n"
                )
                node.update_transaction()
                input("\nPress a key to continue...")

                # Add functionality to mine a block.
            elif choice == "5":
                os.system("cls" if os.name == "nt" else "clear")
                print(
                    "📜 Transaction History : "
                    "=====================\n"
                    "This is the transaction history. Here you can view your transactions that you processed.\n"
                )
                node.see_transaction_history()
                input("\nPress a key to continue...")

            elif choice == "6":
                os.system("cls" if os.name == "nt" else "clear")
                print(
                    "🔗 View Chain : "
                    "=====================\n"
                    "This is the view chain menu. Here you can view the blockchain.\n"
                )
                explore_blockchain_menu_node(node)
                input("\nPress a key to continue...")

                # View Profile of an user
            elif choice == "7":
                os.system("cls" if os.name == "nt" else "clear")
                print(
                    "👧 Profile : "
                    "=====================\n"
                    "This is the profile menu. Here you can view your profile and edit account settings.\n"
                )
                node.see_profile()
                settings_menu(user.username)

                # Add functionality to view the user's transaction history.
            elif choice == "8":
                os.system("cls" if os.name == "nt" else "clear")
                print(f"\nGoodbye {user.username}!")
                input("\nPress a key to continue...")
                ConnectedUsers.remove_user(user.username)
                Request.broadcast_disconnected_users(user.username)
                break

            else:
                os.system("cls" if os.name == "nt" else "clear")
                print("\nPlease select a valid option.")

    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
        print("Logged out...")
    finally:
        print("\nReturning to the main menu...")
