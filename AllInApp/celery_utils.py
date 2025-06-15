from celery import Celery

# Define the Redis URL for broker and backend
# Assumes Redis is running on localhost, default port.
# For production, use a configuration variable.
REDIS_URL = "redis://localhost:6379/0"

# Create the Celery application instance
# 'AllInApp' is the name of the main module where tasks might be auto-discovered.
celery_app = Celery(
    "AllInApp",  # Main module name, helps with task naming and discovery
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["AllInApp.tasks"]  # List of modules to import when the worker starts
                               # We will create AllInApp.tasks in the next step.
)

# Optional Celery configuration (can be expanded)
celery_app.conf.update(
    task_serializer="json",       # Default serializer
    accept_content=["json"],      # Default accept content
    result_serializer="json",     # Default result serializer
    timezone="UTC",               # It's good practice to use UTC
    enable_utc=True,
    # Optional: Configure a simple retry policy for tasks
    # task_acks_late=True,
    # task_reject_on_worker_lost=True,
)

if __name__ == '__main__':
    # This allows running the celery worker directly using:
    # python -m AllInApp.celery_utils worker -l info
    # Or, more commonly, from the project root:
    # celery -A AllInApp.celery_utils worker -l info
    # Note: The above command assumes 'AllInApp' is in PYTHONPATH.
    # If celery_utils.py is run directly, it might not set 'AllInApp' as the app name correctly
    # for autodiscovery if not structured as a package.
    # The `celery -A AllInApp.celery_utils worker` command is preferred.
    celery_app.start()
