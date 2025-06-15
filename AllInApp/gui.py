import os
import sys
import io
from flask import Flask, render_template_string, request, redirect, url_for, flash

# Attempt to import run_pipeline. This might require PYTHONPATH adjustments
# depending on how the Flask app is run.
# Assuming gui.py is inside AllInApp and can import main
try:
    from main import run_pipeline
    # This also implies that modules used by main (config, rss_feed etc.) are findable.
except ImportError:
    # Fallback for cases where direct import might fail, e.g. when running `python AllInApp/gui.py`
    # without AllInApp's parent in PYTHONPATH. This is a common issue.
    # For a robust solution, AllInApp should be structured as a proper package.
    # For now, we'll try to make it work for direct execution if possible.
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    try:
        from AllInApp.main import run_pipeline
    except ImportError as e:
        # If it still fails, we'll have a placeholder
        print(f"Error importing run_pipeline: {e}. Pipeline execution will be simulated.")
        def run_pipeline():
            return "run_pipeline function not found due to import error."

app = Flask(__name__)
app.secret_key = os.urandom(24) # For session management, like flash messages

# Store captured output from the pipeline
pipeline_output_log = ""

@app.route('/', methods=['GET', 'POST'])
def index():
    global pipeline_output_log

    if request.method == 'POST':
        if 'run_pipeline_button' in request.form:
            pipeline_output_log = "Starting pipeline execution...\n"

            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()

            try:
                flash("Pipeline execution started. This might take a while and the browser may hang. Please wait...", "info")
                # Force redirect and render before long task (won't work as expected due to sync execution)
                # return redirect(url_for('index')) # This won't show flash before task completion

                # run_pipeline() # This is synchronous and will block
                # For now, we directly call it. User will experience a hang.
                # In a real app, use Celery/RQ or threading.
                run_pipeline()
                pipeline_run_stdout = captured_output.getvalue()
                pipeline_output_log += pipeline_run_stdout
                pipeline_output_log += "\nPipeline execution finished."
                flash("Pipeline finished!", "success")
            except Exception as e:
                pipeline_output_log += f"\nAn error occurred: {str(e)}\n"
                flash(f"Pipeline encountered an error: {str(e)}", "error")
            finally:
                sys.stdout = old_stdout # Restore stdout

            return redirect(url_for('index')) # Redirect to show updated status and logs

    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AllInApp Pipeline Control</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; color: #333; }
            .container { background-color: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #007bff; text-align: center; margin-bottom: 20px; }
            .pipeline-status { margin-top: 25px; }
            .pipeline-status h2 { color: #555; margin-bottom:10px; }
            .log-output {
                background-color: #222; color: #f0f0f0; font-family: 'Courier New', Courier, monospace;
                padding: 15px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word;
                max-height: 400px; overflow-y: auto; border: 1px solid #444;
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
            <h1>Podcast Processing Pipeline</h1>

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
                <button type="submit" name="run_pipeline_button">Run Full Pipeline</button>
            </form>

            <div class="pipeline-status">
                <h2>Pipeline Output & Logs:</h2>
                <div class="log-output">
                    <pre>{{ captured_logs | safe }}</pre>
                </div>
            </div>
            <p><small>Note: Running the pipeline will block the browser until completion. For production, use background tasks.</small></p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, captured_logs=pipeline_output_log)

if __name__ == '__main__':
    # Ensure AllInApp parent directory is in PYTHONPATH if running directly for imports to work
    # This is a common pattern for local development.
    if not any(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) in p for p in sys.path):
         sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    # Try to re-import run_pipeline with updated path if the initial one failed
    # This is primarily for the `python AllInApp/gui.py` case.
    if 'run_pipeline' not in globals() or globals()['run_pipeline'].__doc__ == "run_pipeline function not found due to import error.":
        try:
            from AllInApp.main import run_pipeline as rp_main
            run_pipeline = rp_main
            print("Successfully imported run_pipeline for direct execution.")
        except ImportError as e:
            print(f"Still could not import run_pipeline after path adjustment: {e}")
            # Keep the placeholder if it fails

    app.run(debug=True, host='0.0.0.0', port=5001)
