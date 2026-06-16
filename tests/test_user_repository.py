import pytest

from app.models.user import User
from app.repositories.memory_user_repo import MemoryUserRepository


@pytest.fixture
def repo():
    return MemoryUserRepository()


@pytest.fixture
def sample_user():
    return User(email="test@example.com", password_hash="hashed_pwd")


class TestMemoryUserRepository:

    async def test_create_and_get_by_email(self, repo, sample_user):
        created = await repo.create(sample_user)
        assert created.email == sample_user.email

        fetched = await repo.get_by_email(sample_user.email)
        assert fetched is not None
        assert fetched.password_hash == "hashed_pwd"

    async def test_get_missing(self, repo):
        result = await repo.get_by_email("missing@example.com")
        assert result is None

    async def test_update(self, repo, sample_user):
        await repo.create(sample_user)
        updated = await repo.update(
            sample_user.email,
            {"email_verified": True, "verification_token": "abc123"},
        )
        assert updated is not None
        assert updated.email_verified is True
        assert updated.verification_token == "abc123"

    async def test_update_missing(self, repo):
        result = await repo.update(
            "missing@example.com", {"email_verified": True}
        )
        assert result is None

    async def test_delete(self, repo, sample_user):
        await repo.create(sample_user)
        deleted = await repo.delete(sample_user.email)
        assert deleted is True
        assert await repo.get_by_email(sample_user.email) is None

    async def test_delete_missing(self, repo):
        result = await repo.delete("missing@example.com")
        assert result is False
