import json
import string
import secrets
from os import path, stat
from threading import Thread
from datetime import datetime
from random import randint, choice

from PIL import Image
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token

from app.app import db
from users.models import User
from core.emails import SendEmail
from core.cryptograph import CryptoGraphs
from accounts.models import CurrentPlan
from users.utils.generics import UserValidation
from accounts.utils.generics import AccountValidation
from activities.utils.generics import ActivityFunctions
from core.fileprocess import create_dir, get_profile_picture_dir, get_profile_thumbnail_dir, get_quotes_dir


class UserActions(UserValidation, AccountValidation):
    def login_user(self, email, password):
        flag, user = self.check_email_password(email, password)
        if not flag:
            return flag, user
        flag, user = self.check_active(user)
        if not flag:
            return flag, user

        jwt_content = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
        }

        tokens = {
            'access_token': create_access_token(identity=jwt_content),
            'refresh_token': create_refresh_token(identity=jwt_content),
        }

        # Save Activity
        if not user.is_admin:
            ActivityFunctions().save_activity(user.id, "login")

        return True, tokens

    def login_refresh(self, email):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user
        response, user = self.check_active(user)
        if not response:
            return response, user

        jwt_content = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
        }

        tokens = {
            'access_token': create_access_token(identity=jwt_content),
            'refresh_token': create_refresh_token(identity=jwt_content),
        }

        return True, tokens

    def logout_user(self, email):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user
        response, user = self.check_active(user)
        if not response:
            return response, user

        # Save Activity
        if not user.is_admin:
            ActivityFunctions().save_activity(user.id, "logout")

        return True, "Logout success"

    def get_user_detail(self, email, media_root):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user
        response, user = self.check_active(user)
        if not response:
            return response, user

        icon = self.get_icon(media_root, user.id)
        details = {
            'id': user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
            "icon": icon,
        }

        return True, details

    def register_user(self, my_id, name, email, admin, plan, project_count, model_quality):
        name = str(name)
        email = str(email)

        response, message = self.verify_name(name)
        if not response:
            return response, message

        response, message = self.verify_email(email)
        if not response:
            return response, message

        response, message = self.verify_admin(admin)
        if not response:
            return response, message

        if not admin:
            response, message = self.verify_plan(plan)
            if not response:
                return response, message

            response, message = self.verify_project_model_count(
                plan, project_count, model_quality)
            if not response:
                return response, message

            days, project_count, model_quality = message

        # Check for existing account
        response, user = self.check_email_exist(email)
        if response:
            return False, "User account already exist"

        # Create user account
        password = ''.join(secrets.choice(
            string.ascii_uppercase + string.digits) for i in range(8))
        print(password)
        password_hash = generate_password_hash(password, method='sha256')
        user = User(name=name, email=email, password=password_hash,
                    is_admin=admin, created_by=my_id, is_active=True, is_deleted=False)
        db.session.add(user)
        db.session.commit()

        if not admin:
            # Create account details
            start_time = datetime.utcnow()
            expire_time = self.get_account_expiration(start_time, days)
            account = CurrentPlan(user_id=user.id, plan_name=plan, active_days=days, project_count=project_count, model_quality=model_quality,
                                  created_at=start_time, plan_starts_at=start_time, plan_expires_at=expire_time, created_by=my_id)
            db.session.add(account)
            db.session.commit()

        # Send password to the user via email
        t = Thread(target=SendEmail().welcome_email,
                   args=[email, name, password])
        t.start()

        context = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'is_active': user.is_active,
            'is_deleted': user.is_deleted,
            'created_at': user.created_at,
        }

        return True, context

    def update_detail(self, email, name):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user
        response, user = self.check_active(user)
        if not response:
            return response, user

        response, message = self.verify_name(name)
        if not response:
            return response, message

        old_name = user.name

        user.name = name
        db.session.commit()
        details = {
            "name": user.name,
        }

        # Save Activity
        if not user.is_admin:
            ActivityFunctions().save_activity(
                user.id, "change_name", [old_name, user.name])

        return True, details

    def upload_profile_pic(self, email, file, media_root):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user
        response, user = self.check_active(user)
        if not response:
            return response, user

        file_name = file.filename
        if not self.allowed_profile_pics(file_name):
            return False, "File format is not supported"

        dir_name = get_profile_picture_dir(media_root, user.id)
        # delete_dir(dir_name)
        create_dir(dir_name)
        thumb_dir = get_profile_thumbnail_dir(media_root, user.id)
        create_dir(thumb_dir)

        file_full_name = path.join(dir_name, secure_filename(file_name))
        thumbnail_file = path.join(thumb_dir, f"{user.id}.png")

        # Save original file
        file.save(file_full_name)

        # Get file-size and convert to MB
        file_size = stat(file_full_name).st_size
        file_size_mb = file_size * (10 ** -6)
        if file_size_mb > 4:
            return False, "File exceeded the allowed size of 4 MB"

        image = Image.open(file_full_name)

        image_dim = image.size
        if image_dim[0] < 180:
            return False, "Image width is less than 180"
        if image_dim[1] < 180:
            return False, "Image height is less than 180"
        thumb_dim = self.get_thumb_size(image_dim, width_max=180)

        image = image.resize(thumb_dim, Image.ANTIALIAS)
        image.save(thumbnail_file, quality=90)

        icon = self.get_icon(media_root, user.id)

        # Save Activity
        if not user.is_admin:
            ActivityFunctions().save_activity(user.id, "change_picture")

        return True, icon

    def deactivate_user(self, email, reason):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user
        response, user = self.check_active(user)
        if not response:
            return response, user
        response, user = self.is_normal_user(user.id, user)
        if not response:
            return response, user

        reason = str(reason).strip()
        response, message = self.validate_reason(reason)
        if not response:
            return response, message

        user.is_active = False
        db.session.commit()

        self.save_deactivate_reason(user.id, reason)

        # Save Activity
        if not user.is_admin:
            ActivityFunctions().save_activity(user.id, "deactivate_account")

        return True, "Account deactivated"

    def update_others_detail(self, user_id, email, name, activate):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user
        if not isinstance(activate, bool):
            return False, "Invalid activate type"

        response, user = self.is_normal_user(user_id, user)
        if not response:
            return response, user

        user.email = email
        user.name = name
        if activate:
            user.is_active = True
            user.is_deleted = False
        else:
            user.is_active = False
            user.is_deleted = True
        db.session.commit()
        details = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'is_active': user.is_active,
            'is_deleted': user.is_deleted,
            'created_at': user.created_at,
        }

        return True, details

    def delete_other_user(self, user_id, email):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user
        response, user = self.check_active(user)
        if not response:
            return response, user
        response, user = self.is_normal_user(user_id, user)
        if not response:
            return response, user

        user.is_active = False
        user.is_deleted = True
        db.session.commit()

        context = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'is_active': user.is_active,
            'is_deleted': user.is_deleted,
            'created_at': user.created_at,
        }

        return True, context

    def get_user_list(self, user_type):
        if user_type == 'admin':
            is_admin = True
        elif user_type == 'normal':
            is_admin = False
        else:
            return False, "Invalid user type"

        user_list = self.get_admin_normal_user_list(is_admin=is_admin)

        return True, user_list

    def change_password(self, email, password1, password2, passwordold):
        password1 = '' if password1 is None else str(password1)
        password2 = '' if password2 is None else str(password2)
        passwordold = '' if passwordold is None else str(passwordold)

        response, password = self.verify_passwords(password1, password2)
        if not response:
            return response, password

        if password == passwordold:
            return False, "Old password and new password are same"

        response, user = self.check_email_password(email, passwordold)
        if not response:
            return response, user

        password_hash = generate_password_hash(password, method='sha256')

        user.password = password_hash
        db.session.commit()

        # Save Activity
        if not user.is_admin:
            ActivityFunctions().save_activity(user.id, "change_password")

        return True, "Password changed"

    def send_password_reset_email(self, email, site_origin):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user

        if user.is_deleted:
            return False, "Account not found"

        if not user.is_active:
            return False, "Account is deactivated. Contact us to reactivate"

        message = f"{user.id}||{email}||{datetime.now()}"

        key = CryptoGraphs().crypto_encrypt_msg(message)
        pwd_reset_link = f"{site_origin}/change-password?auth={key}"

        # Send password to the user via email
        t = Thread(target=SendEmail().pwd_reset_email,
                   args=[email, user.name, pwd_reset_link])
        t.start()

        # Save Activity
        if not user.is_admin:
            ActivityFunctions().save_activity(user.id, "reset_password_email")

        return True, "Password reset email has been sent"

    def reset_password_from_link(self, key, password1, password2):
        key = str(key).strip()
        password1 = str(password1).strip()
        password2 = str(password2).strip()

        response, password = self.verify_passwords(password1, password2)
        if not response:
            return response, password

        decrypted_message = CryptoGraphs().crypto_decrypt_msg(key)

        data_list = decrypted_message.split('||')
        if len(data_list) != 3:
            return False, "Activation link is invalid."

        _user_id = data_list[0]
        email = data_list[1]
        date_string = data_list[2]

        url_generated_time = datetime.strptime(
            date_string, "%Y-%m-%d %H:%M:%S.%f")

        time_difference = datetime.now() - url_generated_time
        minutes_difference = time_difference.seconds / 60
        if minutes_difference > 15:
            return False, "Your account password reset link expired."

        response, user = self.check_email_exist(email)
        if not response:
            return response, user

        if user.is_deleted:
            return False, "Account not found"

        if not user.is_active:
            return False, "Account is deactivated. Contact us to reactivate"

        password_hash = generate_password_hash(password, method='sha256')

        user.password = password_hash
        db.session.commit()

        # Save Activity
        if not user.is_admin:
            ActivityFunctions().save_activity(user.id, "reset_password_done")

        return True, "Password reset success"

    def get_random_quote(self, media_root):
        quotes_dir = get_quotes_dir(media_root)
        quotes_file = path.join(quotes_dir, f"{randint(1, 100)}.json")

        with open(quotes_file) as f:
            data = json.load(f)

        return choice(data)
