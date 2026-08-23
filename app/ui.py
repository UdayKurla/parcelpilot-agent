import sys
import os
from pathlib import Path

# Add project root directory to sys.path so 'app.*' imports resolve on Streamlit Cloud
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import json
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from app.tools import search_documentation, query_operational_data, stage_ticket_action

# Explicitly load local .env if present
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Retrieve API key from environment or Streamlit Cloud secrets
google_key = os.getenv("GOOGLE_API_KEY")
if not google_key and hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets:
    google_key = st.secrets["GOOGLE_API_KEY"]

st.set_page_config(
    page_title="ParcelPilot Support & Ops AI Agent",
    page_icon="📦",
    layout="wide"
)

st.title("📦 ParcelPilot Support & Operations Agent")

with st.sidebar:
    st.header("Context & Access Scope")
    user_role = st.selectbox(
        "Active Role Context",
        ["customer", "internal_ops"],
        help="Switches access boundaries between customer and internal staff."
    )
    
    account_id = None
    if user_role == "customer":
        account_id = st.selectbox(
            "Customer Account",
            ["ACCT-001", "ACCT-002", "ACCT-003", "ACCT-004"],
            help="Enforces data-layer tenancy isolation."
        )
    
    st.markdown("---")
    st.caption("📅 **Snapshot Reference Time**: `2026-08-16 11:00 IST`")
    st.caption("🔒 **Data Access**: Layer-enforced scoping")
    st.caption("⚡ **LLM Engine**: Gemini Flash")
    
    if not google_key:
        st.error("⚠️ GOOGLE_API_KEY not detected in .env or Streamlit Secrets!")

    if st.button("Clear Conversation History"):
        st.session_state.messages = []
        st.session_state.raw_thread = []
        st.rerun()

def extract_clean_text(content) -> str:
    """Extracts human-readable markdown text from string or structured content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
            elif isinstance(part, str):
                text_parts.append(part)
        return "\n".join(text_parts)
    return str(content)

# Tool registry
tools = [search_documentation, query_operational_data, stage_ticket_action]
tools_dict = {t.name: t for t in tools}

if google_key:
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        google_api_key=google_key
    )
    llm_with_tools = llm.bind_tools(tools)
else:
    llm_with_tools = None

system_prompt = f"""You are the ParcelPilot Support and Operations AI Agent.
Dataset Snapshot Time: 2026-08-16 11:00 Asia/Kolkata. Calculate all time deltas, SLAs, and delays from this timestamp.

Active Session Context:
- User Role: {user_role}
- Account ID: {account_id if account_id else 'All Accounts (Authorized Internal Ops)'}

Operating Guidelines:
1. Source Authority Precedence: Customer Agreement (Tier 4) > Current SOPs / Policy v3 (Tier 3) > Product Guide (Tier 2).
2. NEVER use Deprecated Policy v2 for active guidance.
3. Historical ticket resolutions are context-only and may be wrong.
4. For state-changing actions (escalations, fee waivers, ticket updates), call stage_ticket_action and ask for explicit user confirmation before proceeding.
5. If the user replies with 'Confirm' or confirms a pending staged action, acknowledge that the action has been successfully scheduled and executed.
6. Provide clear, step-by-step reasoning with citations of which document or database record was used.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []
if "raw_thread" not in st.session_state:
    st.session_state.raw_thread = []

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "steps" in msg and msg["steps"]:
            with st.expander("🛠️ Tool Execution Trace"):
                st.json(msg["steps"])

# User Chat Input
if prompt_input := st.chat_input("Ask a question or request an action..."):
    if not google_key:
        st.error("Please configure your GOOGLE_API_KEY in the Streamlit secrets or .env file.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt_input})
    with st.chat_message("user"):
        st.markdown(prompt_input)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing data & policies..."):
            try:
                thread_messages = [SystemMessage(content=system_prompt)] + list(st.session_state.raw_thread)
                thread_messages.append(HumanMessage(content=prompt_input))

                step_details = []
                final_ai_msg = None

                # Multi-turn tool execution loop
                for _ in range(5):
                    ai_msg = llm_with_tools.invoke(thread_messages)
                    thread_messages.append(ai_msg)

                    if not ai_msg.tool_calls:
                        final_ai_msg = ai_msg
                        break

                    for tool_call in ai_msg.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]
                        
                        if "account_id" in tool_args and not tool_args.get("account_id") and account_id:
                            tool_args["account_id"] = account_id
                        if "user_role" in tool_args and not tool_args.get("user_role"):
                            tool_args["user_role"] = user_role

                        selected_tool = tools_dict.get(tool_name)
                        if selected_tool:
                            tool_output = selected_tool.invoke(tool_args)
                        else:
                            tool_output = f"Tool '{tool_name}' not found."

                        step_details.append({
                            "tool": tool_name,
                            "input": tool_args,
                            "output": str(tool_output)[:500]
                        })

                        thread_messages.append(ToolMessage(
                            content=str(tool_output),
                            tool_call_id=tool_call["id"]
                        ))
                else:
                    final_ai_msg = ai_msg

                # Extract and display clean Markdown response
                clean_text = extract_clean_text(final_ai_msg.content)
                st.markdown(clean_text)
                
                if step_details:
                    with st.expander("🛠️ Tool Execution Trace"):
                        st.json(step_details)

                # Persist conversational state
                st.session_state.raw_thread = thread_messages[1:]  # Exclude system prompt
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": clean_text,
                    "steps": step_details
                })
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")
