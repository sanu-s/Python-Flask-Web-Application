import json
from os import path

import pandas as pd

from app.app import db
from projects.models import Project
from accounts.models import CurrentPlan
from config.projects import ALLOWED_EXTENSIONS
from core.fileprocess import get_data_from_file, get_stats_dir


class ProjectValidation:
    def validate_name(self, name):
        if len(name) < 3:
            return False, "Name must contain at least 3 characters"
        if len(name) > 20:
            return False, "Maximum allowed characters for name is 20"

        return True, "Success"

    def validate_description(self, description):
        if len(description) < 10:
            return False, "Description must contain at least 10 characters"
        if len(description) > 500:
            return False, "Maximum allowed characters for description is 500"
        return True, "Success"

    def validate_name_description(self, name, description):
        response, message = self.validate_name(name)
        if not response:
            return response, message

        response, message = self.validate_description(description)
        if not response:
            return response, message

        return True, "Success"

    def validate_project_data(self, user_id, data, check_project=True):
        try:
            data = json.loads(data)
        except json.decoder.JSONDecodeError:
            return False, "data must be a stringified value"

        name = data.get('name')
        description = data.get('description')

        if name is None:
            return False, "name must be included in stringified data"
        if description is None:
            return False, "description must be included in stringified data"

        name = str(name).strip()
        description = str(description).strip()

        response, message = self.validate_name_description(name, description)
        if not response:
            return response, message

        if check_project:
            project = Project.query.filter_by(
                name=name, created_by=user_id).first()
            if project is not None:
                return False, "Project already exist with this name"

        return True, (name, description)

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.')[-1].lower() in ALLOWED_EXTENSIONS

    def calculate_statistics(self, stats_file, filename, project):
        unique_list = []
        min_list = []
        max_list = []
        median_list = []
        sd_list = []
        mean_list = []

        data = get_data_from_file(filename)
        rows, columns = data.shape

        col_list = data.columns.values.tolist()
        dtype_list = []
        for d in data.dtypes.tolist():
            d = d.name.lower()
            if d.startswith(('int', 'float')):
                dtype_list.append("Number")
            elif d.startswith('bool'):
                dtype_list.append("Boolean")
            elif d.startswith('date'):
                dtype_list.append("DateTime")
            elif d.startswith('object'):
                dtype_list.append("String")
            else:
                dtype_list.append("String")

        index_list = list(range(len(col_list)))
        missing_list = data.isnull().sum().values.tolist()
        observation_list = data.count().values.tolist()

        for v in col_list:
            try:
                unique_list.append(data[v].nunique())
            except TypeError:
                unique_list.append(data[v].astype(str).nunique())
            if data[v].dtype.name.lower().startswith(("object", "datetime", "bool")):
                min_list.append(pd.NA)
                max_list.append(pd.NA)
                median_list.append(pd.NA)
                sd_list.append(pd.NA)
                mean_list.append(pd.NA)
                continue

            min_list.append(round(data[v].min(), 2))
            max_list.append(round(data[v].max(), 2))
            median_list.append(round(data[v].median(), 2))
            sd_list.append(round(data[v].std(), 2))
            mean_list.append(round(data[v].mean(), 2))

        statistics = {
            'Index': index_list,
            'Name': col_list,
            'DataType': dtype_list,
            'Unique': unique_list,
            'Missing': missing_list,
            'Mean': mean_list,
            'StandardDeviation': sd_list,
            'Median': median_list,
            'Minimum': min_list,
            'Maximum': max_list,
            'TotalValues': observation_list,
        }

        df = pd.DataFrame(statistics)
        json_data = json.loads(df.to_json(orient='records'))

        with open(stats_file, 'w+') as fp:
            json.dump(json_data, fp)

        project.file_rows = rows
        project.file_columns = columns

        db.session.add(project)
        db.session.commit()

    def get_project_minimal_chart(self, stats_file):
        with open(stats_file) as fp:
            data = json.load(fp)

        chart_data = []
        for item in data:
            chart_data.append([item["Name"], item["TotalValues"]])

        return {"data": chart_data, "columns": ["Feature", "Density"]}

    def get_statistical_chart(self, stats_file):
        with open(stats_file) as fp:
            data = json.load(fp)

        return data

    def is_project_limit_exceed(self, user_id):
        project_count = CurrentPlan.query.filter_by(
            user_id=user_id).first().project_count
        projects = Project.query.filter_by(
            created_by=user_id, is_active=True, is_deleted=False)

        if projects.count() >= project_count:
            return True
        return False

    def is_project_creator(self, user_id, project_id):
        project = Project.query.filter_by(
            id=project_id, created_by=user_id, is_active=True, is_deleted=False).first()
        if project is None:
            return False
        return project

    def get_all_projects(self, user_id, media_root, STATS_FILE):
        projects = Project.query.filter_by(
            created_by=user_id, is_active=True, is_deleted=False).order_by(Project.created_at.desc())

        project_list = []
        for project in projects:
            stats_path = get_stats_dir(media_root, user_id, project.id)
            stats_file = path.join(stats_path, STATS_FILE)

            mini_statistics = None
            if path.isfile(stats_file):
                mini_statistics = self.get_project_minimal_chart(stats_file)

            context = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "file_name": project.file_name,
                "rows": project.file_rows,
                "features": project.file_columns,
                "mini_statistics": mini_statistics,
            }

            project_list.append(context)

        return project_list

    def prepare_freqency_data(self, feature, file_name):
        df = get_data_from_file(file_name)

        if df[feature].dtype.name == 'float64':
            df[feature] = df[feature].apply(lambda x: round(x, 2))

        try:
            value_col = df[feature].value_counts(
                dropna=True, sort=False).sort_index()
        except TypeError:
            value_col = df[feature].astype(str).value_counts(
                dropna=True, sort=False).sort_index()

        data = []
        for i, v in value_col.items():
            data.append([i, v])

        return {"data": data, "columns": ["Frequency of Records", feature]}
