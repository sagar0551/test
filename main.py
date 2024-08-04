import requests
import json
from datetime import datetime, timedelta
from prometheus_client import start_http_server, Gauge, Summary
import schedule
import time

# GitHub repository details
GITHUB_REPO = 'sagar0551/skills-hello-github-actions'
GITHUB_TOKEN = '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'

# Prometheus metrics with labels
total_workflows = Gauge('github_total_workflows', 'Total number of GitHub workflows', ['adopter'])
passed_workflows = Gauge('github_passed_workflows', 'Total number of passed GitHub workflows', ['adopter'])
failed_workflows = Gauge('github_failed_workflows', 'Total number of failed GitHub workflows', ['adopter'])
workflow_duration = Summary('github_workflow_duration_seconds', 'Duration of GitHub workflows', ['adopter'])

# Function to get all workflows
def get_all_workflows():
    url = f'https://api.github.com/repos/skills-hello-github-actions/actions/workflows'
    headers = {'Authorization': f'token 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'}
    response = requests.get(url, headers=headers)
    workflows = response.json()['workflows']
    return workflows

# Function to get workflow runs for the last hour
def get_recent_workflow_runs(workflow_id):
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    url = f'https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/skills-hello-github-actions/runs?created={one_hour_ago.isoformat()}Z'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    runs = response.json()['workflow_runs']
    return runs

# Collect metrics
def collect_metrics():
    workflows = get_all_workflows()
    for workflow in workflows:
        adopter = workflow['name']  # Use workflow name as adopter label
        runs = get_recent_workflow_runs(workflow['id'])
        total_workflows.labels(adopter=adopter).set(len(runs))
        passed = failed = 0
        for run in runs:
            if run['conclusion'] == 'success':
                passed += 1
            elif run['conclusion'] == 'failure':
                failed += 1
            workflow_duration.labels(adopter=adopter).observe(run['run_duration'] / 1000.0)  # Convert ms to seconds
        passed_workflows.labels(adopter=adopter).set(passed)
        failed_workflows.labels(adopter=adopter).set(failed)

# Start Prometheus server
start_http_server(8000)

# Collect metrics periodically
schedule.every().hour.do(collect_metrics)

while True:
    schedule.run_pending()
    time.sleep(1)
