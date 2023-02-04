from flask_sqlalchemy.model import DefaultMeta

from server.extensions import db

BaseModel: DefaultMeta = db.Model


class CeleryTask(BaseModel):
    __tablename__ = "celery_task"
    id: int = db.Column(db.Integer, primary_key=True)
    source: str = db.Column(db.String(100))
    destination: str = db.Column(db.String(100))
    log_path: str = db.Column(db.String)
    task_id: str = db.Column(db.String)
    n_accounts: int = db.Column(db.Integer)
    domain: str = db.Column(db.String(100), nullable=True)
    archived: bool = db.Column(db.Boolean, default=False)

    owner_username = db.Column(db.String, db.ForeignKey("user.username"))

    def serialize(self):
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
            if c != "__tablename__"
        }

    def __repr__(self):
        return "<Task ID %r: %s -> %s>" % (self.id, self.source, self.destination)
