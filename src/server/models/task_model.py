from server import db


class CeleryTask(db.Model):
    __tablename__ = "celery_task"
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(30), unique=False, nullable=False)
    destination = db.Column(db.String(30), unique=False, nullable=False)
    log_path = db.Column(db.String, unique=False, nullable=False)
    task_id = db.Column(db.String, unique=False, nullable=False)

    def __repr__(self):
        return "<Task ID %r: %s -> %s>" % (self.id, self.source, self.destination)
