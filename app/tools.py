import json
from langchain_core.tools import tool
from typing import Optional
from app.database import ParcelPilotDB
from app.rag_engine import ParcelPilotKnowledgeBase

db = ParcelPilotDB()
kb = ParcelPilotKnowledgeBase()

@tool
def search_documentation(query: str, account_id: Optional[str] = None) -> str:
    """
    Search support policies, cancellation SOPs, product guides, and enterprise agreements.
    Applies strict source authority: Customer Agreement > Current SOP/Policy > Product Guide.
    """
    results = kb.search(query=query, account_id=account_id)
    if not results:
        return "No matching documentation found."

    formatted = []
    for r in results[:3]:
        formatted.append(
            f"=== Source: {r['filename']} (Authority Tier: {r['authority_level']}) ===\n"
            f"{r['content']}\n"
        )
    return "\n\n".join(formatted)

@tool
def query_operational_data(sql_query: str, session_account_id: Optional[str] = None, user_role: str = "internal") -> str:
    """
    Query structured SQL tables: 'accounts', 'orders', 'tickets'.
    Dataset frozen snapshot reference time: 2026-08-16 11:00 Asia/Kolkata.
    """
    res = db.execute_query(sql_query=sql_query, user_role=user_role, account_id=session_account_id)
    return json.dumps(res, indent=2, default=str)

@tool
def stage_ticket_action(action_type: str, target_id: str, reason: str, details: str) -> str:
    """
    Stage a state-changing ticket action (escalation, fee waiver, service credit).
    DOES NOT execute immediately. Prompts user for explicit confirmation.
    """
    return (
        f"[STAGED ACTION - PENDING CONFIRMATION]\n"
        f"- Action Type: {action_type}\n"
        f"- Target ID: {target_id}\n"
        f"- Justification: {reason}\n"
        f"- Action Details: {details}\n\n"
        f"Please reply 'Confirm' to execute this action."
    )