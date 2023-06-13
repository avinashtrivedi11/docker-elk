import os
import time
import json
import logging
import requests
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger


def get_logger():
    """
    Create and set configuration for logger
    """
    log_file = "logs/jira_reports.log"
    handler = RotatingFileHandler(log_file, mode="a", maxBytes=5 * 1024 * 1024, backupCount=0, encoding=None)
    log_formatter = jsonlogger.JsonFormatter()
    handler.setFormatter(log_formatter)
    handler.setLevel(logging.INFO)
    logger = logging.getLogger("root")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


def validate_environment_variables(logger, required_env_vars):
    """
    Check if all necessary environment variables are set
    """
    for var in required_env_vars:
        if os.environ.get(var) is None:
            logger.error(f"Environment variable '{var}' is not set.")
            exit(1)


def get_jira_issue_data(auth, headers, server, project_name, logger):
    """
    Get Jira issue data from Jira API
    """
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

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException - {e}")
            return None


def main():
    logger = get_logger()

    required_env_vars = ["email", "api_token", "server_name", "projects"]
    log_source = "jira_logs"
    sb_pattern = ["S&B", "Scoping", "S & B"]

    validate_environment_variables(logger, required_env_vars)

    projects = os.getenv("projects").split(",")

    while True:
        email = os.getenv("email")
        api_token = os.getenv("api_token")
        server = os.getenv("server_name")
        frequency = os.getenv("frequency")
        log_time = int(time.time())
        auth = HTTPBasicAuth(email, api_token)
        headers = {"Accept": "application/json"}

        for project_name in projects:
            data = get_jira_issue_data(auth, headers, server, project_name, logger)

            if data:
                for issue in data["issues"]:
                    # Processing issue details
                    # ...

                    if not data["issues"]:  # If there are no more issues, break the loop
                        break

                start_at += len(data["issues"])  # Increment the starting point for the next page

        time.sleep(frequency * 60)


if __name__ == "__main__":
    main()
