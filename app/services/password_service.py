from passlib.context import CryptContext


class PasswordService:

    def __init__(self) -> None:
        self._ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, plain: str) -> str:
        return str(self._ctx.hash(plain))

    def verify(self, plain: str, hashed: str) -> bool:
        return bool(self._ctx.verify(plain, hashed))
