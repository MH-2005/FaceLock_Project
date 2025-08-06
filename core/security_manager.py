import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import json
import os


class SecurityManager:
    def __init__(self, password):
        self._password = password.encode('utf-8')
        self._salt = self._get_or_create_salt()
        self._key = self._derive_key()
        self.fernet = Fernet(self._key)

    def _get_or_create_salt(self):
        salt_path = 'config/app.salt'
        if os.path.exists(salt_path):
            with open(salt_path, 'rb') as f:
                return f.read()
        else:
            salt = os.urandom(16)
            os.makedirs('config', exist_ok=True)
            with open(salt_path, 'wb') as f:
                f.write(salt)
            return salt

    def _derive_key(self):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=480000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(self._password))

    @staticmethod
    def hash_password(password):
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        return hashed_password.decode('utf-8')

    @staticmethod
    def verify_password(plain_password, hashed_password):
        plain_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)

    def encrypt_data(self, data):
        if not isinstance(data, bytes):
            data = str(data).encode('utf-8')
        return self.fernet.encrypt(data)

    def decrypt_data(self, encrypted_data):
        if not isinstance(encrypted_data, bytes):
            encrypted_data = encrypted_data.encode('utf-8')
        try:
            return self.fernet.decrypt(encrypted_data)
        except Exception:
            return None

    def save_settings(self, settings_dict, file_path):
        json_data = json.dumps(settings_dict).encode('utf-8')
        encrypted_data = self.encrypt_data(json_data)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)

    def load_settings(self, file_path):
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()

        decrypted_data = self.decrypt_data(encrypted_data)
        if decrypted_data:
            return json.loads(decrypted_data.decode('utf-8'))
        return None