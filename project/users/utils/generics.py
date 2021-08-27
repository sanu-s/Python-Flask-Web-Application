from os import path
from base64 import b64encode

from werkzeug.security import check_password_hash

from app.app import db
from config import accounts
from projects.models import Project
from users.models import User, Reason
from config.users import ALLOWED_PICS
from core.fileprocess import get_profile_thumbnail_dir


class UserValidation:
    def verify_name(self, name):
        if len(name) < 3:
            return False, "Name must be contain 3 characters"
        if len(name) > 20:
            return False, "Only 20 characters are allowed for name field"
        if not name.replace(' ', '').isalpha():
            return False, "Only alphabhets are allowed as name."
        return True, "Success"

    def verify_email(self, email):
        if len(email) < 7:
            return False, "Invalid email address"
        email_split = email.split('@')
        if len(email_split) != 2:
            return False, "Invalid email address"
        if '.' not in email_split[1]:
            return False, "Invalid email address"
        extension = email_split[1].split('.')
        if not extension[-1].isalpha():
            return False, "Invalid email address"
        return True, "Success"

    def verify_passwords(self, password1, password2):
        if password1 != password2:
            return False, "Mismatched passwords"
        if len(password1) < 8:
            return False, "Password must contain 8 characters"
        if len(password1) > 20:
            return False, "Password must not exceed 20 characters"
        return True, password1

    def verify_admin(self, admin):
        if not isinstance(admin, bool):
            return False, "Boolean value required as admin"
        return True, "Success"

    def check_email_exist(self, email):
        user = User.query.filter_by(email=email).first()
        if user is None:
            return False, "User account does not exist"
        return True, user

    def allowed_profile_pics(self, filename):
        return '.' in filename and filename.rsplit('.')[-1].lower() in ALLOWED_PICS

    def get_icon(self, media_root, user_id):
        icon = None
        icon_dir = get_profile_thumbnail_dir(media_root, user_id)
        if path.isdir(icon_dir):
            icon_file = path.join(icon_dir, f"{user_id}.png")
            if path.isfile(icon_file):
                with open(icon_file, "rb") as image_file:
                    icon = b64encode(image_file.read()).decode('utf-8')
        return icon

    def check_email_password(self, email, password):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user
        if not check_password_hash(user.password, password):
            return False, "Incorrect password"
        return True, user

    def validate_reason(self, reason):
        if len(reason.replace(' ', '')) < 7:
            return False, "Reason must contain at least 7 characters"

        return True, "Success"

    def check_active(self, user):
        if user.is_deleted:
            return False, "Deleted account"
        if not user.is_active:
            return False, "User account is not active"
        return True, user

    def is_admin_user(self, email):
        user = User.query.filter_by(email=email, is_admin=True).first()
        if user is None:
            return False
        return True

    def is_normal_user(self, user_id, user):
        if user_id != user.id:
            return False, "User account does not exist"
        if user.is_admin:
            return False, "Not a normal user"
        return True, user

    def get_admin_normal_user_list(self, is_admin):
        users = User.query.filter_by(is_admin=is_admin)
        user_list = []
        for user in users:
            context = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'is_active': user.is_active,
                'is_deleted': user.is_deleted,
                'created_at': user.created_at,
            }
            user_list.append(context)

        return user_list

    def save_deactivate_reason(self, user_id, reason):
        reason = Reason(user_id=user_id, name='deactivate', description=reason)
        db.session.add(reason)
        db.session.commit()

    def get_thumb_size(self, image_dimension, width_max):
        width_rate = image_dimension[0] / width_max
        height_rate = image_dimension[1] / width_rate
        return (int(width_max), int(height_rate))
