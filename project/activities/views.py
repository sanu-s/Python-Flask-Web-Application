from flask.views import MethodView
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.app import app
from users.utils.utils import UserActions
from activities.utils.utils import ActivityActions


activity_bp = Blueprint('activity_bp', __name__, )


class UserActivity(MethodView):
    decorators = [jwt_required(), ]

    def get(self):
        identity = get_jwt_identity()
        is_admin = UserActions().is_admin_user(identity['email'])
        if not is_admin:
            return jsonify({"detail": "Unauthorized user"}), 401

        id = request.args.get('id')
        format = request.args.get('format')

        if id is None:
            return jsonify({"detail": "id required"}), 400

        if format is None:
            return jsonify({"detail": "format required"}), 400

        # Get all activities of the normal user
        if format == 'json':
            data = ActivityActions(id).get_activities_json()
            return jsonify(data), 200
        if format == 'csv':
            data = ActivityActions(id).get_activities_csv()
            return Response(data, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=activities.csv"})

        return jsonify({"detail": "Invalid format"}), 400


app.add_url_rule(
    "/api/user/activity", view_func=UserActivity.as_view("activity"), methods=["GET"]
)
