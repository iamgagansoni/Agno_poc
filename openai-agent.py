# from typing import Optional
from agno.agent import Agent
# from agno.memory.v2.db.mongodb import MongoMemoryDb
# from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat
# from agno.storage.agent.mongodb import MongoDbAgentStorage
from agno.models.groq import Groq
from textwrap import dedent
from agno.team.team import Team
from tools import salesforce_tool, opp_salesforce_tools
from agno.utils import log
player1 = Agent(
    name="Salesforce_agent1",
    role="allow users to create, retrieve, summarize, and delete support cases and comments, streamlining CRM operations in salesforce.",
    model=OpenAIChat(id = "gpt-4o"),
    add_name_to_instructions=True,
    instructions = dedent("""
    You are a salesforce Agent.
    On the basis of the instructions provided you will do the following tasks:
                          1. fetching case comments
                          2. creating new cases in salesforce.
                          3. delete case in salesforce.
                          4. execute soql query.
                          """),
    tools=[salesforce_tool,],
)

player2 = Agent(
    name="Salesforce_agent2",
    role="fetching and updating opportunities, retrieving leads, and generating personalized outreach emails—streamlining CRM workflows in salesforce",
    model=Groq(id = "llama3-70b-8192"),
    add_name_to_instructions=True,
    instructions = dedent("""    
    You are a salesforce Agent.
    On the basis of the instructions provided you will do the following tasks:
                          1. Fetch all opportunities from Salesforce 
                          2. Fetch the full details of an opportunity by its ID
                          3. Update the stage of an opportunity in Salesforce.
                          4. Validate and update the lifecycle stage of an opportunity based on user-selected option.
                          5. Fetch all leads from Salesforce and display them with ID for follow-up.
                          """),
    tools=[opp_salesforce_tools,]
)

agent_team = Team(
    name="Orchestrator",
    mode="coordinate",
    model=OpenAIChat(id = "gpt-4o"),
    success_criteria="Give the relivant answer to the user query by determining the operation and tool involved",
    members=[player1,player2],
    instructions=[
        "You are a agent master.",
        "Determine the User input and relivant tool to be used on the basis of user ",
        "On the basis of that tool display the result"
    ],
    enable_agentic_context=True,
    share_member_interactions=True,
    show_tool_calls=True,
    debug_mode=True,
    markdown=True,
    show_members_responses=True,
)


agent_team.print_response(
    message="Give all opportunity on salesforce.",
    stream=True,
    stream_intermediate_steps=True,
)
