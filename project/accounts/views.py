from flask.views import MethodView
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.app import app
from config import accounts
from users.utils.utils import UserValidation
from accounts.utils.utils import AccountActions
from accounts.utils.generics import AccountValidation


account_bp = Blueprint('account_bp', __name__, )


class AccountSubscription(MethodView):
    decorators = [jwt_required(), ]

    def get(self):
        identity = get_jwt_identity()
        response, user = UserValidation().check_email_exist(identity['email'])
        if not response:
            return jsonify({"detail": user}), 400

        if user.is_admin:
            user_id = request.args.get('id')
            if user_id is None:
                return jsonify({"detail": "id required"}), 400
        else:
            user_id = user.id

        response, message = AccountActions().get_user_stats(
            user_id, identity['is_admin'])
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200

    def put(self):
        identity = get_jwt_identity()
        is_admin = UserValidation().is_admin_user(identity['email'])
        if not is_admin:
            return jsonify({"detail": "Unauthorized user"}), 401

        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        user_id = request.json.get('id', None)
        action = request.json.get('action', None)
        effect_immediate = request.json.get('immediate', None)

        if user_id is None:
            return jsonify({"detail": "id required"}), 400
        if action is None:
            return jsonify({"detail": "action required"}), 400
        if effect_immediate is None:
            return jsonify({"detail": "immediate required"}), 400

        if not isinstance(effect_immediate, bool):
            return jsonify({"detail": "immediate must be a boolean value"}), 400

        if action not in accounts.PLAN_ACTIONS:
            return jsonify({"detail": "Invalid action"}), 400

        if action == accounts.PLAN_ACTIONS[0]:
            response, message = AccountActions().reactivate_old_plan(
                identity['id'], user_id, effect_immediate)

        elif action == accounts.PLAN_ACTIONS[1]:
            plan = request.json.get('plan', None)
            project_count = request.json.get('project_count', None)
            model_quality = request.json.get('model_quality', None)

            if plan is None:
                return jsonify({"detail": "plan required"}), 400

            response, message = AccountValidation().verify_plan(plan)
            if not response:
                return response, message

            if plan == accounts.PLANS[3]:
                if project_count is None:
                    return jsonify({"detail": "project_count required"}), 400
                if model_quality is None:
                    return jsonify({"detail": "model_quality required"}), 400
            else:
                project_count = None
                model_quality = None

            response, message = AccountValidation().verify_project_model_count(plan,
                                                                               project_count, model_quality)
            if not response:
                return jsonify({"detail": message}), 400

            days, project_count, model_quality = message
            response, message = AccountActions().change_old_plan(
                identity['id'], user_id, effect_immediate, plan, days, project_count, model_quality)

        else:
            return jsonify({"detail": "Unknown action"}), 400

        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200

    def delete(self):
        identity = get_jwt_identity()
        is_admin = UserValidation().is_admin_user(identity['email'])
        if not is_admin:
            return jsonify({"detail": "Unauthorized user"}), 401

        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        user_id = request.json.get('user_id', None)
        subscription_id = request.json.get('subscription_id', None)

        if user_id is None:
            return jsonify({"detail": "user_id required"}), 400
        if subscription_id is None:
            return jsonify({"detail": "subscription_id required"}), 400

        response, message = AccountActions().delete_future_subscription(
            user_id, subscription_id)
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200


app.add_url_rule(
    "/api/user/account", view_func=AccountSubscription.as_view("account"), methods=["GET", "PUT", "DELETE"]
)
