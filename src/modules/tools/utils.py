from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
#from Wallet import Wallet
import pickle, os

def compute_hash(data):
    if isinstance(data, str):
        data = bytearray(data, "utf-8")

    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()

# def load_from_file(filename):
#     with open(os.path.join('keys', filename), 'rb') as file:
#         private_serialized, public_serialized = pickle.load(file)
        
#         private_key = serialization.load_pem_private_key(
#             private_serialized,
#             password=None,
#             backend=default_backend()
#         )
        
#         public_key = public_serialized
        
#         return Wallet(private_key, public_key)