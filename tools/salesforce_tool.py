import os
import requests
import json
from agno.tools import tool

def get_access_token():
    """
    Get an access token using the OAuth 2.0 Password Grant Flow.
    """
    auth_url = 'https://login.salesforce.com/services/oauth2/token'

    # Request parameters for the password grant flow
    data = {
        'grant_type': 'password',
        'client_id': os.getenv("SF_CONSUMER_KEY"),
        'client_secret': os.getenv("SF_CONSUMER_SECRET"),
        'username': os.getenv("SF_USERNAME"),
        'password': os.getenv("SF_PASSWORD")+os.getenv("SF_SECURITY_TOKEN")
    }

    # Send POST request to get the access token
    response = requests.post(auth_url, data=data)

    if response.status_code == 200:
        response_data = response.json()
        access_token = response_data.get('access_token')
        instance_url = response_data.get('instance_url')
        return access_token, instance_url
    else:
        raise Exception(f"Error fetching access token: {response.status_code}, {response.text}")

@tool(description="Fetch case comments from Salesforce for a specific case number and summarize them.")
def fetch_case_comments(case_number: str):
    """
    Fetch case comments from Salesforce for a specific case number and summarize them.

    Args:
        case_number (str): The Salesforce Case Number to fetch comments for.

    Returns:
        str: Case comments summary with creation dates.
    """
    
    # Get Salesforce access token and instance URL
    access_token, instance_url = get_access_token()

    # Define the query to retrieve the case comments
    query = f"SELECT Id, CommentBody, CreatedDate FROM CaseComment WHERE ParentId IN (SELECT Id FROM Case WHERE CaseNumber = '{case_number}')"

    # Define headers for the request
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Salesforce API version
    api_version = 'v57.0'

    # Send the GET request to Salesforce API to fetch case comments
    response = requests.get(f'{instance_url}/services/data/{api_version}/query', headers=headers, params={'q': query})

    # Check the response status and return the case comments
    if response.status_code == 200:
        case_comments = response.json().get('records', [])
        if not case_comments:
            return "*❌ No comments found for this case number.*"
        
        # In Agno, we don't directly use OpenAI or other LLMs within tools
        # Instead, we collect and format the data for the main agent to process
        
        # Format comments for display
        formatted_comments = ""
        for comment in case_comments:
            formatted_comments += (
                f"*📝 Comment:* {comment['CommentBody']}\n"
                f"*📅 Created On:* {comment['CreatedDate']}\n\n"
            )
        
        # Return the raw comments - the agent will handle summarization
        return (
            "*✅ Case Comments Retrieved Successfully!*\n\n"
            f"*🎫 Case Number:* `{case_number}`\n\n"
            f"*🔎 Full Comments:* \n{formatted_comments}"
        )
    else:
        return f"*❌ Error fetching case comments: {response.status_code}, {response.text}*"

@tool(description="Create a new case in Salesforce with subject, description and priority.")
def create_case_in_salesforce(case_subject: str, case_description: str, case_priority: str):
    """
    Create a new case in Salesforce.

    Args:
        case_subject (str): The subject/title of the case.
        case_description (str): A detailed description of the case.
        case_priority (str): Priority of the case (e.g., High, Medium, Low).

    Returns:
        str: Confirmation and case details.
    """
    
    # Get Salesforce access token and instance URL
    access_token, instance_url = get_access_token()

    # Define the data to create a new case
    case_data = {
        "Subject": case_subject,
        "Description": case_description,
        "Priority": case_priority,
        "Status": "New",
        "Origin": "Web"
    }

    # Define headers for the request
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Salesforce API version
    api_version = 'v57.0'

    # Send the POST request to Salesforce API to create a new case
    response = requests.post(f'{instance_url}/services/data/{api_version}/sobjects/Case/', headers=headers, json=case_data)

    # Check the response status and return case creation details
    if response.status_code == 201:
        created_case = response.json()
        case_id = created_case.get('id')

        return (
            "*✅ Case Created Successfully!*\n\n"
            f"*🎫 Case ID:* `{case_id}`\n\n"
            f"*🔎 Case Details:*\n"
            f"Subject: {case_subject}\n"
            f"Description: {case_description}\n"
            f"Priority: {case_priority}"
        )
    else:
        return f"*❌ Error creating case: {response.status_code}, {response.text}*"
    
@tool(description="Delete a specific case in Salesforce by its case ID.")
def delete_case_in_salesforce(case_id: str):
    """
    Delete a specific case in Salesforce by its case ID.

    Args:
        case_id (str): The Salesforce Case ID to delete.

    Returns:
        str: Confirmation message whether the case was deleted or not.
    """
    
    # Get Salesforce access token and instance URL
    access_token, instance_url = get_access_token()

    # Define headers for the request
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Salesforce API version
    api_version = 'v57.0'

    # Send the DELETE request to Salesforce API to delete the case
    response = requests.delete(f'{instance_url}/services/data/{api_version}/sobjects/Case/{case_id}', headers=headers)

    # Check the response status and return case deletion result
    if response.status_code == 204:
        return f"*✅ Case with ID `{case_id}` was deleted successfully!*"
    else:
        return f"*❌ Error deleting the case with ID `{case_id}`: {response.status_code}, {response.text}*"

@tool(description="Execute a SOQL query in Salesforce.")
def execute_soql_query(soql_query: str):
    """
    Execute a SOQL query in Salesforce.
    
    Args:
        soql_query (str): The SOQL query to execute.
    
    Returns:
        str: The result of the executed SOQL query.
    """
    
    # Get Salesforce access token and instance URL
    access_token, instance_url = get_access_token()
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    api_version = 'v57.0'

    # Send the GET request to Salesforce API to execute the query
    response = requests.get(f'{instance_url}/services/data/{api_version}/query', headers=headers, params={'q': soql_query})

    # Check the response and format the result
    if response.status_code == 200:
        records = response.json().get('records', [])