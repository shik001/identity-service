from app.models.user import User, UserCreate, UserUpdate


class TestUser:

    def test_create_user(self):
        user = User(
            email="test@example.com",
            password_hash="hashed_pwd",
        )
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_pwd"
        assert user.email_verified is False
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_extra_fields_ignored(self):
        user = User(
            email="test@example.com",
            password_hash="hashed",
            custom_field="should be ignored",
        )
        assert not hasattr(user, "custom_field")

    def test_defaults(self):
        user = User(email="a@b.com", password_hash="pwd")
        assert user.email_verified is False
        assert user.verification_token is None
        assert user.reset_token is None
        assert user.reset_token_expires is None
        assert user.created_at is not None
        assert user.updated_at is not None


class TestUserCreate:

    def test_create_payload(self):
        data = UserCreate(email="a@b.com", password_hash="hashed")
        assert data.email == "a@b.com"
        assert data.password_hash == "hashed"


class TestUserUpdate:

    def test_all_optional(self):
        data = UserUpdate()
        assert data.email_verified is None
        assert data.verification_token is None
        assert data.reset_token is None
        assert data.password_hash is None

    def test_partial(self):
        data = UserUpdate(email_verified=True)
        assert data.email_verified is True
