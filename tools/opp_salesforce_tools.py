import os
import requests
import json
from agno.tools import tool

# Get Access Token
def get_access_token():
    """
    Get an access token using the OAuth 2.0 Password Grant Flow.
    """
    auth_url = 'https://login.salesforce.com/services/oauth2/token'
    data = {
        'grant_type': 'password',
        'client_id': os.getenv("SF_CONSUMER_KEY"),
        'client_secret': os.getenv("SF_CONSUMER_SECRET"),
        'username': os.getenv("SF_USERNAME"),
        'password': os.getenv("SF_PASSWORD") + os.getenv("SF_SECURITY_TOKEN")
    }

    response = requests.post(auth_url, data=data)

    if response.status_code == 200:
        response_data = response.json()
        access_token = response_data.get('access_token')
        instance_url = response_data.get('instance_url')
        return access_token, instance_url
    else:
        raise Exception(f"Error fetching access token: {response.status_code}, {response.text}")

# Generate Prompt for Lifecycle Transition
def generate_lifecycle_transition_prompt(opportunity_name, current_stage, new_stage):
    """
    Generate a prompt that helps guide the lifecycle transition process for an opportunity.

    Args:
        opportunity_name (str): The name of the opportunity.
        current_stage (str): The current stage of the opportunity.
        new_stage (str): The stage to which the opportunity is being transitioned.

    Returns:
        str: The prompt text that guides the lifecycle transition.
    """
    prompt_template = f"""
    You are a Salesforce assistant. I have an opportunity called '{opportunity_name}' which is currently in the '{current_stage}' stage.
    The sales team wants to update it to the '{new_stage}' stage. Please confirm if all necessary conditions are met for this transition.
    If so, proceed with the update. If there are any blockers or reasons why this transition can't happen, provide suggestions to resolve them.
    """
    return prompt_template

# Fetch All Opportunities and Present Them
@tool(description="Fetch all opportunities from Salesforce and display them with ID for easy follow-up.")
def fetch_opportunities():
    """
    Fetch all opportunities from Salesforce and display them with ID for easy follow-up.
    
    Returns:
        tuple: A tuple containing (formatted_opportunities_text, opportunity_options_dict)
    """
    soql_query = "SELECT Id, Name, StageName, CloseDate, Amount FROM Opportunity"
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
        if not records:
            return "*❌ No opportunities found.*", {}
        
        # Format the response
        formatted_opportunities = "*✅ Opportunities Retrieved Successfully!*\n\n"
        opportunity_options = {}
        
        for index, record in enumerate(records, start=1):
            formatted_opportunities += (
                f"*Option {index} - Opportunity Name:* {record['Name']}\n"
                f"*📅 Close Date:* {record['CloseDate']}\n"
                f"*💰 Amount:* {record['Amount']}\n"
                f"*📊 Stage:* {record['StageName']}\n\n"
            )
            opportunity_options[index] = record['Id']

        return formatted_opportunities, opportunity_options
    else:
        return f"*❌ Error fetching opportunities: {response.status_code}, {response.text}*", {}

# Fetch Opportunity Details by ID
def fetch_opportunity_details(opportunity_id):
    """
    Fetch the full details of an opportunity by its ID.

    Args:
        opportunity_id (str): The ID of the opportunity to fetch.

    Returns:
        dict: The opportunity details, including the current stage.
    """
    access_token, instance_url = get_access_token()

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    api_version = 'v57.0'
    opportunity_url = f"{instance_url}/services/data/{api_version}/sobjects/Opportunity/{opportunity_id}"

    # Send the GET request to Salesforce API to fetch the opportunity details
    response = requests.get(opportunity_url, headers=headers)

    if response.status_code == 200:
        return response.json()  # Return full opportunity details
    else:
        raise Exception(f"Error fetching opportunity details: {response.status_code}, {response.text}")

# Update Opportunity Stage in Salesforce
@tool(description="Update the stage of an opportunity in Salesforce.")
def update_opportunity_stage(opportunity_id: str, new_stage: str):
    """
    Update the stage of an opportunity in Salesforce.

    Args:
        opportunity_id (str): The ID of the opportunity to update.
        new_stage (str): The new stage to set for the opportunity.

    Returns:
        str: Success or failure message for the update.
    """
    access_token, instance_url = get_access_token()

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    api_version = 'v57.0'
    update_url = f"{instance_url}/services/data/{api_version}/sobjects/Opportunity/{opportunity_id}"

    # Prepare the data to update
    data = {
        'StageName': new_stage
    }

    response = requests.patch(update_url, headers=headers, json=data)

    if response.status_code == 204:
        return f"🎉 Opportunity stage successfully updated to {new_stage}!"
    else:
        return f"❌ Failed to update stage: {response.status_code}, {response.text}"

