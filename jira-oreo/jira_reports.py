import requests
from requests.auth import HTTPBasicAuth
import json
import os
import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
import time
from datetime import datetime, timedelta

# Setup rotating log handler
logFile = "logs/jira_reports.log"
my_handler = RotatingFileHandler(logFile, mode="a", maxBytes=5 * 1024 * 1024, backupCount=0, encoding=None)
log_formatter = jsonlogger.JsonFormatter()
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)
app_log = logging.getLogger("root")
app_log.setLevel(logging.INFO)
app_log.addHandler(my_handler)

required_env_vars = ["email", "api_token", "server_name", "projects"]
log_source = "jira_logs"
sb_pattern = ["S&B", "Scoping", "S & B"]

for var in required_env_vars:
    if os.environ.get(var) is None:
        app_log.error(f"Environment variable '{var}' is not set.")
        exit(1)

projects = os.getenv("projects").split(',')

while True:

    email = os.getenv("email")
    api_token = os.getenv("api_token")
    server = os.getenv("server_name")
    log_time = int(time.time())
    auth = HTTPBasicAuth(email, api_token)

    headers = {"Accept": "application/json"}

    for project_name in projects:
        start_at = 0
        while True:
            try:
                response = requests.request(
                    "GET",
                    server + "/rest/api/3/search",
                    params={
                        "jql": f'project="{project_name.strip()}"',
                        "fields": "summary,created,updated,status,priority,assignee,resolutiondate",
                        "startAt": start_at,
                    },
                    headers=headers,
                    auth=auth,
                )

                response.raise_for_status()
                data = json.loads(response.text)

                for issue in data["issues"]:
                    ticket_name = issue["key"]
                    ticket_status = issue["fields"]["status"]["name"]
                    ticket_priority = issue["fields"]["priority"]["name"]
                    issue_summary = issue["fields"]["summary"]
                    issue_created = issue["fields"]["created"]
                    issue_updated = issue["fields"]["updated"]
                    issue_resolutiondate = (
                        issue["fields"]["resolutiondate"] if issue["fields"]["resolutiondate"] else "Not resolved yet"
                    )
                    issue_assignee = (
                        issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else "Unassigned"
                    )
                    issue_type = "Non-SLA"
                    jira_sla_breached = "NA"
                    jira_sla_current = "NA"

                    if any(pattern in issue_summary for pattern in sb_pattern):
                        issue_type = "SLA"
                        issue_created_date = datetime.strptime(issue_created, "%Y-%m-%dT%H:%M:%S.%f%z")
                        now = datetime.now(tz=issue_created_date.tzinfo)
                        difference = now - issue_created_date
                        jira_sla_current = difference.days
                        if difference > timedelta(days=7):
                            jira_sla_breached = "yes"
                        else:
                            jira_sla_breached = "no"

                    log_info = {
                        "jira_log_time": log_time,    
                        "log_source": log_source,
                        "jira_ticket_name": ticket_name,
                        "jira_issue_summary": issue_summary,
                        "jira_status": ticket_status,
                        "jira_priority": ticket_priority,
                        "jira_created": issue_created,
                        "jira_updated": issue_updated,
                        "jira_finished": issue_resolutiondate,
                        "jira_assignee": issue_assignee,
                        "jira_issue_type": issue_type,
                        "jira_sla_breached": jira_sla_breached,
                        "jira_sla_current": jira_sla_current,
                        "jira_project": project_name.strip()
                    }

                    app_log.info(log_info)

                if not data["issues"]:  # If there are no more issues, break the loop
                    break

                start_at += len(data["issues"])  # Increment the starting point for the next page

            except requests.exceptions.RequestException as e:
                app_log.error(f"RequestException - {e}")

    time.sleep(200)
