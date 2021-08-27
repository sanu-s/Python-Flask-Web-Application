from os import path

from app.app import db
from projects.models import Project
from config.projects import STATS_FILE
from accounts.models import CurrentPlan
from users.utils.utils import UserValidation
from projects.utils.generics import ProjectValidation
from accounts.utils.generics import AccountValidation
from activities.utils.generics import ActivityFunctions
from core.fileprocess import create_dir, delete_dir, get_project_dir, get_stats_dir, get_project_root


class ProjectActions(UserValidation, ProjectValidation, AccountValidation):
    def create_project(self, email, data, file, media_root):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user

        response, user = self.is_normal_user(user.id, user)
        if not response:
            return response, user

        account = CurrentPlan.query.filter_by(user_id=user.id).first()
        if account is None:
            return False, "Account not found"

        account_expired = self.is_account_expired(account)
        if account_expired:
            return False, "Your subscription has expired. Contact us to nenew your subscription"

        response = self.is_project_limit_exceed(user.id)
        if response:
            return False, "Allowed project limit exceeded"

        response, data = self.validate_project_data(user.id, data)
        if not response:
            return response, data

        name, description = data

        file_name = file.filename
        if not self.allowed_file(file_name):
            return False, "File format is not supported"

        # Save project details in database
        project = Project(name=name, description=description,
                          file_name=file_name, created_by=user.id)
        db.session.add(project)
        db.session.commit()

        # Save files in project directory
        dir_name = get_project_dir(media_root, user.id, project.id)
        create_dir(dir_name)

        file_full_name = path.join(dir_name, file_name)
        file.save(file_full_name)

        # Calculate Data Statistics as a process
        stats_path = get_stats_dir(media_root, user.id, project.id)
        create_dir(stats_path)
        stats_file = path.join(stats_path, STATS_FILE)

        ProjectValidation().calculate_statistics(stats_file, file_full_name, project)

        mini_statistics = self.get_project_minimal_chart(stats_file)

        context = {
            "id": project.id,
            "name": name,
            "description": description,
            "file_name": file_name,
            "rows": project.file_rows,
            "features": project.file_columns,
            "mini_statistics": mini_statistics,
        }

        # Save Activity
        ActivityFunctions().save_activity(user.id, "create_project", [name])

        return True, context

    def get_project_details(self, email, project_id, media_root):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user

        response, user = self.is_normal_user(user.id, user)
        if not response:
            return response, user

        project = self.is_project_creator(user.id, project_id)
        if not project:
            return False, "You are not allowed to view project details"

        stats_path = get_stats_dir(media_root, user.id, project.id)
        stats_file = path.join(stats_path, STATS_FILE)

        statistics = None
        if path.isfile(stats_file):
            statistics = self.get_statistical_chart(stats_file)

        mini_statistics = self.get_project_minimal_chart(stats_file)

        context = {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'file_name': project.file_name,
            "rows": project.file_rows,
            "features": project.file_columns,
            "model_target": project.model_target,
            "model_count": project.model_count,
            "model_accuracy": project.model_accuracy if project.model_accuracy is not None else 0,
            "statistics": statistics,
            "mini_statistics": mini_statistics,
        }

        return True, context

    def delete_project(self, media_root, email, project_id):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user

        response, user = self.is_normal_user(user.id, user)
        if not response:
            return response, user

        project = self.is_project_creator(user.id, project_id)
        if not project:
            return False, "You are not allowed to view project details"

        # Delete project files
        project_dir = get_project_root(media_root, user.id, project_id)
        delete_dir(project_dir)

        # Delete model database entries
        # TODO

        db.session.delete(project)
        db.session.commit()

        return True, "Project deleted"

    def update_project_detail(self, email, media_root, project_id, name, description):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user

        response, user = self.is_normal_user(user.id, user)
        if not response:
            return response, user

        project = self.is_project_creator(user.id, project_id)
        if not project:
            return False, "You are not allowed to view project details"

        response, message = self.validate_name_description(name, description)
        if not response:
            return response, message

        project.name = name
        project.description = description

        db.session.add(project)
        db.session.commit()

        stats_path = get_stats_dir(media_root, user.id, project.id)
        stats_file = path.join(stats_path, STATS_FILE)

        statistics = None
        if path.isfile(stats_file):
            statistics = self.get_statistical_chart(stats_file)

        mini_statistics = self.get_project_minimal_chart(stats_file)

        context = {
            "id": project_id,
            "name": name,
            "description": description,
            "file_name": project.file_name,
            "rows": project.file_rows,
            "features": project.file_columns,
            "model_target": project.model_target,
            "model_count": project.model_count,
            "model_accuracy": project.model_accuracy,
            "statistics": statistics,
            "mini_statistics": mini_statistics,
        }

        return True, context

    def get_project_list(self, email, media_root):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user

        response, user = self.is_normal_user(user.id, user)
        if not response:
            return response, user

        projects = self.get_all_projects(user.id, media_root, STATS_FILE)

        # Save Activity
        ActivityFunctions().save_activity(user.id, "view_project_list")

        return True, projects

    def get_frequency_chart(self, email, media_root, project_id, feature):
        response, user = self.check_email_exist(email)
        if not response:
            return response, user

        response, user = self.is_normal_user(user.id, user)
        if not response:
            return response, user

        project = self.is_project_creator(user.id, project_id)
        if not project:
            return False, "Project does not exist"

        dir_name = get_project_dir(media_root, user.id, project.id)
        file_name = path.join(dir_name, project.file_name)

        data = self.prepare_freqency_data(feature, file_name)

        # Save Activity
        ActivityFunctions().save_activity(
            user.id, "frequency_chart", [feature, project.name])

        return True, data
