PLANS = ['PREMIUM', 'STANDARD', 'BASIC', 'CUSTOM']

MIN_ALLOWED_PROJECTS = 1
MAX_ALLOWED_PROJECTS = 100

MODEL_QUALITIES = [1, 2, 3]

MODEL_QUALITY_MAP = {
    "BASIC": {
        "active_days": 15,
        "project_count": 5,
        "model_quality": 3,
    },
    "STANDARD": {
        "active_days": 365,
        "project_count": 10,
        "model_quality": 2,
    },
    "PREMIUM": {
        "active_days": 365,
        "project_count": 20,
        "model_quality": 1,
    },
    "CUSTOM": {
        "active_days": 365,
        "project_count": 0,
        "model_quality": 3,
    },
}

PLAN_ACTIONS = ['reactivate', 'change']
