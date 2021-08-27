import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from config import accounts
from projects.models import Project
from activities.models import Activity


class AccountValidation:
    def is_account_expired(self, account):
        time_difference = account.plan_expires_at - datetime.utcnow()
        minutes_diff = time_difference.total_seconds() / 60

        if minutes_diff <= 0:
            return True
        return False

    def get_remaining_projects(self, projects_allowed, projects_created):
        return projects_allowed - projects_created

    def get_account_expiration(self, start_at, active_days):
        return start_at + timedelta(days=active_days)

    def get_remaining_time(self, account_expire):
        remaining_days = ""
        diff = relativedelta(account_expire, datetime.now())
        if diff.years != 0:
            remaining_days += f"{diff.years} {'year' if diff.years==1 else 'years'} "
        if diff.months != 0:
            remaining_days += f"{diff.months} {'month' if diff.months==1 else 'months'} "
        if diff.days != 0:
            remaining_days += f"{diff.days} {'day' if diff.days==1 else 'days'} "
        if diff.hours != 0:
            remaining_days += f"{diff.hours} {'hour' if diff.hours==1 else 'hours'} "
        if diff.minutes != 0:
            remaining_days += f"{diff.minutes} {'minute' if diff.minutes==1 else 'minutes'}"

        return remaining_days.strip()

    def get_remaining_days(self, expires_at):
        time_difference = expires_at - datetime.utcnow()
        days = time_difference.days if time_difference.days >= 0 else 0
        return days

    def get_past_account_stats(self, user_id, account):
        data = []
        for a in account:
            context = {
                "id": a.id,
                "account_period": a.active_days,
                "created_at": a.created_at,
                "start_at": a.plan_starts_at,
                "expire_at": a.plan_expired_at,
                "plan": a.plan_name,
                "status": "expired",
            }
            data.append(context)

        return data

    def get_future_account_stats(self, user_id, account):
        data = []
        for a in account:
            context = {
                "id": a.id,
                "account_period": a.active_days,
                "created_at": a.created_at,
                "start_at": a.plan_starts_at,
                "expire_at": a.plan_expires_at,
                "plan": a.plan_name,
                "status": "upcoming",
            }
            data.append(context)

        return data

    def get_project_model_chart(self, allowed_projects, created_projects, models_created):
        created_projects = 18
        data = []
        for i in list(range(allowed_projects+1)):
            temp_data = []
            if i <= created_projects:
                temp_data.extend([str(i), i])
            else:
                temp_data.extend([str(i), None])
            if i <= models_created:
                temp_data.append(i)
            else:
                temp_data.append(None)

            data.append(temp_data)
        return {'data': data, 'columns': ['TotalProjects', 'Projects', 'Models']}

    def get_application_usage_chart(self, user_id):
        day = datetime.today().day
        while True:
            try:
                before_3_months = datetime(
                    datetime.today().year, datetime.today().month - 3, day)
                break
            except ValueError:
                day -= 1

        # Get activities created from before 3 months
        activities = Activity.query.filter_by(
            user_id=user_id).filter(Activity.created_at >= before_3_months).order_by(Activity.created_at)

        data = []
        if activities.first() is None:
            return data

        prev_datetime = activities.first().created_at.date()

        activity_count = 0
        new_activity = False

        for activity in activities:
            current_datetime = activity.created_at.date()
            if (current_datetime - prev_datetime).days < 1:
                if new_activity:
                    activity_count = 0
                else:
                    activity_count += 1
                prev_datetime = current_datetime
                new_activity = False
            elif (current_datetime - prev_datetime).days == 1:
                data.append([prev_datetime.strftime("%B %d"), activity_count])
                prev_datetime = current_datetime
                new_activity = True
                activity_count = 0
            elif (current_datetime - prev_datetime).days > 1:
                for i in range((current_datetime - prev_datetime).days):
                    data.append([prev_datetime.strftime("%B %d"), 0])
                    prev_datetime = prev_datetime + timedelta(days=i+1)
                new_activity = True

        data.append([prev_datetime.strftime("%B %d"), activity_count])
        today_date = datetime.utcnow().date()
        no_activity_days = (today_date - prev_datetime).days
        for i in range(no_activity_days):
            prev_datetime = prev_datetime + timedelta(days=1)
            data.append([prev_datetime.strftime("%B %d"), 0])

        return {"data": data, "columns": ["Date", "Activity"]}

    def get_account_stats(self, user_id, account, expired_plan, future_plan):
        projects = Project.query.filter_by(
            created_by=user_id, is_active=True, is_deleted=False)

        projects_remain = self.get_remaining_projects(
            account.project_count, projects.count())

        time_remain = self.get_remaining_time(account.plan_expires_at)
        days_remain = self.get_remaining_days(account.plan_expires_at)

        models_created = 4  # TODO  # fetch model generated status from db
        project_model_chart = self.get_project_model_chart(
            account.project_count, projects.count(), models_created)

        current_plan = {
            "id": account.id,
            "account_period": account.active_days,
            "created_at": account.created_at,
            "start_at": account.plan_starts_at,
            "expire_at": account.plan_expires_at,
            "plan": account.plan_name,
            "status": "current",
        }
        expired_plans = self.get_past_account_stats(user_id, expired_plan)
        expired_plans.reverse()
        upcoming_plans = self.get_future_account_stats(user_id, future_plan)
        upcoming_plans.reverse()

        timeline_data = []
        timeline_data.extend(upcoming_plans)
        timeline_data.append(current_plan)
        timeline_data.extend(expired_plans)

        context = {
            "projects_allowed": account.project_count,
            "projects_created": projects.count(),
            "projects_remain": projects_remain,
            "model_quality_allowed": account.model_quality,
            "account_period": account.active_days,
            "account_expire_at": account.plan_expires_at,
            "days_remain": days_remain,
            "time_remain": time_remain,
            "starts_at": account.plan_starts_at,
            "plan": account.plan_name,
            "project_model_chart": project_model_chart,
            "app_usage_chart": self.get_application_usage_chart(user_id),
            "timeline": timeline_data,
        }

        return context

    def verify_plan(self, plan):
        if plan not in accounts.PLANS:
            return False, "Invalid plan"
        return True, "Success"

    def verify_project_model_count(self, plan, custom_project_count, custom_model_quality):
        project_model_map = accounts.MODEL_QUALITY_MAP[plan]
        days = project_model_map["active_days"]
        project_count = project_model_map["project_count"]
        model_quality = project_model_map["model_quality"]
        if plan == accounts.PLANS[3]:
            if custom_project_count is None or custom_model_quality is None:
                return False, "project_count and model_quality required"
            project_count = custom_project_count
            model_quality = custom_model_quality
            if isinstance(project_count, str):
                try:
                    project_count = int(project_count)
                except ValueError:
                    return False, "Invalid project_count data"
            if isinstance(model_quality, str):
                try:
                    model_quality = int(model_quality)
                except ValueError:
                    return False, "Invalid model_quality data"

            if project_count > accounts.MAX_ALLOWED_PROJECTS:
                return False, "Maximum allowed projects are 100"
            if project_count < accounts.MIN_ALLOWED_PROJECTS:
                return False, "Minimum allowed projects are 1"
            if model_quality not in accounts.MODEL_QUALITIES:
                return False, f"Allowed model_quality values are {accounts.MODEL_QUALITIES}"

        return True, (days, project_count, model_quality)
