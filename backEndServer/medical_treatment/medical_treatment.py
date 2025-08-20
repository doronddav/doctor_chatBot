from typing import List, TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_aws import ChatBedrock
import boto3
import os
from dotenv import load_dotenv
load_dotenv()

client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN")

)
llm = ChatBedrock(
    model_id='anthropic.claude-3-5-sonnet-20240620-v1:0', client=client)

user_sessions = {}


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    name: str
    finish: bool
    return_data: str
    stage: str
    user_feeling_prompt: str

# TOOLS


@tool
def feeling_data_save(name: str) -> str:
    """Save the current conversation to a text file and finish the process."""
    print('\n \t\tSAVETOOLLL \n')

    session = user_sessions.get(name, {})
    user_feeling_prompt = session.get('user_feeling_prompt', '')

    fileName = f"{name.lower()}_medical_plan.txt"

    try:
        with open(fileName, 'w') as file:
            file.write(user_feeling_prompt)
            print(f"\nMedical content saved to {fileName}")
            return f"Saved medical content to {fileName}"
    except Exception as e:
        return f"Failed to save medical content: {str(e)}"


@tool
def update_medical_situation(content: str) -> str:
    """Update the medical document with the new content."""
    print('\n \tUPDATE TOOL \n')
    return f"Updated medical content:\n {content}"


tools = [feeling_data_save, update_medical_situation]
llm = llm.bind_tools(tools)


def process_user_message(user_name: str, user_message: str) -> dict:

    if user_name not in user_sessions:
        user_sessions[user_name] = {
            'stage': 'greeting',
            'messages': [],
            'user_feeling_prompt': '',
            'collected_info': {
                'pain_location': None,
                'body_heat': None,
                'previous_treatment': None
            }
        }

    session = user_sessions[user_name]

    if session['stage'] == 'greeting':
        session['stage'] = 'questions'
        return {
            'reply': f"שלום {user_name}! אני דוקטור AI. איך אתה מרגיש היום? ספר לי מה מציק לך.",
            'stage': 'questions',
            'finished': False
        }

    elif session['stage'] == 'questions':
        return handle_questions_stage(user_name, user_message)

    elif session['stage'] == 'treatment':
        return handle_treatment_stage(user_name, user_message)

    else:
        return {'reply': 'שגיאה במערכת', 'stage': 'error', 'finished': False}


def handle_questions_stage(user_name: str, user_message: str) -> dict:
    """Handle the questions gathering stage"""
    session = user_sessions[user_name]

    system_prompt = SystemMessage(f"""
    You are a doctor. You should assist user to find the best treatment for their health.
    
    Talk only in Hebrew!
    
    You need to gather this information from the user:
    - What part of the body hurts? (organ like stomach, throat, head etc.)
    - Body temperature/heat symptoms
    - Any previous treatment they've tried
    
    Current collected info: {session['collected_info']}
    
    Ask clear, follow-up questions **one at a time** to gather missing information.
    Once all info is collected, say: "כל המידע נאסף! מכין את ההמלצות הרפואיות..."
    
    Be empathetic and professional.
    """)

    user_msg = HumanMessage(content=user_message)
    session['messages'].append(user_msg)

    response = llm.invoke([system_prompt] + session['messages'])
    session['messages'].append(AIMessage(content=response.content))

    if "כל המידע נאסף" in response.content or "מכין את ההמלצות" in response.content:
        session['stage'] = 'treatment'
        return {
            'reply': response.content,
            'stage': 'treatment',
            'finished': False
        }

    return {
        'reply': response.content,
        'stage': 'questions',
        'finished': False
    }


def handle_treatment_stage(user_name: str, user_message: str) -> dict:
    session = user_sessions[user_name]

    system_prompt = SystemMessage(content=f"""
You are a Doctor Agent. You are a helpful assistant that helps users understand what to do when they are sick.

Talk only in Hebrew!

You should help the user understand:
- What might be happening with them based on symptoms
- Folk remedies for their situation
- Over-the-counter medications available in Israel
- When to see a doctor

Current conversation history contains the symptoms and info gathered.

- FIRST: Always call update_medical_situation tool with your complete medical recommendations
- THEN: Provide your response to the user  
- If the user wants to finish or save the content, use the feeling_data_save tool with the user name: {user_name}

Always provide medical diagnosis possibilities and treatment recommendations.
Be clear that this is not a substitute for professional medical advice.
""")

    if any(word in user_message.lower() for word in ['שמור', 'סיים', 'תודה', 'זה הכל']):
        save_result = feeling_data_save(user_name)
        return {
            'reply': f"תודה! {save_result}. אני מקווה שעזרתי לך. זכור - אם המצב מחמיר, חשוב לפנות לרופא!",
            'stage': 'finished',
            'finished': True
        }

    user_msg = HumanMessage(content=user_message)
    session['messages'].append(user_msg)

    response = llm.invoke([system_prompt] + session['messages'])
    session['messages'].append(response)

    # Update the session's medical content if tool was called
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call['name'] == 'update_medical_situation':
                session['user_feeling_prompt'] = tool_call['args']['content']

    return {
        'reply': response.content,
        'stage': 'treatment',
        'finished': False
    }


def run_doctor_chat_session(name: str, message: str) -> str:
    """Main function to handle chat sessions - simplified for API use"""
    result = process_user_message(name, message)
    return result['reply']


def get_session_info(user_name: str) -> dict:
    """Get current session information"""
    if user_name in user_sessions:
        session = user_sessions[user_name]
        return {
            'stage': session['stage'],
            'message_count': len(session['messages']),
            'collected_info': session['collected_info']
        }
    return {'stage': 'new', 'message_count': 0, 'collected_info': {}}


def reset_session(user_name: str):
    """Reset a user's session"""
    if user_name in user_sessions:
        del user_sessions[user_name]
