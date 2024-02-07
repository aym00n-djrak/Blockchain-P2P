from InquirerPy import inquirer
from InquirerPy.base.control import Choice
import os
from modules.database.Userbase import (
    change_password,
    delete_account,
)


def settings_menu(username=None):
    if not username:
        os.system("cls" if os.name == "nt" else "clear")
    print(
        "⚙️  Settings\n"
        "=====================\n"
        "This is the settings menu. Here you can change your password or delete your account.\n"
    )
    choice = inquirer.select(
        message="Select an action:",
        choices=[
            Choice(value="1", name="🔗 Change a password"),
            Choice(value="2", name="❗ Delete account"),
            Choice(value="3", name="🔙 Back"),
        ],
        default=None,
    ).execute()

    if choice == "1":
        os.system("cls" if os.name == "nt" else "clear")
        print("🔗 Change a password\n=====================\n")
        if not username:
            username = inquirer.text(message="Enter your username:").execute()
        result = change_password(username)
        if result:
            print("✅ Password changed successfully!")
        else:
            print("❌ Password change failed!")

        input("Press a key to continue...")

    if choice == "2":
        os.system("cls" if os.name == "nt" else "clear")
        print("❗Delete account\n=====================\n")
        if not username:
            username = inquirer.text(message="Enter your username:").execute()
        result = delete_account(username)
        if result:
            print("✅ Account deleted successfully!")
        else:
            print("❌ Account deletion failed!")

        input("Press a key to continue...")

    if choice == "3":
        return

    settings_menu()
