from werkzeug.security import generate_password_hash, check_password_hash
from server import db


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(130), unique=True, nullable=False)
    _password = db.column(db.String(100))
    last_login = db.Column(db.DateTime, nullable=True)

    @property
    def password(self):
        raise AttributeError("Can't read password")

    @password.setter
    def password(self, password):
        self._password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self._password, password)

    def __repr__(self):
        return "<User %r>" % self.username
