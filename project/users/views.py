from flask.views import MethodView
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequestKeyError
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.app import app
from users.utils.utils import UserActions


user_bp = Blueprint('user_bp', __name__, )


class UserLogin(MethodView):
    def post(self):
        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        email = request.json.get('email', None)
        password = request.json.get('password', None)
        if email is None:
            return jsonify({"detail": "email required"}), 400
        if password is None:
            return jsonify({"detail": "password required"}), 400

        response, data = UserActions().login_user(email, password)
        if not response:
            return jsonify({'detail': data}), 401

        return jsonify(data), 200


# class UserRefresh(MethodView):
#     decorators = [jwt_refresh_token_required, ]

#     def post(self):
#         identity = get_jwt_identity()
#         response, data = UserActions().login_refresh(identity['email'])
#         if not response:
#             return jsonify({'detail': data}), 401

#         return jsonify(data), 200


class UserLogout(MethodView):
    decorators = [jwt_required(), ]

    def post(self):
        identity = get_jwt_identity()
        response, data = UserActions().logout_user(identity['email'])

        if not response:
            return jsonify({'detail': data}), 401

        return jsonify({'detail': data}), 200


class UserAdminCRUD(MethodView):
    decorators = [jwt_required(), ]

    def get(self):
        identity = get_jwt_identity()
        is_admin = UserActions().is_admin_user(identity['email'])
        if not is_admin:
            return jsonify({"detail": "Unauthorized user"}), 401

        user_type = request.args.get('type')

        if user_type is None:
            return jsonify({"detail": "type required"}), 400

        # Get all users list
        response, message = UserActions().get_user_list(user_type)
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200

    def post(self):
        identity = get_jwt_identity()
        is_admin = UserActions().is_admin_user(identity['email'])
        if not is_admin:
            return jsonify({"detail": "Unauthorized user"}), 401

        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        name = request.json.get('name', None)
        email = request.json.get('email', None)
        admin = request.json.get('admin', None)
        plan = request.json.get('plan', None)
        project_count = request.json.get('project_count', None)
        model_quality = request.json.get('model_quality', None)

        if name is None:
            return jsonify({"detail": "name required"}), 400
        if email is None:
            return jsonify({"detail": "email required"}), 400
        if admin is None:
            return jsonify({"detail": "admin required"}), 400
        if not isinstance(admin, bool):
            return jsonify({"detail": "admin must be boolean"}), 400
        if not admin:
            if plan is None:
                return jsonify({"detail": "plan required"}), 400
            if project_count is None:
                return jsonify({"detail": "project_count required"}), 400
            if model_quality is None:
                return jsonify({"detail": "model_quality required"}), 400
        else:
            plan = None
            project_count = None
            model_quality = None

        response, message = UserActions().register_user(
            identity['id'], name, email, admin, plan, project_count, model_quality)
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify({"detail": message}), 200

    def put(self):
        identity = get_jwt_identity()
        is_admin = UserActions().is_admin_user(identity['email'])
        if not is_admin:
            return jsonify({"detail": "Unauthorized user"}), 401

        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        user_id = request.json.get('id', None)
        name = request.json.get('name', None)
        email = request.json.get('email', None)
        activate = request.json.get('activate', None)

        if user_id is None:
            return jsonify({"detail": "id required"}), 400
        if name is None:
            return jsonify({"detail": "name required"}), 400
        if email is None:
            return jsonify({"detail": "email required"}), 400
        if activate is None:
            return jsonify({"detail": "activate required"}), 400

        response, message = UserActions().update_others_detail(
            user_id, email, name, activate)

        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200

    def delete(self):
        identity = get_jwt_identity()
        is_admin = UserActions().is_admin_user(identity['email'])
        if not is_admin:
            return jsonify({"detail": "Unauthorized user"}), 401

        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        user_id = request.json.get('id', None)
        email = request.json.get('email', None)

        if user_id is None:
            return jsonify({"detail": "id required"}), 400
        if email is None:
            return jsonify({"detail": "email required"}), 400

        response, message = UserActions().delete_other_user(user_id, email)

        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200


