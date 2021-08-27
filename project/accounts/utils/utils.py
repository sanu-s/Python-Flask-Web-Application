from datetime import datetime

from app.app import db
from accounts.utils.generics import AccountValidation
from activities.utils.generics import ActivityFunctions
from accounts.models import CurrentPlan, ExpiredPlan, FuturePlan


class AccountActions(AccountValidation):
    def get_user_stats(self, user_id, is_admin):
        current_plan = CurrentPlan.query.filter_by(user_id=user_id).first()
        if current_plan is None:
            return False, "Account not found"
        expired_plan = ExpiredPlan.query.filter_by(user_id=user_id)
        future_plan = FuturePlan.query.filter_by(user_id=user_id)
        data = self.get_account_stats(
            user_id, current_plan, expired_plan, future_plan)

        # Save Activity
        if not is_admin:
            ActivityFunctions().save_activity(user_id, "view_subscription")

        return True, data

    def reactivate_old_plan(self, admin_id, user_id, effect_immediate):
        account = CurrentPlan.query.filter_by(user_id=user_id).first()
        if account is None:
            return False, "Account not found"

        expired = self.is_account_expired(account)

        if effect_immediate or expired:
            current_time = datetime.utcnow()
            future_plan_expires = self.get_account_expiration(
                current_time, account.active_days)
            if account.plan_expires_at < current_time:
                expired_at = account.plan_expires_at
            else:
                expired_at = current_time

            # Move current plan to expired
            expired_plan = ExpiredPlan(user_id=user_id, plan_name=account.plan_name, active_days=account.active_days, project_count=account.project_count, plan_expired_at=expired_at,
                                       model_quality=account.model_quality, plan_starts_at=account.plan_starts_at, created_at=account.created_at, created_by=account.created_by)
            db.session.add(expired_plan)
            db.session.commit()
            # Update the plan_starts_at time in CurrentPlan
            account.plan_starts_at = current_time
            account.created_by = admin_id
            account.plan_expires_at = future_plan_expires
            account.created_at = current_time
            db.session.commit()

            # Change the start/expire time of future plans
            prev_plans = FuturePlan.query.filter_by(
                user_id=user_id).order_by(FuturePlan.plan_starts_at)
            for prev_plan in prev_plans:
                prev_plan.plan_starts_at = future_plan_expires
                future_plan_expires = self.get_account_expiration(
                    future_plan_expires, prev_plan.active_days)
                prev_plan.plan_expires_at = future_plan_expires
                db.session.commit()

        else:
            # Check previous futureplan
            prev_plan = FuturePlan.query.filter_by(
                user_id=user_id).order_by(FuturePlan.plan_starts_at.desc()).first()

            # Create a plan for future (effect after current plan)
            if prev_plan is None:
                future_plan_expires = self.get_account_expiration(
                    account.plan_expires_at, account.active_days)
                future_plan_starts = account.plan_expires_at
            else:
                future_plan_expires = self.get_account_expiration(
                    prev_plan.plan_expires_at, account.active_days)
                future_plan_starts = prev_plan.plan_expires_at

            future_plan = FuturePlan(user_id=user_id, plan_name=account.plan_name, active_days=account.active_days, plan_starts_at=future_plan_starts,
                                     project_count=account.project_count, plan_expires_at=future_plan_expires, model_quality=account.model_quality, created_by=admin_id)

            db.session.add(future_plan)
            db.session.commit()

        expired_plan = ExpiredPlan.query.filter_by(user_id=user_id)
        future_plan = FuturePlan.query.filter_by(user_id=user_id)
        data = self.get_account_stats(
            user_id, account, expired_plan, future_plan)

        return True, data

    def change_old_plan(self, admin_id, user_id, effect_immediate, plan, days, project_count, model_quality):
        account = CurrentPlan.query.filter_by(user_id=user_id).first()
        if account is None:
            return False, "Account not found"

        expired = self.is_account_expired(account)

        response, message = self.verify_project_model_count(
            plan, project_count, model_quality)
        if not response:
            return response, message

        days, project_count, model_quality = message

        if effect_immediate or expired:
            current_time = datetime.utcnow()
            future_plan_expires = self.get_account_expiration(
                current_time, days)
            if account.plan_expires_at < current_time:
                expired_at = account.plan_expires_at
            else:
                expired_at = current_time

            # Move current plan to expired
            expired_plan = ExpiredPlan(user_id=user_id, plan_name=account.plan_name, active_days=account.active_days, project_count=account.project_count, plan_expired_at=expired_at,
                                       model_quality=account.model_quality, plan_starts_at=account.plan_starts_at, created_at=account.created_at, created_by=account.created_by)
            db.session.add(expired_plan)
            db.session.commit()

            # Update the plan_starts_at time in CurrentPlan
            account.plan_name = plan
            account.plan_starts_at = current_time
            account.plan_expires_at = future_plan_expires
            account.created_by = admin_id
            account.created_at = current_time
            account.active_days = days
            account.model_quality = model_quality
            account.project_count = project_count
            db.session.commit()

            # Change the start/expire time of future plans
            prev_plans = FuturePlan.query.filter_by(
                user_id=user_id).order_by(FuturePlan.plan_starts_at)
            for prev_plan in prev_plans:
                prev_plan.plan_starts_at = future_plan_expires
                future_plan_expires = self.get_account_expiration(
                    future_plan_expires, prev_plan.active_days)
                prev_plan.plan_expires_at = future_plan_expires
                db.session.commit()

        else:
            # Check previous futureplan
            prev_plan = FuturePlan.query.filter_by(
                user_id=user_id).order_by(FuturePlan.plan_starts_at.desc()).first()

            if prev_plan is None:
                future_plan_expires = self.get_account_expiration(
                    account.plan_expires_at, days)
                future_plan_starts = account.plan_expires_at
            else:
                future_plan_expires = self.get_account_expiration(
                    prev_plan.plan_expires_at, days)
                future_plan_starts = prev_plan.plan_expires_at

            future_plan = FuturePlan(user_id=user_id, plan_name=plan, active_days=days, plan_starts_at=future_plan_starts,
                                     project_count=project_count, plan_expires_at=future_plan_expires, model_quality=model_quality, created_by=admin_id)

            db.session.add(future_plan)
            db.session.commit()

        expired_plan = ExpiredPlan.query.filter_by(user_id=user_id)
        future_plan = FuturePlan.query.filter_by(user_id=user_id)
        data = self.get_account_stats(
            user_id, account, expired_plan, future_plan)

        return True, data

    def delete_future_subscription(self, user_id, subscription_id):
        future_plan = FuturePlan.query.filter_by(
            id=subscription_id, user_id=user_id)
        if future_plan.first() is None:
            return False, "Subscription not found"

        future_plan.delete()
        db.session.commit()

        response, data = self.get_user_stats(user_id, True)

        return response, data
