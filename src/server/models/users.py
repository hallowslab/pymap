from flask_sqlalchemy.model import DefaultMeta

from server.extensions import db

BaseModel: DefaultMeta = db.Model


class User(BaseModel):
    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(60), unique=True)
    email: str = db.Column(db.String(200), unique=True)
    password: str = db.Column(db.Text)
    roles: str = db.Column(db.Text)
    is_active: bool = db.Column(db.Boolean, default=True, server_default="true")
    last_login: str = db.Column(db.String(20), nullable=True)

    tasks = db.relationship("CeleryTask", backref="user")

    @property
    def identity(self):
        """
        Provides the required attribute or property ``identity``
        """
        return self.id

    @property
    def rolenames(self):
        """
        Provides the required attribute or property ``rolenames``
        """
        try:
            return self.roles.split(",")
        except Exception:
            return []

    @classmethod
    def lookup(cls, username: str):
        """
        Provides the required classmethod ``lookup()``
        """
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id: int):
        """
        Provides the required classmethod ``identify()``
        """
        return cls.query.get(id)
