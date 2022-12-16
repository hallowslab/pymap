import secrets
from flask_testing import TestCase

from server import create_flask_app
from server.models import db


class APIV2Test(TestCase):
    """Base test class for all APIV2 endpoints"""

    def create_app(self):
        config = dict(
            SQLALCHEMY_DATABASE_URI="sqlite://",
            TESTING=True,
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SECRET_KEY=str(secrets.SystemRandom()),
            JWT_SECRET_KEY=str(secrets.SystemRandom()),
        )

        # pass in test configuration
        return create_flask_app(config)

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
