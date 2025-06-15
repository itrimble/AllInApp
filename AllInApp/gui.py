import os
import sys
from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify
from celery.result import AsyncResult
# Import celery_app to ensure its context is available for AsyncResult,
# though AsyncResult(task_id) should work with the default app if configured.
# For robustness, explicitly use the app if needed: AsyncResult(task_id, app=celery_app)
try:
    from .celery_utils import celery_app # For explicit app context with AsyncResult if needed
except ImportError:
    if not any(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) in p for p in sys.path):
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    try:
        from AllInApp.celery_utils import celery_app
    except ImportError as e_celery_utils:
        print(f"Warning: Could not import celery_app from celery_utils: {e_celery_utils}. Task status might rely on default Celery app.")
        celery_app = None # Define it as None to avoid NameError later if import fails

# Celery task import
# This relies on AllInApp being a package and tasks.py being correctly structured.
try:
    from .tasks import execute_podcast_pipeline
except ImportError:
    # Fallback for local development if imports are tricky
    # Ensure AllInApp parent is in path for 'python AllInApp/gui.py'
    if not any(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) in p for p in sys.path):
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    try:
        from AllInApp.tasks import execute_podcast_pipeline
    except ImportError as e:
        print(f"Error importing Celery task execute_podcast_pipeline: {e}. Task execution will fail.")
        # Define a placeholder task if import fails
        class MockTask:
            def delay(self, *args, **kwargs):
                class MockAsyncResult:
                    id = "IMPORT_ERROR_TASK_ID"
                print("MockTask: execute_podcast_pipeline.delay called, but task import failed.")
                return MockAsyncResult()
        execute_podcast_pipeline = MockTask()


app = Flask(__name__)
# Secret key for session management (used for flash messages and potentially storing task_id)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

