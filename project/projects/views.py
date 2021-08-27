from flask.views import MethodView
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequestKeyError
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.app import app
from projects.utils.utils import ProjectActions


project_bp = Blueprint('project_bp', __name__, )


class ProjectCRUD(MethodView):
    decorators = [jwt_required(), ]

    def get(self):
        identity = get_jwt_identity()
        project_id = request.args.get('id')

        if project_id is None:
            return jsonify({"detail": "id required"}), 400

        response, message = ProjectActions().get_project_details(
            identity['email'], project_id, app.config.get('MEDIA_ROOT'))
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200

    def post(self):
        identity = get_jwt_identity()

        data = request.form.get('data')
        if data is None:
            return jsonify({"detail": "data required"}), 400

        try:
            file = request.files['file']
        except BadRequestKeyError:
            return jsonify({"detail": "file is missing in request"}), 400

        response, message = ProjectActions().create_project(
            identity['email'], data, file, app.config.get('MEDIA_ROOT'))
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200

    def put(self):
        identity = get_jwt_identity()

        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        project_id = request.json.get('id', None)
        name = request.json.get('name', None)
        description = request.json.get('description', None)

        if project_id is None:
            return jsonify({"detail": "id required"}), 400
        if name is None:
            return jsonify({"detail": "name required"}), 400
        if description is None:
            return jsonify({"detail": "description required"}), 400

        response, message = ProjectActions().update_project_detail(
            identity['email'], app.config.get('MEDIA_ROOT'), project_id, name, description)

        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200

    def delete(self):
        identity = get_jwt_identity()

        if not request.is_json:
            return jsonify({"detail": "Data is missing in request"}), 400

        project_id = request.json.get('id', None)

        if project_id is None:
            return jsonify({"detail": "id required"}), 400

        response, message = ProjectActions().delete_project(
            app.config.get('MEDIA_ROOT'), identity['email'], project_id)
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify({"detail": message}), 200


class ProjectList(MethodView):
    decorators = [jwt_required(), ]

    def get(self):
        identity = get_jwt_identity()

        response, message = ProjectActions().get_project_list(
            identity['email'], app.config.get('MEDIA_ROOT'))
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200


class FrequencyChart(MethodView):
    decorators = [jwt_required(), ]

    def get(self):
        identity = get_jwt_identity()

        project_id = request.args.get('id')
        feature = request.args.get('feature')

        if project_id is None:
            return jsonify({"detail": "id required"}), 400
        if feature is None:
            return jsonify({"detail": "feature required"}), 400

        response, message = ProjectActions().get_frequency_chart(
            identity['email'], app.config.get('MEDIA_ROOT'), project_id, feature)
        if not response:
            return jsonify({"detail": message}), 400

        return jsonify(message), 200


app.add_url_rule(
    "/api/project", view_func=ProjectCRUD.as_view("project"), methods=["GET", "POST", "PUT", "DELETE"]
)
app.add_url_rule(
    "/api/project/list", view_func=ProjectList.as_view("project-list"), methods=["GET"]
)
app.add_url_rule(
    "/api/project/chart", view_func=FrequencyChart.as_view("frequency-chart"), methods=["GET"]
)
