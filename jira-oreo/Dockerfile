# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc bash

# Install Python dependencies
# COPY requirements.txt .
RUN pip install requests

# Copy project
COPY jira_reports.py /app/jira_reports.py
# COPY sample.env /app/.env

# Command to run the script
CMD [ "python", "./jira_reports.py" ]
