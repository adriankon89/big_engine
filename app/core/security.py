from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher


class PasswordHasher:
    def __init__(self):
        # Argon2 jest obecnie najbezpieczniejszym zalecanym algorytmem
        self.password_hash = PasswordHash((Argon2Hasher(),))

    def hash(self, password: str) -> str:
        return self.password_hash.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self.password_hash.verify(plain_password, hashed_password)