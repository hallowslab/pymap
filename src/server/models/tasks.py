from flask_sqlalchemy.model import DefaultMeta

from server.models import db

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
