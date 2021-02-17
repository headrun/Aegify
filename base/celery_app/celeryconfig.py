BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ROUTES = {'task_name': {'queue': 'queue_name_for_task'}}
CELERY_IMPORTS = ('crawl.celery.tasks',)