# encryption.py
import os
from cryptography.fernet import Fernet

def get_or_create_master_key():
    if not os.path.exists("secret.key"):
        master_key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(master_key)
    return open("secret.key", "rb").read()

def encrypt_data(raw_text):
    master_key = get_or_create_master_key()
    f = Fernet(master_key)
    return f.encrypt(raw_text.encode()).decode()

def decrypt_data(encrypted_text):
    master_key = get_or_create_master_key()
    f = Fernet(master_key)
    return f.decrypt(encrypted_text.encode()).decode()