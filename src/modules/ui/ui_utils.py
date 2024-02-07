# from Transaction import Transaction
from modules.io.io_blockchain import load_block_from_file
from rich.console import Console
from rich.table import Table
from modules.database.Userbase import get_username_by_public_key
from datetime import datetime
from rich import box


def print_block(block):
    table = Table(title="Block Info")

    table.add_column("Block", justify="right", style="cyan", no_wrap=True)
    table.add_column(f"# {block.id}", justify="left", style="green")

    table.add_row("timestamp", f"{datetime.fromtimestamp(block.timestamp)}")
    table.add_row("nonce", f"{block.nonce}")
    table.add_row(
        "block_hash",
        f"{block.block_hash.hex() if block.block_hash is not None else None}",
    )
    table.add_row(
        "previous_block_hash",
        f"{block.previous_hash.hex() if block.previous_hash is not None else None}",
    )
    table.add_row("number of transactions", f"{len(block.data)}")
    # table.add_row("transactions", transactions_table(block.data))

    table.add_row(
        "Validity", f"{block.valid}, {len(block.flags['valid_flags'])} valid flags"
    )

    console = Console()
    console.print(table)


def print_block_details(block):
    table = Table(title="Block Details")

    table.add_column("Block", justify="right", style="cyan", no_wrap=True)
    table.add_column(f"# {block.id}", justify="left", style="green")

    table.add_row(
        "Valid Flags",
        f"{'🚩' * len(block.flags['valid_flags']) if len(block.flags['valid_flags']) else '0'}",
    )
    table.add_row(
        "Invalid Flags",
        f"{'🏴‍☠️' * len(block.flags['invalid_flags']) if len(block.flags['invalid_flags']) else '0'}",
    )
    table.add_row("Timestamp", f"{datetime.fromtimestamp(block.timestamp)}")
    table.add_row("Nonce", f"{block.nonce}")
    table.add_row("Block Hash", f"{block.block_hash.hex()}")
    table.add_row(
        "Previous Block Hash",
        f"{block.previous_hash.hex() if block.previous_hash is not None else None}",
    )
    table.add_row("Transactions", transactions_table(block.data))

    console = Console()
    console.print(table)


def transactions_table(transactions):
    tt = Table(
        show_edge=True,
        show_lines=False,
    )

    tt.add_column("Tx No.", justify="left", style="cyan", no_wrap=True)
    tt.add_column("Sender", justify="left", style="green")
    tt.add_column("Receiver", justify="left", style="green")
    tt.add_column("Tx. Value", justify="center", style="green")
    tt.add_column("Tx. Fee", justify="center", style="green")

    for i, tx in enumerate(transactions):
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
            )
            tx_no_appeared = True
    return tt


def print_user_transactions(user):
    table = Table(title="User Transactions")

    table.add_column("Block", justify="right", style="cyan", no_wrap=True)
    table.add_column(f"# {user}", justify="left", style="green")

    block = load_block_from_file()
    while block:
        for tx in block.data:
            if tx.inputs[0][0] == user or tx.outputs[0][0] == user:
                table.add_row(
                    f"{block.id}.",
                    f"{get_username_by_public_key(tx.inputs[0][0]) if len(tx.inputs) > 0 else 'REWARD'}",
                    f"{get_username_by_public_key(tx.outputs[0][0])}",
                    f"{tx.outputs[0][1]}",
                    f"{tx.transaction_fee()}",
                )
        block = block.previous_block

    console = Console()
    console.print(table)


def get_block_with_id(block_id):
    block = load_block_from_file()
    while block:
        if int(block.id) == int(block_id):
            return block
        block = block.previous_block
    return None


def print_user_transactions_table(user):
    console = Console()
    tt = Table(
        box=box.SIMPLE,
        show_edge=True,
        show_lines=False,
        title="User Transactions",
        title_style="bold magenta",
    )

    tt.add_column("Block", justify="right", style="cyan", no_wrap=True)
    tt.add_column("Tx No.", justify="left", style="cyan", no_wrap=True)
    tt.add_column("Sender", justify="left", style="green")
    tt.add_column("Receiver", justify="left", style="green")
    tt.add_column("Tx. Value", justify="right", style="green")
    tt.add_column("Tx. Fee", justify="right", style="green")
    tt.add_column("Time", justify="left", style="green")

    block = load_block_from_file()
    while block:
        tx_number = 0
        block_number_occured = False
        for i, tx in enumerate(block.data):
            if any(inp[0] == user.public_key for inp in tx.inputs) or any(
                output[0] == user.public_key for output in tx.outputs
            ):
                tx_number += 1
                for inp in tx.inputs:
                    if inp[0] == user.public_key:
                        receivers = [
                            get_username_by_public_key(output[0])
                            for output in tx.outputs
                        ]
                        values = [output[1] for output in tx.outputs]
                        tx_no_occured = False
                        for idx, receiver in enumerate(receivers):
                            formatted_row = [
                                f"{'' if block_number_occured else str(block.id)}",
                                f"{'' if tx_no_occured else str(tx_number) + '.'}",
                                f"{get_username_by_public_key(inp[0])}",
                                f"{receiver}",
                                f"{values[idx]*(-1)}",
                                f"{'' if tx_no_occured else round(float(tx.transaction_fee()), 2)}",
                                f"{datetime.fromtimestamp(block.timestamp).strftime('%d/%m/%Y, %H:%M:%S')}",
                            ]
                            formatted_row[
                                4
                            ] = f"[red]{formatted_row[4]}[/red]"  # Tx. Value column
                            formatted_row[
                                5
                            ] = f"[red]{formatted_row[5]}[/red]"  # Tx. Fee column

                            tt.add_row(*formatted_row)
                            tx_no_occured = True
                        block_number_occured = True

                for output in tx.outputs:
                    if output[0] == user.public_key:
                        sender_username = (
                            get_username_by_public_key(tx.inputs[0][0])
                            if len(tx.inputs) > 0
                            else "REWARD"
                        )

                        formatted_row = [
                            f"{'' if block_number_occured else str(block.id)+'.'}",
                            f"{tx_number}.",
                            f"{sender_username}",
                            f"{get_username_by_public_key(output[0])}",
                            f"{output[1]}",
                            f"{round(float(tx.transaction_fee()), 2)}",
                            f"{datetime.fromtimestamp(block.timestamp).strftime('%d/%m/%Y, %H:%M:%S')}",
                        ]
                        tt.add_row(*formatted_row)
                        block_number_occured = True

        block = block.previous_block

    console.print(tt)
