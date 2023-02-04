import json

from tests.server.apiv2 import APIV2Test

from server.extensions import guard
from server.extensions import db
from server.models.users import User


class UserFunctionalityTest(APIV2Test):
    """Tests for user functionality"""

    def setUp(self):
        super().setUp()
        # Add test user
        self._user2 = User(
            username="test_user_2",
            password=guard.hash_password("12345"),
            email="test_user_2@test.com",
            roles="operator",
        )
        db.session.add(self._user2)
        db.session.commit()
        # login with user
        res = self.client.post(
            "/api/v2/login",
            data=json.dumps(dict(identifier="test_user_2", password="12345")),
            content_type="application/json",
        )
        # set token and header
        self._token = res.json.get("access_token")
        self._header = {"Authorization": f"Bearer {self._token}"}

    def test_check_token_status(self):
        res = self.client.get("/api/v2/token-status", headers=self._header)
        self.assert200(res)

    def test_logout(self):
        res = self.client.post(
            "/api/v2/logout",
            data=json.dumps(dict(identifier="test_user_2")),
            content_type="application/json",
            headers=self._header,
        )
        self.assert200(res)


class UserManagementTests(APIV2Test):
    """Tests for admin functionality"""

    def setUp(self):
        super().setUp()
        # Add test users and admin
        self._admin = User(
            username="admin",
            password=guard.hash_password("12345"),
            email="test_admin@localhost",
            roles="admin,operator",
        )
        db.session.add(self._admin)
        self._user2 = User(
            username="test_user_2",
            password=guard.hash_password("12345"),
            email="test_user_2@test.com",
            roles="operator",
        )
        db.session.add(self._user2)
        db.session.commit()
        # login with admin
        res = self.client.post(
            "/api/v2/login",
            data=json.dumps(dict(identifier="admin", password="12345")),
            content_type="application/json",
        )
        # set token and header
        self._token = res.json.get("access_token")
        self._header = {"Authorization": f"Bearer {self._token}"}

    def test_add_existing(self):
        res = self.client.post(
            "/api/v2/register",
            data=json.dumps(
                dict(
                    username="test_user_2",
                    password="12345",
                    email="test_user_2@test.com",
                )
            ),
            content_type="application/json",
            headers=self._header,
        )
        self.assert400(res)

    def test_add(self):
        res = self.client.post(
            "/api/v2/register",
            data=json.dumps(
                dict(
                    username="test_user_1",
                    password="12345",
                    email="test_user_1@test.com",
                )
            ),
            content_type="application/json",
            headers=self._header,
        )
        db_user = User.query.filter_by(username="test_user_1").first()

        assert db_user.username == "test_user_1"
        assert db_user.email == "test_user_1@test.com"
        assert guard.authenticate(db_user.username, "12345") is db_user

        db.session.delete(db_user)
        db.session.commit()

    def test_get_account_status(self):
        res = self.client.get(
            "/api/v2/account-status",
            data=json.dumps(dict(identifier="admin")),
            content_type="application/json",
            headers=self._header,
        )
        assert res.json.get("message") == "User admin is Active"

    def test_change_account_status(self):
        user = User.query.filter_by(username="test_user_2").first()
        assert user.is_active is True
        self.client.post(
            "/api/v2/change-account-status",
            data=json.dumps(dict(identifier="test_user_2")),
            content_type="application/json",
            headers=self._header,
        )
        assert user.is_active is False

    def test_change_account_status_invalid(self):
        res = self.client.post(
            "/api/v2/change-account-status",
            data=json.dumps(dict(identifier="NON_EXISTENT_USER")),
            content_type="application/json",
            headers=self._header,
        )
        self.assert404(res)

    def test_unathorized(self):
        res1 = self.client.post(
            "/api/v2/change-account-status",
            data=json.dumps(dict(identifier="NON_EXISTENT_USER")),
        )
        res2 = self.client.post(
            "/api/v2/register",
            data=json.dumps(
                dict(
                    username="test_user_1",
                    password="12345",
                    email="test_user_1@test.com",
                )
            ),
        )
        res3 = self.client.get("/api/v2/account-status")
        self.assert401(res1)
        self.assert401(res2)
        self.assert401(res3)
        # res4 = self.client.get("/api/v2/logout")
        # self.assert401(res4)
