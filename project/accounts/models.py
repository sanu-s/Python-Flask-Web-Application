from datetime import datetime

from app.app import db


class ExpiredPlan(db.Model):
    __tablename__ = "expiredplans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=False, nullable=False)
    plan_name = db.Column(db.String(30), unique=False, nullable=False)
    active_days = db.Column(db.Integer, nullable=False, default=15)
    project_count = db.Column(db.Integer, nullable=False, default=5)
    model_quality = db.Column(db.Integer, nullable=False, default=3)
    plan_starts_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)
    plan_expired_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    created_by = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return str(self.user_id)


class CurrentPlan(db.Model):
    __tablename__ = "currentplans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False)
    plan_name = db.Column(db.String(30), unique=False, nullable=False)
    active_days = db.Column(db.Integer, nullable=False, default=15)
    project_count = db.Column(db.Integer, nullable=False, default=5)
    model_quality = db.Column(db.Integer, nullable=False, default=3)
    plan_starts_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)
    plan_expires_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    created_by = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return str(self.user_id)


class FuturePlan(db.Model):
    __tablename__ = "futureplans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=False, nullable=False)
    plan_name = db.Column(db.String(30), unique=False, nullable=False)
    active_days = db.Column(db.Integer, nullable=False, default=15)
    project_count = db.Column(db.Integer, nullable=False, default=5)
    model_quality = db.Column(db.Integer, nullable=False, default=3)
    plan_starts_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)
    plan_expires_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    created_by = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return str(self.user_id)
