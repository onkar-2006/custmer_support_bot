import sqlite3
import json
import os
import io
import operator
import logging
from typing import TypedDict, Annotated, List, Union
from pathlib import Path

# --- Third-party imports for the server and voice capabilities ---
from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
# Using the standard 'groq' library for Whisper STT
from groq import Groq
# Using gTTS for simple TTS synthesis
from gtts import gTTS
from dotenv import load_dotenv

# --- LangChain/LangGraph imports (User's original code) ---
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END

# --- Global Setup ---
logging.basicConfig(level=logging.INFO)
load_dotenv()
DB_FILE = "customer_support.db"
# Session storage for LangGraph state
conversation_history = {}
GROQ_MODEL = "llama-3.3-70b-versatile"

try:
    # Initialize the Groq client for Whisper transcription
    groq_client = Groq()
except Exception as e:
    logging.error(f"Error initializing Groq client: {e}. Check your GROQ_API_KEY.")
    groq_client = None

# Initialize Flask App
app = Flask(__name__)
CORS(app)  # Enable CORS for client interaction


# --- Database Setup (User's original code) ---

def setup_database():
    """Initializes the SQLite database and creates the 'issues' table."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            issue TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database setup complete: {DB_FILE} and 'issues' table ready.")


setup_database()


# --- Tool Definitions (User's original code) ---

@tool
def register_customer_issue(name: str, issue: str) -> str:
    """
    Registers a new customer issue in the database.
    Requires the customer's full name and a description of the issue.
    Returns a confirmation message with the name and issue status.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO issues (name, issue) VALUES (?, ?)", (name, issue))
        conn.commit()
        return f"Issue registered successfully for {name}. Issue description: '{issue}'. You can now confirm to the user that their ticket has been created."
    except Exception as e:
        conn.rollback()
        return f"Error registering issue: {e}"
    finally:
        conn.close()


@tool
def get_customer_issues(name: str = None) -> str:
    """
    Fetches the list of customer issues from the database.
    If 'name' is provided, it fetches issues only for that customer.
    If 'name' is None, it fetches the three most recent issues for a general overview.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if name:
        cursor.execute("SELECT name, issue FROM issues WHERE name LIKE ? ORDER BY id DESC", ('%' + name + '%',))
        results = cursor.fetchall()
        if not results:
            return f"No issues found for customer: {name}."
    else:
        cursor.execute("SELECT name, issue FROM issues ORDER BY id DESC LIMIT 3")
        results = cursor.fetchall()
        if not results:
            return "No recent issues found in the database."

    conn.close()

    formatted_issues = ["--- Fetched Issues ---"]
    for i, (customer_name, issue_desc) in enumerate(results, 1):
        formatted_issues.append(f"Ticket {i}. Customer: {customer_name}, Issue: {issue_desc}")

    return "\n".join(formatted_issues)


# --- LLM and Agent Setup (User's original code) ---

CUSTOMER_SUPPORT_PROMPT = """
You are a professional and helpful Customer Support Agent. Your goal is to assist users with their issues efficiently.
You will operate in a ReAct loop: **Think** about the next step, **Act** by calling a tool if needed, and **Observe** the tool's result.

You have access to two database tools: 'register_customer_issue' and 'get_customer_issues'.

