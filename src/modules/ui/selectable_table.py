from rich.console import Console
from rich.table import Table
from pynput import keyboard
from colorama import Fore, Style, init
import time
import os

init(autoreset=True)


class SingleSelectTable:
    def __init__(self, headers, data, question="Select an option:"):
        self.question = question
        self.headers = headers
        self.data = data
        self.selected_row = 0
        self.display_updated = True
        self.last_key_time = time.time()
        self.console = Console()
        self.selected_value = None
        self.should_finish = False

        os.system("cls" if os.name == "nt" else "clear")  # Clear the screen

    def display_table(self):
        table = Table(show_header=True, header_style="bold magenta")
        print("❓", self.question)

        for header in self.headers:
            table.add_column(header)

        for i, row in enumerate(self.data):
            if i == self.selected_row:
                table.add_row(
                    *[f"[bold green]{str(entry)}[/bold green]" for entry in row]
                )
                self.selected_value = row
            else:
                table.add_row(*[str(entry) for entry in row])

        self.console.print(table)

    def on_press(self, key):
        current_time = time.time()
        elapsed_time = current_time - self.last_key_time

        if key == keyboard.Key.down or key == keyboard.Key.up:
            os.system("cls" if os.name == "nt" else "clear")  # Clear the screen

        try:
            if key == keyboard.Key.down:
                self.selected_row = min(self.selected_row + 1, len(self.data) - 1)
                self.display_updated = True
            elif key == keyboard.Key.up:
                self.selected_row = max(self.selected_row - 1, 0)
                self.display_updated = True
            elif key == keyboard.Key.enter:
                self.should_finish = True

        except Exception as e:
            print(f"Error: {e}")

        self.last_key_time = current_time

    def run(self):
        with keyboard.Listener(on_press=self.on_press) as listener:
            try:
                while not self.should_finish:
                    if self.display_updated:
                        self.display_table()
                        self.display_updated = False
            except KeyboardInterrupt:
                pass
            finally:
                listener.stop()

        return self.selected_value  # Return the selected value


class MultiSelectTable(SingleSelectTable):
    def __init__(
        self,
        headers,
        data,
        min_selections=None,
        max_selections=None,
        question="Select an options:",
    ):
        super().__init__(headers, data, question)
        self.selected_rows = set()
        self.min_selections = min_selections
        self.max_selections = max_selections

    def display_table(self):
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Select", style="bold cyan", justify="center")
        print("❓", self.question)

        for header in self.headers:
            table.add_column(header)

        for i, row in enumerate(self.data):
            checkbox = "✔️" if i in self.selected_rows else ""
            if i == self.selected_row:
                table.add_row(
                    checkbox,
                    *[f"[bold green]{str(entry)}[/bold green]" for entry in row],
                )
                self.selected_value = row
            else:
                table.add_row(checkbox, *[str(entry) for entry in row])

        self.console.print(table)

    def on_press(self, key):
        current_time = time.time()
        elapsed_time = current_time - self.last_key_time

        if (
            key == keyboard.Key.down
            or key == keyboard.Key.up
            or key == keyboard.Key.space
        ):
            os.system("cls" if os.name == "nt" else "clear")  # Clear the screen

        try:
            if key == keyboard.Key.space:
                if self.selected_row not in self.selected_rows:
                    if (
                        self.max_selections is None
                        or len(self.selected_rows) < self.max_selections
                    ):
                        self.selected_rows.add(self.selected_row)
                    else:
                        print("Maximum selections reached. Cannot select more.")
                else:
                    self.selected_rows.remove(self.selected_row)
                self.display_updated = True
            elif key == keyboard.Key.enter:
                if (
                    self.min_selections is not None
                    and len(self.selected_rows) < self.min_selections
                ):
                    print("Minimum selections not met. Please select more.")
                else:
                    self.should_finish = True

            else:
                super().on_press(key)

        except Exception as e:
            print(f"Error: {e}")

        self.last_key_time = current_time

    def run(self):
        with keyboard.Listener(on_press=self.on_press) as listener:
            try:
                while not self.should_finish:
                    if self.display_updated:
                        self.display_table()
                        self.display_updated = False
            except KeyboardInterrupt:
                pass
            finally:
                listener.stop()

        return [self.data[i] for i in self.selected_rows]  # Return the selected rows


if __name__ == "__main__":
    headers = ["Name", "Age", "City"]
    data = [
        ["John Doe", 28, "New York"],
        ["Jane Smith", 35, "San Francisco"],
        ["Bob Johnson", 42, "Los Angeles"],
    ]

    single_select_table = SingleSelectTable(headers, data)
    selected_value = single_select_table.run()
    print(f"Selected value: {selected_value}")

    multi_select_table = MultiSelectTable(
        headers, data, min_selections=1, max_selections=2
    )
    selected_rows = multi_select_table.run()
    print(f"Selected rows: {selected_rows}")
