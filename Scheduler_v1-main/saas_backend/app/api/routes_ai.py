"""
saas_backend/app/api/routes_ai.py
AI Assistant endpoint — powered by Google Gemini 1.5 Flash.

Set GEMINI_API_KEY environment variable to enable real AI responses.
Falls back to rule-based mock responses if no API key is configured.
"""

import os
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.entities import ConflictLog, Faculty, ScheduleEntry, Subject

router = APIRouter()

GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

# Lazily initialise Gemini client only when the API key is available
_gemini_model = None


def _get_gemini_model():
    global _gemini_model
    if _gemini_model is None and GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            _gemini_model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=(
                    "You are an expert AI assistant for an Automated Class Scheduling System (ASCS) "
                    "used in a Philippine K-12 school. You help administrators optimise timetables, "
                    "resolve scheduling conflicts, suggest faculty assignments, and answer questions "
                    "about the schedule. Be concise, practical, and always use school-appropriate language. "
                    "Format your responses with markdown for clarity."
                ),
            )
        except ImportError:
            pass
    return _gemini_model


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    tenant_id: str = "local-tenant"


class ChatResponse(BaseModel):
    reply: str
    used_ai: bool = False


# ── Context builder ───────────────────────────────────────────────────────────
def _build_context(db: Session, tenant_id: str) -> str:
    """Fetch live DB context to inject into the AI prompt."""
    try:
        faculty_count    = db.query(Faculty).filter(Faculty.tenant_id == tenant_id).count()
        subject_count    = db.query(Subject).filter(Subject.tenant_id == tenant_id).count()
        scheduled_count  = db.query(ScheduleEntry).filter(ScheduleEntry.tenant_id == tenant_id, ScheduleEntry.status == "finalized").count()
        pending_count    = db.query(ScheduleEntry).filter(ScheduleEntry.tenant_id == tenant_id, ScheduleEntry.status == "pending").count()
        unassigned_count = db.query(ScheduleEntry).filter(ScheduleEntry.tenant_id == tenant_id, ScheduleEntry.faculty_id == None).count()  # noqa: E711
        conflict_count   = db.query(ConflictLog).filter(ConflictLog.tenant_id == tenant_id, ConflictLog.is_resolved == False).count()  # noqa: E712

        return (
            f"Current schedule context for tenant '{tenant_id}':\n"
            f"- Faculty members: {faculty_count}\n"
            f"- Subjects configured: {subject_count}\n"
            f"- Finalized schedule entries: {scheduled_count}\n"
            f"- Pending schedule entries: {pending_count}\n"
            f"- Entries without assigned faculty: {unassigned_count}\n"
            f"- Unresolved conflicts: {conflict_count}\n"
        )
    except Exception:
        return "Context unavailable (database not seeded yet).\n"


# ── Fallback rule-based responses ─────────────────────────────────────────────
def _fallback_response(message: str) -> str:
    msg_lower = message.lower()
    if any(kw in msg_lower for kw in ["unassigned", "suggestion", "suggest", "recommend"]):
        return (
            "📋 **Unassigned Subjects**\n\n"
            "Based on the current schedule, some subjects are unassigned. "
            "To get AI-powered suggestions, please set your **GEMINI_API_KEY** environment variable.\n\n"
            "**Quick Tips:**\n"
            "- Check the Dashboard for unassigned subjects count\n"
            "- Use the Manual Override section to assign them manually\n"
            "- Ensure faculty members have subjects assigned in the Faculty Manager"
        )
    elif any(kw in msg_lower for kw in ["conflict", "scan", "error", "double"]):
        return (
            "🔍 **Conflict Scan**\n\n"
            "To run a real-time conflict scan, the Conflict Monitor runs automatically after schedule generation.\n\n"
            "**Common conflicts to check:**\n"
            "- 🔴 Room double-booking (same room, same period, different sections)\n"
            "- 🟡 Teacher consecutive classes (5+ periods in a row)\n"
            "- 🟡 Lunch period violations"
        )
    elif any(kw in msg_lower for kw in ["help", "what can you", "how"]):
        return (
            "👋 **I'm the ASCS AI Assistant!**\n\n"
            "I can help you with:\n"
            "- 📋 **Unassigned subjects** — get suggestions for placement\n"
            "- 🔍 **Conflict detection** — find scheduling conflicts\n"
            "- 👩‍🏫 **Faculty load** — check teacher workload balance\n"
            "- 📅 **Schedule optimization** — tips to improve your timetable\n\n"
            "_For full AI capabilities, set your GEMINI_API_KEY environment variable._"
        )
    else:
        return (
            f"🤖 I understand you asked: **\"{message}\"**\n\n"
            "I'm currently running in demo mode. For real AI-powered responses, "
            "configure your `GEMINI_API_KEY` environment variable.\n\n"
            "Try asking me about:\n- Unassigned subjects\n- Schedule conflicts\n- Faculty load balancing"
        )


# ── Route ─────────────────────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
def ai_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    AI Scheduling Assistant endpoint.
    Uses Google Gemini 1.5 Flash when GEMINI_API_KEY is set,
    otherwise falls back to rule-based responses.
    """
    model = _get_gemini_model()

    if model:
        try:
            context = _build_context(db, request.tenant_id)
            full_prompt = f"{context}\n\nUser question: {request.message}"
            response = model.generate_content(full_prompt)
            return ChatResponse(reply=response.text, used_ai=True)
        except Exception as exc:
            # Graceful fallback if Gemini call fails
            return ChatResponse(
                reply=f"⚠️ AI temporarily unavailable: {str(exc)[:100]}\n\n" + _fallback_response(request.message),
                used_ai=False,
            )

    return ChatResponse(reply=_fallback_response(request.message), used_ai=False)
