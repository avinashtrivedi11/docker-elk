import requests
from requests.auth import HTTPBasicAuth
import json
import os
import logging
import time


logging.basicConfig(filename='logs/jira_reports.log', level=logging.INFO)

while True:
    email = os.environ.get('email')
    api_token = os.environ.get('api_token')
    server = os.environ.get('server_name')
    project_name = os.environ.get('project_name')

    auth = HTTPBasicAuth(email, api_token)

    headers = {
    "Accept": "application/json"
    }

    queries = {
        'open_tickets': f'project=\"{project_name}\" AND (status="To Do" OR status="In Progress")',
        'closed_tickets': f'project=\"{project_name}\" AND status=Done',
        'critical_tickets': f'project=\"{project_name}\" AND (priority=High OR priority="Highest") AND (status="To Do" OR status="In Progress")',
        'sla_met': f'project=\"{project_name}\" AND (status="In Progress") AND created >= -7d',
        'sla_breached': f'project=\"{project_name}\" AND (status="In Progress") AND created < -7d'
    }

    metrics = {}

    for key, query in queries.items():
        response = requests.request(
        "GET", 
        server + "/rest/api/3/search",
        params={'jql': query},
        headers=headers,
        auth=auth
        )

        data = json.loads(response.text)
        # print(data) 

        metrics[key] = data['total']

    logging.info(metrics)
    time.sleep(60)
