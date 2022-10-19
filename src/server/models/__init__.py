from werkzeug.security import generate_password_hash, check_password_hash
from server import db
from flask_sqlalchemy.model import DefaultMeta

BaseModel: DefaultMeta = db.Model


class CeleryTask(BaseModel):
    __tablename__ = "celery_task"
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100), unique=False, nullable=False)
    destination = db.Column(db.String(100), unique=False, nullable=False)
    log_path = db.Column(db.String, unique=False, nullable=False)
    task_id = db.Column(db.String, unique=False, nullable=False)
    n_accounts = db.Column(db.Integer, unique=False, nullable=False)
    domain = db.Column(db.String(100), unique=False, nullable=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return "<Task ID %r: %s -> %s>" % (self.id, self.source, self.destination)


class User(BaseModel):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(130), unique=True, nullable=False)
    _password = db.Column(db.String(100))
    last_login = db.Column(db.DateTime, nullable=True)

    def as_dict(self):
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
            if c.name != "_password"
        }

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
