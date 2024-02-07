import pickle, os
from modules.database.Userbase import get_keys_by_username, get_username_by_public_key
from modules.database.Userbase import get_all_users_except_current
from InquirerPy import inquirer
from InquirerPy.validator import NumberValidator
from rich.console import Console
from rich.table import Table

from modules.networking.wallet_network.wallet_client import Request

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
STORAGE_DIR = os.path.join(PROJECT_DIR, "data")
FILENAME = os.path.join(STORAGE_DIR, "pool.dat")

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(FILENAME), exist_ok=True)


def get_transactions_from_memory():
    if not os.path.isfile(FILENAME):
        print("File not found, creating a new file 4️⃣0️⃣4️⃣")
        open(FILENAME, "ab").close()  # Use 'ab' to create the file in binary mode
        return []
    try:
        with open(FILENAME, "rb") as file_obj:
            current_mem_pool_list = pickle.load(file_obj)
    except (EOFError, pickle.UnpicklingError):
        # Handle the case where the file is empty or corrupted
        print("File is empty or corrupted ☁️")
        current_mem_pool_list = []
    return current_mem_pool_list


def store_transactions_in_memory(transactions):
    temp_file_path = f"{FILENAME}.tmp"
    with open(temp_file_path, "wb") as file_obj:
        pickle.dump(transactions, file_obj)
    os.replace(temp_file_path, FILENAME)


def clear_pool_file():
    open(FILENAME, "wb").close()  # Clear the contents of the file


def print_pool(tx_pool):
    tt = Table(
        show_edge=True,
        show_lines=False,
        title="Pool Transactions",
        title_style="bold magenta",
    )

    tt.add_column("Tx No.", justify="left", style="cyan", no_wrap=True)
    tt.add_column("Sender", justify="left", style="green")
    tt.add_column("Receiver", justify="left", style="green")
    tt.add_column("Tx. Value", justify="center", style="green")
    tt.add_column("Tx. Fee", justify="center", style="green")
    tt.add_column("Tx. Hash", justify="center", style="green")

    for i, tx in enumerate(tx_pool):
        tx_no_appeared = False

        for output in tx.outputs:
            sender_username = (
                get_username_by_public_key(tx.inputs[0][0])
                if len(tx.inputs) > 0
                else "REWARD"
            )
            tt.add_row(
                f"{'' if tx_no_appeared else str(i)+'.'}",
                f"{'' if tx_no_appeared else sender_username}",
                f"{get_username_by_public_key(output[0])}",
                f"{float(output[1])}",
                f"{'' if tx_no_appeared else round(float(tx.transaction_fee()), 2)}",
                f"{'' if tx_no_appeared else tx.hash.hex()}",

            )
            tx_no_appeared = True

    console = Console()
    console.print(tt)


def update_pool(addr):
    tx_pool = get_transactions_from_memory()

    while True:
        print_pool(tx_pool)

        tx_choice = int(
            input(
                "Enter the index of the transaction you want to update (or -1 to exit): "
            )
        )

        if tx_choice == -1:
            print("Exiting...")
            break

        if tx_choice < 0 or tx_choice >= len(tx_pool):
            print("Invalid choice!")
            continue

        tx = tx_pool[tx_choice]

        print("\nCurrent state of the chosen transaction:")
        print(tx)

        print("\nChoose an option to update:")
        print("1. Add input")
        print("2. Update input")
        print("3. Remove input")
        print("4. Add output")
        print("5. Update output")
        print("6. Remove output")
        print("7. Exit")

        choice = int(input("Enter your choice (1-7): "))

        if choice == 1:
            print("\nTransaction:", tx_choice)
            print("Current Inputs:", tx.inputs)
            amt = float(input("Enter amount: "))
            tx.add_input(addr, amt)
            print("Input added")

        elif choice == 2:
            print("\nTransaction:", tx_choice)
            for i, inp in enumerate(tx.inputs):
                print("Input " + str(i) + " : " + str(inp))

            input_choice = int(
                input("Enter the index of the input you want to update: ")
            )

            if addr != tx.inputs[input_choice][0]:
                print("You can only update your own inputs!")
                continue

            amt = float(input("Enter new amount: "))
            tx.update_input(input_choice, addr, amt)
            print("Input updated")

        elif choice == 3:
            print("\nTransaction:", tx_choice)
            for i, inp in enumerate(tx.inputs):
                print("Input " + str(i) + " : " + str(inp))

            input_choice = int(
                input("Enter the index of the input you want to remove: ")
            )

            if addr != tx.inputs[input_choice][0]:
                print("You can only remove your own inputs!")
                continue

            tx.remove_input(input_choice)
            print("Input removed")

        elif choice == 4:
            print("\nTransaction:", tx_choice)
            print("Current Outputs:", tx.outputs)
            amt = float(input("Enter amount: "))
            tx.add_output(addr, amt)
            print("Output added")

        elif choice == 5:
            print("\nTransaction:", tx_choice)
            for i, out in enumerate(tx.outputs):
                print("Output " + str(i) + " : " + str(out))

            output_choice = int(
                input("Enter the index of the output you want to update: ")
            )

            if addr != tx.outputs[output_choice][0]:
                print("You can only update your own outputs!")
                continue

            amt = float(input("Enter new amount: "))
            tx.update_output(output_choice, addr, amt)
            print("Output updated")

        elif choice == 6:
            print("\nTransaction:", tx_choice)
            for i, out in enumerate(tx.outputs):
                print("Output " + str(i) + " : " + str(out))

            output_choice = int(
                input("Enter the index of the output you want to remove: ")
            )

            if addr != tx.outputs[output_choice][0]:
                print("You can only remove your own outputs!")
                continue

            tx.remove_output(output_choice)
            print("Output removed")

        elif choice == 7:
            break

        else:
            print("Invalid choice!")
            continue

        tx_pool[tx_choice] = tx
        store_transactions_in_memory(tx_pool)


