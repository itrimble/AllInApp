import sys
import io
import traceback # To capture full traceback on error

# Import the Celery app instance defined in celery_utils.py
# This assumes that tasks.py is in the same AllInApp directory as celery_utils.py
# and that AllInApp is discoverable as a package.
from .celery_utils import celery_app

# Import the actual pipeline function
# This requires that main.py and its dependencies (config.py, etc.) are correctly structured
# and importable within the AllInApp package.
try:
    from .main import run_pipeline
except ImportError:
    # This fallback is less ideal for Celery tasks as they run in a worker process
    # that needs reliable imports. Proper packaging of AllInApp is key.
    # If this happens, the task will likely fail to execute correctly.
    print("Critical Import Error: Could not import run_pipeline in tasks.py. Ensure AllInApp is packaged correctly.")
    # Define a placeholder if import fails, so Celery can still load the task module,
    # though the task itself will be non-functional.
    def run_pipeline():
        raise ImportError("run_pipeline could not be imported in the Celery task environment.")

@celery_app.task(bind=True)
def execute_podcast_pipeline(self):
    """
    Celery task to execute the full podcast processing pipeline.
    Captures stdout and returns status and output.
    `bind=True` gives access to `self` (the task instance).
    """
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()

    output_log = ""
    final_status = "FAILURE" # Default to failure

    try:
        self.update_state(state='STARTED', meta={'output': 'Pipeline started...\n'})

        # Call the main pipeline function
        run_pipeline() # This function logs to stdout, which we are capturing.

        output_log = captured_output.getvalue()
        final_status = "SUCCESS"
        # Update state one last time with final output before returning
        self.update_state(state='SUCCESS', meta={'output': output_log, 'status_message': 'Pipeline completed successfully.'})
        return {'status': 'SUCCESS', 'output': output_log, 'status_message': 'Pipeline completed successfully.'}

    except Exception as e:
        error_output = captured_output.getvalue() # Get any output captured before the error
        error_output += f"\n--- Pipeline Execution Error ---:\n"
        error_output += traceback.format_exc() # Get full traceback
        final_status = "FAILURE" # Ensure status is failure
        # Update state with error details
        self.update_state(state='FAILURE', meta={'output': error_output, 'error': str(e), 'status_message': 'Pipeline failed.'})
        return {'status': 'FAILURE', 'output': error_output, 'error': str(e), 'status_message': 'Pipeline failed.'}

    finally:
        sys.stdout = old_stdout # Always restore stdout
        # The state might have already been set to SUCCESS or FAILURE.
        # If not (e.g. some unhandled exit), this is a fallback.
        if self.AsyncResult(self.request.id).state not in ['SUCCESS', 'FAILURE']:
             self.update_state(state=final_status, meta={'output': captured_output.getvalue(), 'status_message': f'Pipeline finished with status: {final_status}'})