class UserCRUD(MethodView):
    decorators = [jwt_required(), ]

    def get(self):
        identity = get_jwt_identity()
        response, message = UserActions().get_user_detail(
            identity['email'], app.config.get('MEDIA_ROOT'))
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200

    def put(self):
        identity = get_jwt_identity()
        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        name = request.json.get('name', None)
        if name is None:
            return jsonify({"detail": "name required"}), 400

        response, message = UserActions().update_detail(
            identity['email'], name)
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200

    def delete(self):
        identity = get_jwt_identity()
        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        reason = request.json.get('reason', None)
        if reason is None:
            return jsonify({"detail": "reason required"}), 400

        response, message = UserActions().deactivate_user(
            identity['email'], reason)
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify({"detail": message}), 200


class UserPicture(MethodView):
    decorators = [jwt_required(), ]

    def get(self):
        pass

    def post(self):
        identity = get_jwt_identity()
        try:
            file = request.files['file']
        except BadRequestKeyError:
            return jsonify({"detail": "file is missing in request"}), 400

        response, message = UserActions().upload_profile_pic(
            identity['email'], file, app.config.get('MEDIA_ROOT'))
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify({"detail": message}), 200

    def put(self):
        pass


class PasswordChange(MethodView):
    decorators = [jwt_required(), ]

    def put(self):
        identity = get_jwt_identity()
        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        password1 = request.json.get('password1', None)
        password2 = request.json.get('password2', None)
        passwordold = request.json.get('passwordold', None)

        if password1 is None:
            return jsonify({"detail": "password1 required"}), 400
        if password2 is None:
            return jsonify({"detail": "password2 required"}), 400
        if passwordold is None:
            return jsonify({"detail": "passwordold required"}), 400

        response, message = UserActions().change_password(
            identity['email'], password1, password2, passwordold)
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify({"detail": message}), 200


class PasswordReset(MethodView):
    def post(self):
        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        email = request.json.get('email', None)

        if email is None:
            return jsonify({"detail": "email required"}), 400

        response, message = UserActions().send_password_reset_email(
            email, app.config.get('SITE_ORIGIN'))
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify({"detail": message}), 200

    def put(self):
        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        key = request.json.get('key', None)
        password1 = request.json.get('password1', None)
        password2 = request.json.get('password2', None)

        if key is None:
            return jsonify({"detail": "key required"}), 400
        if password1 is None:
            return jsonify({"detail": "password1 required"}), 400
        if password2 is None:
            return jsonify({"detail": "password2 required"}), 400

        response, message = UserActions().reset_password_from_link(key, password1, password2)
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify({"detail": message}), 200


class RandomQuotes(MethodView):
    def get(self):
        quotes = UserActions().get_random_quote(app.config.get('MEDIA_ROOT'))
        return jsonify(quotes), 200


app.add_url_rule(
    "/api/user/login", view_func=UserLogin.as_view("login"), methods=["POST"]
)
# app.add_url_rule(
#     "/api/user/refresh", view_func=UserRefresh.as_view("refresh"), methods=["POST"]
# )
app.add_url_rule(
    "/api/user/logout", view_func=UserLogout.as_view("logout"), methods=["POST"]
)
app.add_url_rule(
    "/api/user/admin", view_func=UserAdminCRUD.as_view("admin"), methods=["GET", "POST", "PUT", "DELETE"]
)
app.add_url_rule(
    "/api/user", view_func=UserCRUD.as_view("user"), methods=["GET", "PUT", "DELETE"]
)
app.add_url_rule(
    "/api/user/picture", view_func=UserPicture.as_view("picture"), methods=["POST"]
)
app.add_url_rule(
    "/api/user/change-passsword", view_func=PasswordChange.as_view("change-password"), methods=["PUT"]
)
app.add_url_rule(
    "/api/user/reset-password", view_func=PasswordReset.as_view("reset-password"), methods=["POST", "PUT"]
)
app.add_url_rule(
    "/api/quote", view_func=RandomQuotes.as_view("quote"), methods=["GET"]
)
