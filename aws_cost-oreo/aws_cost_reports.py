import boto3
import os
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

# Load environment variables
load_dotenv()

# Get AWS credentials and region from environment variables
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_default_region = os.getenv("AWS_DEFAULT_REGION")

# Set up logging
logger = logging.getLogger("aws_cost_explorer")
logger.setLevel(logging.INFO)

# Create a custom formatter that outputs log messages as JSON
formatter = jsonlogger.JsonFormatter()

# Set up a rotating file handler
handler = RotatingFileHandler("logs/aws_cost_explorer.log", maxBytes=20000, backupCount=5)
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

# Create a session using your credentials
session = boto3.Session(
    aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=aws_default_region
)

# Create a client using the session
client = session.client("ce")

# Define the start and end dates
start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
end_date = datetime.now().strftime("%Y-%m-%d")


def fetch_service_cost(service_name):
    """
    This function fetches the cost usage for a specific service
    """
    params = {
        "TimePeriod": {"Start": start_date, "End": end_date},
        "Granularity": "DAILY",
        "Metrics": ["BlendedCost", "UnblendedCost", "UsageQuantity"],
        "Filter": {
            "Dimensions": {"Key": "SERVICE", "Values": [service_name]},
        },
    }

    # Make the request
    response = client.get_cost_and_usage(**params)

    # Transform each response and log it separately
    for result in response["ResultsByTime"]:
        transformed_response = transform_log(result, service_name)
        logger.info(transformed_response)


def transform_log(result, service_name):
    """
    This function transforms the log response according to elasticsearch needs
    """
    # Get the total cost metrics
    total = result["Total"]

    # Set the transformed log structure
    transformed_data = {
        "message": f"AWS Cost Explorer Transformed Response for {service_name}",
        "aws_costs_date": result["TimePeriod"]["Start"],
        "aws_cost_service": service_name,
        "aws_cost_amount_unblended": total["UnblendedCost"]["Amount"],
        "aws_cost_amount_blended": total["BlendedCost"]["Amount"],
        "aws_cost_unit": total["BlendedCost"]["Unit"],
        "aws_cost_usage_quantity": total["UsageQuantity"]["Amount"],
        "aws_cost_usage_unit": total["UsageQuantity"]["Unit"],
        "aws_cost_estimated": result["Estimated"],
    }

    return transformed_data


while True:
    fetch_service_cost("Amazon Elastic Compute Cloud - Compute")
    # fetch_service_cost("Amazon Simple Storage Service")
    # Sleep for 24 hours
    time.sleep(60 * 60 * 24)