Tool Usage Rules:
1.  **ALWAYS** use the 'register_customer_issue' tool when a user states a new problem or requests to log a ticket. You MUST extract the customer's full name and the full issue description accurately for the tool.
2.  Use 'get_customer_issues' if the user asks for history, checks on past tickets, or inquires about existing issues.
3.  After using a tool, you MUST synthesize the tool output and respond professionally, clearly, and concisely to the user.
"""

llm = ChatGroq(
    model=GROQ_MODEL,
    temperature=0
)

tools = [register_customer_issue, get_customer_issues]
llm_with_tools = llm.bind_tools(tools)


# --- LangGraph State and Nodes (User's original code) ---

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]


def agent_node(state: AgentState):
    """The main node where the LLM decides to respond or call a tool (ReAct Agent)."""
    messages = state['messages']
    prompt_messages = [SystemMessage(content=CUSTOMER_SUPPORT_PROMPT)] + messages
    response = llm_with_tools.invoke(prompt_messages)
    return {"messages": [response]}


def tool_node(state: AgentState):
    """Executes the tool calls requested by the LLM (Action/Observation)."""
    tool_calls = state['messages'][-1].tool_calls
    tool_results = []

    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        # Map tool name to the function object
        tool_map = {"register_customer_issue": register_customer_issue,
                    "get_customer_issues": get_customer_issues}
        selected_tool = tool_map[tool_name]

        # Execute the tool
        output = selected_tool.invoke(tool_args)

        # Append the tool result as a ToolMessage (more accurate than HumanMessage)
        tool_results.append(ToolMessage(
            content=output,
            tool_call_id=tool_call["id"],
        ))

    return {"messages": tool_results}


# --- Graph Definition (User's original code) ---

def should_continue(state: AgentState):
    """Decides whether to continue the loop (call tool) or end (respond to user)."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "call_tool"
    return "end"


def create_customer_support_graph():
    """Compiles the LangGraph StateGraph."""
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("call_tool", tool_node)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"call_tool": "call_tool", "end": END}
    )

    workflow.add_edge('call_tool', 'agent')

    return workflow.compile()


# Compile the LangGraph agent globally
customer_support_app = create_customer_support_graph()


# --- Flask Server Routes for Voice/Chat Capability ---

@app.route('/')
def home():
    """Simple check to ensure the server is running."""
    return f"Customer Support Voice Assistant Backend is running! Groq Model: {GROQ_MODEL}"


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handles the voice assistant chat interaction: STT -> LangGraph -> TTS.
    """
    try:
        if groq_client is None:
            return jsonify({"error": "Groq client not initialized. Check API Key."}), 500

        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio']
        session_id = request.form.get('session_id')
        if not session_id:
            session_id = os.urandom(16).hex()

        response_headers = {"X-Session-ID": session_id}

        # 1. Save audio temporarily for Whisper API
        temp_audio_path = Path(f"temp_user_input_{session_id}.wav")
        audio_file.save(temp_audio_path)

        # 2. Transcribe Audio (STT)
        with open(temp_audio_path, "rb") as audio:
            transcription = groq_client.audio.transcriptions.create(
                file=audio,
                model="whisper-large-v3",
                response_format="text"
            )
        user_text = transcription.strip()
        os.remove(temp_audio_path)

        logging.info(f"User said (Transcription): {user_text}")
        response_headers["X-Transcription"] = user_text

        if not user_text:
            response_text = "I didn't hear a command. Could you please speak up?"
        else:
            # 3. Invoke LangGraph Agent
            if session_id not in conversation_history:
                # Initialize new session state
                conversation_history[session_id] = {"messages": [], "intermediate_steps": []}

            user_message = HumanMessage(content=user_text)
            current_state = conversation_history[session_id]
            new_state = current_state.copy()
            new_state['messages'] = current_state['messages'] + [user_message]

            logging.info("Invoking LangGraph agent...")

            # Using the pre-compiled graph
            result = customer_support_app.invoke(new_state)

            ai_response_message = result["messages"][-1]
            response_text = ai_response_message.content

            # Update history state
            conversation_history[session_id] = result

        logging.info(f"Assistant says: {response_text}")

        # 4. Generate Spoken Response (TTS)
        tts = gTTS(text=response_text, lang='en')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        # 5. Return Audio Response
        response = make_response(send_file(
            audio_buffer,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="response.mp3"
        ))
        for key, value in response_headers.items():
            response.headers[key] = value

        return response

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        # Error handling response via TTS
        error_response_text = "I am sorry, an unexpected error occurred. Please check the server logs."
        tts = gTTS(text=error_response_text, lang='en')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        error_response = make_response(send_file(
            audio_buffer,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="error.mp3"
        ))
        error_response.status_code = 500
        return error_response


# --- Main Execution ---

if __name__ == '__main__':
    print("\n--- Customer Support Voice Assistant Server Initialized ---")
    print("Ensure you have a GROQ_API_KEY and the necessary Python libraries installed.")
    print("Running server on http://127.0.0.1:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