# Validate and Update Lifecycle Transition
@tool(description="Validate and update the lifecycle stage of an opportunity based on user-selected option.")
def validate_and_update_lifecycle_transition(opportunity_choice: int, new_stage: str):
    """
    Validate and update the lifecycle stage of an opportunity based on user-selected option.
    
    Args:
        opportunity_choice (int): The option number of the selected opportunity.
        new_stage (str): The new stage to set for the opportunity.
        
    Returns:
        str: Enhanced response with details about the transition.
    """
    # Fetch opportunities
    formatted_opportunities, opportunity_options = fetch_opportunities()

    if not opportunity_options:
        return formatted_opportunities  # No opportunities found

    # Validate user-selected opportunity
    if opportunity_choice not in opportunity_options:
        return "*❌ Invalid option selected. Please choose a valid option.*"

    # Get the opportunity ID based on the user selection
    opportunity_id = opportunity_options[opportunity_choice]

    # Fetch current opportunity details (including current stage)
    opportunity_details = fetch_opportunity_details(opportunity_id)
    current_stage = opportunity_details.get('StageName', 'Not Available')

    # Check if the current stage is the same as the new stage
    if current_stage == new_stage:
        return f"⚠️ The stage of the opportunity \"{opportunity_details['Name']}\" is already set to *{new_stage}*. There's no need to update!"

    # Generate lifecycle transition prompt
    lifecycle_prompt = generate_lifecycle_transition_prompt(opportunity_details['Name'], current_stage, new_stage)

    # Call the function to perform update
    update_message = update_opportunity_stage(opportunity_id, new_stage)

    # Format the final response with opportunity details
    enhanced_response = f"""
    🚀 **Opportunity Lifecycle Transition**:

    🔍 **Selected Opportunity**: Option {opportunity_choice}
    💵 **Opportunity Amount**: {opportunity_details.get('Amount', 'Not Available')}
    📅 **Close Date**: {opportunity_details.get('CloseDate', 'Not Available')}

    🎯 **New Stage**: {new_stage}

    💬 **Lifecycle Transition Prompt**:
    {lifecycle_prompt}

    ✅ **Action**: {update_message}
    """
    return enhanced_response

@tool(description="Fetch all leads from Salesforce and display them with ID for follow-up.")
def fetch_leads():
    """
    Fetch all leads from Salesforce and display them with ID for follow-up.
    
    Returns:
        tuple: A tuple containing (formatted_leads_text, lead_options_dict)
    """
    soql_query = "SELECT Id, FirstName, LastName, Company, Email, LeadSource FROM Lead"
    access_token, instance_url = get_access_token()

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    api_version = 'v57.0'

    # Send the GET request to Salesforce API to execute the query
    response = requests.get(f'{instance_url}/services/data/{api_version}/query', headers=headers, params={'q': soql_query})

    if response.status_code == 200:
        records = response.json().get('records', [])
        if not records:
            return "*❌ No leads found.*", {}

        # Format the response
        formatted_leads = "*✅ Leads Retrieved Successfully!*\n\n"
        lead_options = {}

        for index, record in enumerate(records, start=1):
            formatted_leads += (
                f"*Option {index} - Lead Name:* {record.get('FirstName', '')} {record.get('LastName', '')}\n"
                f"*🏢 Company:* {record.get('Company', '')}\n"
                f"*📧 Email:* {record.get('Email', '')}\n"
                f"*🔗 Lead Source:* {record.get('LeadSource', '')}\n\n"
            )
            lead_options[index] = record['Id']

        return formatted_leads, lead_options
    else:
        return f"*❌ Error fetching leads: {response.status_code}, {response.text}*", {}

@tool(description="Get detailed information about a lead by ID")
def get_lead_details(lead_id: str):
    """
    Get detailed information about a lead by ID.
    
    Args:
        lead_id (str): The ID of the lead to fetch details for.
        
    Returns:
        str: Formatted lead details
    """
    access_token, instance_url = get_access_token()

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    api_version = 'v57.0'
    lead_url = f"{instance_url}/services/data/{api_version}/sobjects/Lead/{lead_id}"

    # Fetch the lead details
    response = requests.get(lead_url, headers=headers)

    if response.status_code == 200:
        lead_details = response.json()
        
        # Format the lead details for display
        formatted_details = f"""
        📊 **Lead Details**:
        
        👤 **Name**: {lead_details.get('FirstName', '')} {lead_details.get('LastName', '')}
        🏢 **Company**: {lead_details.get('Company', '')}
        📧 **Email**: {lead_details.get('Email', '')}
        📱 **Phone**: {lead_details.get('Phone', '')}
        🔗 **Lead Source**: {lead_details.get('LeadSource', '')}
        🏆 **Status**: {lead_details.get('Status', '')}
        """
        
        return formatted_details
    else:
        return f"*❌ Error fetching lead details: {response.status_code}, {response.text}*"

@tool(description="Generate personalized email template for a lead using their details")
def get_lead_email_info(lead_id: str):
    """
    Get lead information for email generation.
    
    Args:
        lead_id (str): The ID of the lead to fetch details for.
        
    Returns:
        dict: Lead information needed for email generation
    """
    access_token, instance_url = get_access_token()

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    api_version = 'v57.0'
    lead_url = f"{instance_url}/services/data/{api_version}/sobjects/Lead/{lead_id}"

    # Fetch the lead details
    response = requests.get(lead_url, headers=headers)

    if response.status_code == 200:
        lead_details = response.json()
        
        # Return information for email generation
        return {
            "first_name": lead_details.get('FirstName', ''),
            "last_name": lead_details.get('LastName', ''),
            "company": lead_details.get('Company', ''),
            "lead_source": lead_details.get('LeadSource', ''),
            "email": lead_details.get('Email', '')
        }
    else:
        raise Exception(f"Error fetching lead details: {response.status_code}, {response.text}")