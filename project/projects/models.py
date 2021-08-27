from datetime import datetime

from sqlalchemy.dialects.postgresql import JSON

from app.app import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=False, nullable=False)
    description = db.Column(db.String(1000), unique=False, nullable=False)
    tags = db.Column(JSON)
    file_name = db.Column(db.String(400), unique=False, nullable=False)
    file_rows = db.Column(db.Integer, default=0, nullable=True)
    file_columns = db.Column(db.Integer, default=0, nullable=True)
    model_target = db.Column(db.String(200), unique=False, nullable=True)
    model_count = db.Column(db.Integer, default=0, nullable=True)
    model_accuracy = db.Column(db.String(50), unique=False, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    created_by = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return self.name
