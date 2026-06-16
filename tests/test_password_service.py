from app.services.password_service import PasswordService


class TestPasswordService:

    def setup_method(self) -> None:
        self.service = PasswordService()

    def test_hash_and_verify(self):
        hashed = self.service.hash("my_secret_password")
        assert self.service.verify("my_secret_password", hashed)

    def test_wrong_password_fails(self):
        hashed = self.service.hash("correct_password")
        assert not self.service.verify("wrong_password", hashed)

    def test_same_plain_produces_different_hashes(self):
        hash1 = self.service.hash("password")
        hash2 = self.service.hash("password")
        assert hash1 != hash2
