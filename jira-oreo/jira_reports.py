import requests
from requests.auth import HTTPBasicAuth
import json
import os
import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
import time

# Setup rotating log handler
logFile = 'logs/jira_reports.log'
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
log_formatter = jsonlogger.JsonFormatter(fmt="%(asctime)s %(levelname)s %(message)s")
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)
app_log = logging.getLogger('root')
app_log.setLevel(logging.INFO)
app_log.addHandler(my_handler)

required_env_vars = ['email', 'api_token', 'server_name', 'project_name']

sb_pattern = ['S&B'] # enter your patterns here

for var in required_env_vars:
    if os.environ.get(var) is None:
        app_log.error(f"Environment variable '{var}' is not set.")
        exit(1)

while True:
    email = os.getenv('email')
    api_token = os.getenv('api_token')
    server = os.getenv('server_name')
    project_name = os.getenv('project_name')

    auth = HTTPBasicAuth(email, api_token)

    headers = {
    "Accept": "application/json"
    }

    try:
        response = requests.request(
        "GET", 
        server + "/rest/api/3/search",
        params={'jql': f'project=\"{project_name}\"', 'fields': 'summary,created,updated,status,priority,assignee,resolutiondate'},
        headers=headers,
        auth=auth
        )

        response.raise_for_status()
        data = json.loads(response.text)

        for issue in data['issues']:
            ticket_name = issue['key']
            ticket_status = issue['fields']['status']['name']
            ticket_priority = issue['fields']['priority']['name']
            issue_summary = issue['fields']['summary']
            issue_created = issue['fields']['created']
            issue_updated = issue['fields']['updated']
            issue_resolutiondate = issue['fields']['resolutiondate'] if issue['fields']['resolutiondate'] else "Not resolved yet"
            issue_assignee = issue['fields']['assignee']['displayName'] if issue['fields']['assignee'] else "Unassigned"

            log_info = {
                "ticket_name": ticket_name, 
                "issue_summary": issue_summary,
                "status": ticket_status, 
                "priority": ticket_priority,
                "created": issue_created,
                "updated": issue_updated,
                "finished": issue_resolutiondate,
                "assignee": issue_assignee,
                "type": "All"
            }

            app_log.info(log_info)

            if any(pattern in issue_summary for pattern in sb_pattern):
                log_info["type"] = "Filtered"
                app_log.info(log_info)

    except requests.exceptions.RequestException as e:
        app_log.error(f"RequestException - {e}")

    time.sleep(60)
