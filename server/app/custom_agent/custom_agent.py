import json
from . import (
    get_rent_data,
    get_sale_data
)
from agents import Agent, WebSearchTool, function_tool

STYLE_INSTRUCTIONS = "Use a conversational tone and write in a chat style without formal formatting or lists and do not use any emojis."


@function_tool
def get_rent_data() -> str:
    '''
        Function to recover rent data from the default data.
    '''
    return json.dumps(get_rent_data())

@function_tool
def get_sale_data() -> str:
    '''
        Function to recover sale data from the default data.
    '''
    return json.dumps(get_sale_data())


# declare the agents
rent_support_agent = Agent(
    name="Rent Support Agent",
    instructions=f"You are a rent support assistant. {STYLE_INSTRUCTIONS}",
    model="gpt-4o-mini",
    tools=[get_rent_data],
)

sale_support_agent = Agent(
    name="Sale Support Agent",
    instructions=f"You are a sale support assistant. {STYLE_INSTRUCTIONS}",
    model="gpt-4o-mini",
    tools=[get_sale_data],
)