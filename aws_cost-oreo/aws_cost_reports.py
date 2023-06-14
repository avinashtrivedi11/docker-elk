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
        logger.info(f"AWS Cost Explorer Transformed Response for {service_name}", extra=transformed_response)


def transform_log(result, service_name):
    """
    This function transforms a single day's log according to given specifications
    """
    transformed_data = {}

    # Set the message
    transformed_data["message"] = f"AWS Cost Explorer Transformed Response for {service_name}"

    # Set the date
    transformed_data["aws_costs_date"] = result["TimePeriod"]["Start"]

    # Set the service
    transformed_data["aws_cost_service"] = service_name

    # Set the costs and units
    for metric_key, metric_value in result["Total"].items():
        if metric_key == "BlendedCost":
            transformed_data["aws_cost_amount_blended"] = float(metric_value["Amount"])
        elif metric_key == "UnblendedCost":
            transformed_data["aws_cost_amount_unblended"] = float(metric_value["Amount"])
        elif metric_key == "UsageQuantity":
            transformed_data["aws_cost_usage_quantity"] = float(metric_value["Amount"])
            transformed_data["aws_cost_usage_unit"] = metric_value["Unit"]

    # Set the cost unit (assuming the cost unit is same for blended and unblended)
    transformed_data["aws_cost_unit"] = result["Total"]["BlendedCost"]["Unit"]

    # Set the estimated value
    transformed_data["aws_cost_estimated"] = result["Estimated"]

    return transformed_data


def transform_results_by_time(results_by_time):
    """
    This function transforms the ResultsByTime data according to given specifications
    """
    transformed_results_by_time = []

    # Iterate over the ResultsByTime data and transform it
    for result in results_by_time:
        transformed_result = {}

        for key in result:
            if key == "TimePeriod":
                transformed_result["aws_cost_" + key] = result[key]["Start"]
            else:
                transformed_result["aws_cost_" + key] = result[key]

        # Append the transformed result to the list
        transformed_results_by_time.append(transformed_result)

    return transformed_results_by_time


while True:
    fetch_service_cost("Amazon Elastic Compute Cloud - Compute")
    fetch_service_cost("Amazon Simple Storage Service")
    # Sleep for 24 hours
    time.sleep(60 * 60 * 24)