def print_from_pool_user_tx(tx_pool, public_key):
    if not tx_pool:
        print("Error: The transaction pool is empty.")
        return

    if not public_key:
        print("Error: Invalid user address provided.")
        return

    found_transactions = False  # Variable pour vérifier si nous avons trouvé des transactions pour cet utilisateur

    # Pour afficher uniquement les transactions pour lesquelles l'utilisateur a effectué des entrées
    for i, tx in enumerate(tx_pool):
        # Vérifier si la transaction a des inputs et si oui, est-ce que l'utilisateur en fait partie
        if not hasattr(tx, "inputs") or not tx.inputs:
            continue

        user_inputs = [inp for inp in tx.inputs if inp[0] == public_key]

        if (
            user_inputs
        ):  # Si l'utilisateur a des entrées dans cette transaction, on l'affiche
            print("Transaction:", i)
            print("Flag:", tx.flag)

            print("Inputs:")
            for inp in user_inputs:
                print(inp)

            print("Outputs:")
            for out in tx.outputs:
                print(out)
            print("-----------------------------------")
            found_transactions = True

    if not found_transactions:
        print("No transactions found for the provided user address.")


def update_pool_for_user(public_key, private_key, notifications):
    tx_pool = get_transactions_from_memory()

    all_users_except_current = get_all_users_except_current(
        get_username_by_public_key(public_key)
    )

    while True:
        user_txs = [tx for tx in tx_pool if public_key in [inp[0] for inp in tx.inputs]]
        user_txs_info = [
            {
                "name": f"Transaction: {', '.join([get_username_by_public_key(in_addr) if in_addr else 'REWARD' + ' send ' + str(amount) for in_addr, amount in tx.inputs])} to {', '.join([get_username_by_public_key(out_addr) + ' receive ' + str(amount) for out_addr, amount in tx.outputs])} (Fee: {round(tx.transaction_fee(), 2)}))",
                "value": tx,
            }
            for tx in user_txs
        ]

        if not user_txs_info:
            print("No transactions found for this user.")
            break

        user_txs_info.append({"name": "Exit", "value": None})
        selected_tx_info = inquirer.select(
            message="Select the transaction you want to update or exit:",
            choices=user_txs_info,
        ).execute()

        if selected_tx_info is None:
            print("Exiting...")
            break

        selected_tx = selected_tx_info

        text = f"Transaction: {', '.join([get_username_by_public_key(in_addr) if in_addr else 'REWARD' + ' send ' + str(amount) for in_addr, amount in selected_tx.inputs])} to {', '.join([get_username_by_public_key(out_addr) + ' receive ' + str(amount) for out_addr, amount in selected_tx.outputs])} (Fee: {round(selected_tx.transaction_fee(), 2)}))"

        action_choices = ["Update", "Delete", "Exit"]
        action_choice = inquirer.select(
            message="Do you want to Update or Delete an input, or Exit?",
            choices=action_choices,
        ).execute()

        if action_choice == "Exit":
            print("Exiting update...")
            break

        if action_choice == "Update":
            input_choices = [
                {
                    "name": f"Input {i}: {amount} from {get_username_by_public_key(addr)}",
                    "value": i,
                }
                for i, (addr, amount) in enumerate(selected_tx.inputs)
                if addr == public_key
            ]

            input_choice = inquirer.select(
                message="Select the input you want to update:",
                choices=input_choices,
            ).execute()

            new_amt = inquirer.text(
                message="Enter new amount:",
                validate=NumberValidator(float_allowed=True),
            ).execute()

            new_amt = float(new_amt)
            selected_tx.inputs[input_choice] = (public_key, new_amt)
            total_input = sum(
                amt for addr, amt in selected_tx.inputs if addr == public_key
            )
            selected_tx.outputs.clear()

            total_input = sum(
                amt for addr, amt in selected_tx.inputs if addr == public_key
            )

            # ask for fees

            fee = inquirer.text(
                message="Enter fees value:",
                validate=NumberValidator(float_allowed=True),
            ).execute()

            remaining_input = total_input - float(fee)

            while remaining_input > 0:
                recipient_choices = [
                    {"name": user.username, "value": user}
                    for user in all_users_except_current
                ]
                recipient_username = inquirer.select(
                    message="Select recipient username:",
                    choices=recipient_choices,
                ).execute()

                keys = get_keys_by_username(recipient_username.username)
                amount_to_send = inquirer.text(
                    message=f"Enter amount to send to {recipient_username.username} (Available: {remaining_input}):",
                    validate=NumberValidator(float_allowed=True),
                ).execute()
                amount_to_send = float(amount_to_send)

                if 0 < amount_to_send <= remaining_input:
                    selected_tx.add_output(keys[1], amount_to_send)
                    remaining_input -= amount_to_send
                else:
                    print(
                        "Invalid amount. Please enter a value greater than 0 and up to the available amount."
                    )

            selected_tx.sign(private_key)
            selected_tx.calculate_hash()

            if selected_tx.is_valid_tx():
                print("Transaction is valid, flag removed")
                index = tx_pool.index(selected_tx_info)
                tx_pool[index] = selected_tx
                if selected_tx.add_to_pool_update(tx_pool):
                    print("Transaction updated in pool")
                else:
                    tx_pool = get_transactions_from_memory()
                    updated_text = f"Transaction: {', '.join([get_username_by_public_key(in_addr) if in_addr else 'REWARD' + ' send ' + str(amount) for in_addr, amount in selected_tx.inputs])} to {', '.join([get_username_by_public_key(out_addr) + ' receive ' + str(amount) for out_addr, amount in selected_tx.outputs])} (Fee: {round(selected_tx.transaction_fee(), 2)}))"
                    print("updated_text", updated_text)
                    notifications.append(
                        f"Updated transaction: \n Old : {text} \n New : {updated_text}\n"
                    )
                    continue
            else:
                tx_pool = get_transactions_from_memory()

        elif action_choice == "Delete":
            if not selected_tx.inputs:
                print("No inputs available to delete.")
                continue

            input_choices = [
                {
                    "name": f"Input {i}: {amount} from {get_username_by_public_key(addr)}",
                    "value": i,
                }
                for i, (addr, amount) in enumerate(selected_tx.inputs)
                if addr == public_key
            ]
            input_choices.append({"name": "Cancel", "value": -1})

            del_input_choice = inquirer.select(
                message="Select the input you want to delete or cancel:",
                choices=input_choices,
            ).execute()

            if del_input_choice == -1:
                continue

            deleted_input = selected_tx.inputs[del_input_choice]

            deleted_txt = f"Transaction: {', '.join([get_username_by_public_key(in_addr) if in_addr else 'REWARD' + ' send ' + str(amount) for in_addr, amount in selected_tx.inputs])} to {', '.join([get_username_by_public_key(out_addr) + ' receive ' + str(amount) for out_addr, amount in selected_tx.outputs])} (Fee: {round(selected_tx.transaction_fee(), 2)}))"

            selected_tx.inputs.pop(del_input_choice)

            selected_tx.outputs.clear()

            if not selected_tx.inputs:
                tx_pool.remove(selected_tx)
                store_transactions_in_memory(tx_pool)
                Request.broadcast_updated_pool(tx_pool)
                print("Transaction removed, no inputs left.")
                print("deleted_txt", deleted_txt)
                notifications.append(f"Deleted transaction: \n {deleted_txt}\n")
                continue
