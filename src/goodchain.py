import threading, logging
from modules.networking.wallet_network.wallet_server import start_wallet_server
from modules.networking.miner_network.miner_server import start_miner_server
from modules.menu.Node_menu import node_menu
from modules.menu.Public_menu import public_menu
from modules.database.Userbase import create_tables, User
from InquirerPy import prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler('application.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.propagate = False

def run_wallet_server():
    logger.info("Starting wallet server...")
    start_wallet_server()

def run_miner_server():
    logger.info("Starting miner server...")
    start_miner_server()

if __name__ == "__main__":
    # Initialize the User instance
    user = User()
    # Initialize/create the necessary tables in the database
    create_tables()

    # Démarrer le serveur dans un thread séparé
    wallet_server_thread = threading.Thread(target=run_wallet_server)
    wallet_server_thread.start()
    logger.info("Wallet Server thread started.")

    miner_server_thread = threading.Thread(target=run_miner_server)
    miner_server_thread.start()
    logger.info("Miner Server thread started.")

    try:
            
        while True:
            if user.is_logged_in:
                # If t(he user is logged in, display the node menu
                node_menu(user)
            else:
                
                prompt_result = prompt([{"type": "input", "message": "Press Enter to start :", "name": "start"}])

                # If the user is not logged in, display the public menu
                public_menu(user)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Exiting...")
        exit(0)