@app.route('/', methods=['GET', 'POST'])
def index():
    # Task ID from session for initial page load
    current_task_id = session.get('task_id', None)
    initial_task_status = session.get('task_status', 'No tasks submitted yet.')

    if request.method == 'POST':
        if 'run_pipeline_button' in request.form:
            try:
                task = execute_podcast_pipeline.delay()
                session['task_id'] = task.id
                current_task_id = task.id # Update for current render
                initial_task_status = 'Pipeline task submitted. Waiting for worker...'
                session['task_status'] = initial_task_status # Store for next GET
                flash(f"Pipeline task submitted! Task ID: {task.id}. Page will auto-update.", "info")
            except Exception as e:
                flash(f"Error submitting task to Celery: {str(e)}", "error")
                session.pop('task_id', None) # Clear task_id on error
                current_task_id = None
                initial_task_status = f"Error submitting task: {str(e)}"
                session['task_status'] = initial_task_status

            # Redirect to GET to prevent form resubmission and show flash messages correctly
            return redirect(url_for('index'))

    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AllInApp Pipeline Control (Celery)</title>
        <style>
            /* ... (styles remain the same as previous step) ... */
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; color: #333; }
            .container { background-color: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #007bff; text-align: center; margin-bottom: 20px; }
            .task-info { margin-top: 20px; padding: 10px; background-color: #e9ecef; border-radius: 4px; }
            .log-output-container { margin-top: 20px; }
            .log-output {
                background-color: #222; color: #f0f0f0; font-family: 'Courier New', Courier, monospace;
                padding: 15px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word;
                min-height: 100px; max-height: 400px; overflow-y: auto; border: 1px solid #444;
            }
            button {
                background-color: #28a745; color: white; padding: 12px 20px;
                border: none; border-radius: 5px; cursor: pointer; font-size: 16px;
                display: block; width: 100%; margin-bottom: 20px;
            }
            button:hover { background-color: #218838; }
            .flash-messages { list-style-type: none; padding: 0; margin-bottom: 15px; }
            .flash-messages li { padding: 10px; margin-bottom: 10px; border-radius: 4px; }
            .flash-messages .info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            .flash-messages .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .flash-messages .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Podcast Processing Pipeline (Celery)</h1>

            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                <ul class="flash-messages">
                {% for category, message in messages %}
                  <li class="{{ category }}">{{ message }}</li>
                {% endfor %}
                </ul>
              {% endif %}
            {% endwith %}

            <form method="POST">
                <button type="submit" name="run_pipeline_button">Run Full Pipeline (Async)</button>
            </form>

            <div class="task-info">
                <h3>Current Task Information:</h3>
                <p><strong>Task ID:</strong> <span id="task-id-display">{{ current_task_id if current_task_id else 'N/A' }}</span></p>
                <p><strong>Status:</strong> <span id="task-status-display">{{ initial_task_status }}</span></p>
            </div>

            <div class="log-output-container">
                <h3>Pipeline Output & Logs:</h3>
                <div class="log-output" id="log-output-content">
                    <pre>Logs will appear here as the task progresses...</pre>
                </div>
            </div>
            <p><small>Pipeline runs in the background. This page will auto-update.</small></p>
        </div>

        <script>
            const taskId = "{{ current_task_id if current_task_id else '' }}";
            const taskStatusDisplay = document.getElementById('task-status-display');
            const logOutputContent = document.getElementById('log-output-content').getElementsByTagName('pre')[0];
            const taskIdDisplay = document.getElementById('task-id-display'); // To update if task ID changes via session

            let pollingInterval;

            function updateTaskStatus(data) {
                if(data.task_id && taskIdDisplay.textContent !== data.task_id) {
                    taskIdDisplay.textContent = data.task_id;
                }
                taskStatusDisplay.textContent = data.state + (data.status_message ? ' - ' + data.status_message : '');

                let outputContent = data.output || '';
                if (data.state === 'FAILURE' && data.error) {
                    outputContent += "\n\n--- ERROR ---:\n" + data.error;
                }
                logOutputContent.textContent = outputContent || 'Waiting for output...';

                if (data.state === 'SUCCESS' || data.state === 'FAILURE') {
                    if (pollingInterval) {
                        clearInterval(pollingInterval);
                        pollingInterval = null;
                        console.log('Polling stopped for task:', taskId, 'State:', data.state);
                    }
                }
            }

            async function fetchTaskStatus(currentTaskId) {
                if (!currentTaskId) {
                    // console.log('No task ID to poll.');
                    if (pollingInterval) clearInterval(pollingInterval); // Stop if task ID is lost
                    return;
                }
                // console.log('Polling for task:', currentTaskId);
                try {
                    const response = await fetch(`/pipeline_status/${currentTaskId}`);
                    if (!response.ok) {
                        console.error('Failed to fetch task status:', response.status);
                        taskStatusDisplay.textContent = 'Error fetching status.';
                        if (pollingInterval) clearInterval(pollingInterval);
                        return;
                    }
                    const data = await response.json();
                    updateTaskStatus(data);
                } catch (error) {
                    console.error('Error during fetch:', error);
                    taskStatusDisplay.textContent = 'Error fetching status (network/parse error).';
                    if (pollingInterval) clearInterval(pollingInterval); // Stop on error
                }
            }

            // Start polling if a task ID is present on page load
            if (taskId) {
                // Initial fetch to get status immediately
                fetchTaskStatus(taskId);

                // Only start interval if task is not already completed (initial_task_status might give a hint, but rely on fetch)
                // A better way: check initial status from a quick fetch or server-rendered data before starting interval.
                // For now, we start polling and let it stop itself if task is already final.
                if (!['SUCCESS', 'FAILURE'].includes(taskStatusDisplay.textContent.split(' - ')[0])) {
                     pollingInterval = setInterval(() => fetchTaskStatus(taskId), 3000); // Poll every 3 seconds
                     console.log('Polling started for task:', taskId);
                } else {
                    console.log('Task already in final state on load, no polling needed for task:', taskId);
                }
            } else {
                 logOutputContent.textContent = "No active task. Submit the pipeline to see logs.";
            }
        </script>
    </body>
    </html>
    """
    # Pass current_task_id and initial_task_status for the template to use
    return render_template_string(html_template, current_task_id=current_task_id, initial_task_status=initial_task_status)

@app.route('/pipeline_status/<task_id>')
def pipeline_status_route(task_id):
    # Use AsyncResult with the explicit app context if available and configured
    # task_result = AsyncResult(task_id, app=celery_app if celery_app else None)
    # Simpler: AsyncResult should use the default app if the task was sent from an imported task instance
    # that was defined with that app.
    task_result = AsyncResult(task_id)

    response_data = {
        'task_id': task_id,
        'state': task_result.state,
        'status_message': '', # Custom message based on state
        'output': '',
        'error': None
    }

    if task_result.state == 'PENDING':
        response_data['status_message'] = 'Task is waiting to be processed by a Celery worker.'
    elif task_result.state == 'STARTED':
        response_data['status_message'] = 'Task has started processing.'
        if task_result.info: # Celery task's meta data via self.update_state()
            response_data['output'] = task_result.info.get('output', '')
            response_data['status_message'] = task_result.info.get('status_message', response_data['status_message'])
    elif task_result.state == 'SUCCESS':
        response_data['status_message'] = 'Task completed successfully!'
        if task_result.result and isinstance(task_result.result, dict):
            response_data['output'] = task_result.result.get('output', '')
            response_data['status_message'] = task_result.result.get('status_message', response_data['status_message'])
        else:
            response_data['output'] = str(task_result.result) # Fallback if result is not dict
    elif task_result.state == 'FAILURE':
        response_data['status_message'] = 'Task failed.'
        if task_result.result and isinstance(task_result.result, dict): # Our task returns a dict
            response_data['output'] = task_result.result.get('output', '')
            response_data['error'] = task_result.result.get('error', 'Unknown error')
            response_data['status_message'] = task_result.result.get('status_message', response_data['status_message'])
        else: # Fallback if result is an Exception object or other
            response_data['error'] = str(task_result.reason) if hasattr(task_result, 'reason') else str(task_result.result)
            response_data['output'] = task_result.traceback if task_result.traceback else ''
    else: # Other states like RETRY, REVOKED
        response_data['status_message'] = f'Task is in an unexpected state: {task_result.state}'
        if task_result.info: # Check for meta if available
             response_data['output'] = task_result.info.get('output', '')

    return jsonify(response_data)

if __name__ == '__main__':
    # Path adjustments for local development if needed
    if not any(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) in p for p in sys.path):
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    try:
        # Re-check import for execute_podcast_pipeline if it was mocked
        if isinstance(execute_podcast_pipeline, MockTask): # type: ignore
            from AllInApp.tasks import execute_podcast_pipeline as real_task
            execute_podcast_pipeline = real_task # type: ignore
            print("Successfully re-imported Celery task for direct Flask execution.")
    except ImportError as e:
        print(f"Could not re-import Celery task for direct Flask execution: {e}")

    app.run(debug=True, host='0.0.0.0', port=5001)
