from app.app import app, db
from users.views import user_bp
from projects.views import project_bp
from accounts.views import account_bp
from activities.views import activity_bp


app.register_blueprint(user_bp)
app.register_blueprint(account_bp)
app.register_blueprint(project_bp)
app.register_blueprint(activity_bp)


if __name__ == "__main__":
    app.run()
