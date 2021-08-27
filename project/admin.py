from datetime import datetime

from werkzeug.security import generate_password_hash

from app.app import app, db
from users.models import User
from users.views import user_bp
from projects.views import project_bp
from accounts.views import account_bp


# Register Blueprints
app.register_blueprint(user_bp)
app.register_blueprint(account_bp)
app.register_blueprint(project_bp)

# Build the databases
drop_ask = input("Do you want to delete all tables before migration? [y/N]")
if drop_ask.lower().strip() == 'y':
    db.drop_all()
    print("All database tables are droped.")
    print("Trying to create all database tables.")

db.create_all()
print("Database Migration Complete.\n")

if __name__ == "__main__":
    admin_ask = input("Do you want to create an admin user? [y/N]")
    if admin_ask.lower().strip() == 'y':
        print("Creating Admin User Account.\n")

        name = None
        while name is None:
            name = input("Enter name:").strip()
            if len(name) < 3:
                name = None
                print("Name must contain at least 3 characters.")
                continue
            if len(name) > 20:
                name = None
                print("Only 20 characters are allowed for name field")
                continue
            if not name.replace(' ', '').isalpha():
                name = None
                print("Only alphabhets are allowed in name.")
                continue

        email = None
        while email is None:
            email = input("Enter email:").strip()
            if len(email) < 7:
                email = None
                print('Email address is invalid.')
                continue
            email_split = email.split('@')
            if len(email_split) != 2:
                email = None
                print('Email address is invalid.')
                continue
            if '.' not in email_split[1]:
                email = None
                print('Email address is invalid.')
                continue

        password = None
        while password is None:
            password = input("Enter password:").strip()
            if len(password) < 8:
                password = None
                print("password must contain at least 8 characters")
                continue
            if len(password) > 20:
                password = None
                print("password must contain atmost 20 characters")
                continue

        password = generate_password_hash(password, method='sha256')
        user = User(name=name, email=email, password=password, is_admin=True)
        db.session.add(user)
        db.session.commit()
        print("Default Admin User Account Created.")
