import os
import pickle

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STORAGE_DIR = os.path.join(PROJECT_DIR, "data")
FILENAME = os.path.join(STORAGE_DIR, "block.dat")

os.makedirs(STORAGE_DIR, exist_ok=True)


def store_block_in_file(block):
    temp_file_path = f"{FILENAME}.tmp"
    # Explicitly use a context manager to ensure the file is closed
    with open(temp_file_path, "wb") as file_obj:
        pickle.dump(block, file_obj)
    
    # Make sure the file is closed before we attempt to replace
    try:
        os.replace(temp_file_path, FILENAME)
    except PermissionError as e:
        print(f"Permission error: {e}. Trying to remove the temp file.")
        os.remove(temp_file_path)  # Attempt to remove temporary file if replace fails
    return True


# Load data from file
def load_block_from_file():
    if not os.path.isfile(FILENAME):
        print("File not found, creating a new file 💾")
        open(FILENAME, "a").close()
        return None

    with open(FILENAME, "rb") as loadfile:
        try:
            load_block = pickle.load(loadfile)
        except EOFError:
            return None
        except pickle.UnpicklingError as e:
            print(f"Error loading data: {e}")
            return None
    return load_block


def clear_block_file():
    # Open the file in write mode to clear it
    open(FILENAME, "wb").close()


def is_empty_file():
    return os.path.exists(FILENAME) and os.path.getsize(FILENAME) == 0
