import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CryptoGraphs:
    def __init__(self):
        password = "4^%HD7PZ34^%HS645%$YourpasswordKey-014^&FDK".encode()

        salt = b'`y\xcdB`\xc8.\xb8J\xd5\x99\xb6\xfb\x99X\x94'  # must be of type bytes

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        self.key = base64.urlsafe_b64encode(
            kdf.derive(password))  # Can only use kdf once

    def crypto_encrypt_msg(self, data_string):
        encoded_message = data_string.encode()
        f = Fernet(self.key)

        encrypted = f.encrypt(encoded_message)
        encrypted = encrypted.decode()

        return encrypted

    def crypto_decrypt_msg(self, data_string):
        encoded_message = data_string.encode()

        f = Fernet(self.key)
        try:
            decrypted = f.decrypt(encoded_message)
        except InvalidToken:
            return None

        decrypted = decrypted.decode()

        return decrypted
