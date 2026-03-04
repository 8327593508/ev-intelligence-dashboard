import os
import re
import random
from typing import List, Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_groq import ChatGroq

# 🔥 PHASE 3 IMPORT
from analytics_engine import try_advanced_analytics

# 🔥 NEW: Assistant Helper Import
from assistant_helper import ConversationManager


# =====================================================
# LOAD ENV
# =====================================================
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL not found in ai_agent/.env")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in ai_agent/.env")


# =====================================================
# FASTAPI APP
# =====================================================
app = FastAPI(
    title="Moxie EV Intelligence Agent",
    version="4.3"
)


class QuestionRequest(BaseModel):
    question: str


# =====================================================
# DATABASE
# =====================================================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True
)

db = SQLDatabase(engine)


# =====================================================
# LLM
# =====================================================
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant",
    temperature=0
)

sql_chain = create_sql_query_chain(llm=llm, db=db)


# =====================================================
# CONFIG
# =====================================================
AGENT_NAME = "Moxie"

conversation_manager = ConversationManager()

GREETINGS = [
    "hi", "hello", "hey",
    "good morning", "good afternoon", "good evening",
    "namaste"
]

GREETING_FOLLOWUPS = [
    "How can I assist you with EV analytics today?",
    "What EV insights would you like to explore?",
    "Ask me about EV growth, registrations, or trends.",
    "Ready to analyze your EV database."
]


# =====================================================
# HELPERS
# =====================================================
def normalize(text: str) -> str:
    return text.lower().strip()


def is_greeting(q: str) -> bool:
    q = q.strip().lower()
    return q in GREETINGS


def clean_sql(raw_sql: str) -> str:
    if not raw_sql:
        return ""

    sql = str(raw_sql)
    sql = sql.replace("```sql", "").replace("```", "")

    prefixes = ["SQLQuery:", "SQLResult:", "Answer:", "Question:"]
    for p in prefixes:
        sql = sql.replace(p, "")

    select_index = sql.lower().find("select")
    if select_index != -1:
        sql = sql[select_index:]

    sql = sql.replace("[", "").replace("]", "")
    sql = sql.replace("\n", " ").strip().rstrip(";")

    return sql


def is_valid_select(sql: str) -> bool:
    if not sql:
        return False
    return sql.strip().lower().startswith("select")


def apply_guardrails(sql: str) -> str:

    sql = re.sub(
        r"\bev_registrations\b",
        "ev_registrations_state_weighted",
        sql,
        flags=re.IGNORECASE
    )

    sql = re.sub(
        r"\bregistration_count\b",
        "estimated_ev_registrations",
        sql,
        flags=re.IGNORECASE
    )

    exclusion = "state NOT IN ('India','Grand Total','Total','Unknown','')"
    lower_sql = sql.lower()

    if "where" in lower_sql:
        sql = re.sub(
            r"\bwhere\b",
            f"WHERE {exclusion} AND",
            sql,
            flags=re.IGNORECASE,
            count=1
        )
    else:
        match = re.search(r"\b(group by|order by|limit)\b", lower_sql)
        if match:
            idx = match.start()
            sql = sql[:idx] + f" WHERE {exclusion} " + sql[idx:]
        else:
            sql += f" WHERE {exclusion}"

    return sql


def generate_human_answer(question: str, data: List[Dict[str, Any]]) -> str:

    if not data:
        return "I couldn't find relevant EV data for your query."

    q = question.lower()

    if "total" in q:
        value = list(data[0].values())[0]
        return f"The total estimated EV registrations are approximately {int(value):,}."

    if len(data) > 1:

        lines = []
        for i, row in enumerate(data[:5], 1):
            state = row.get("state", "Unknown")
            val = row.get("total_registrations") or row.get("estimated_ev_registrations", 0)
            lines.append(f"{i}. {state} – {int(val):,} EV registrations")

        first_state = data[0].get("state", "Leading State")
        first_val = data[0].get("total_registrations") or data[0].get("estimated_ev_registrations", 0)

        if any(word in q for word in ["lowest", "least", "bottom"]):
            return (
                f"{first_state} has the lowest EV registrations ({int(first_val):,}).\n\n"
                + "\n".join(lines)
            )

        return (
            f"{first_state} leads EV adoption ({int(first_val):,}).\n\n"
            + "\n".join(lines)
        )

    return "Here are the EV insights derived from your database."


# =====================================================
# ENDPOINT
# =====================================================
@app.post("/ask")
async def ask_agent(request: QuestionRequest):

    question = normalize(request.question)

    if not question:
        return {"answer": "Please enter a valid EV-related question."}

    # HELP COMMAND
    if question == "help":
        conversation_manager.reset_counter()
        return {
            "answer": conversation_manager.generate_help_only(),
            "chart": None,
            "data": []
        }

    # Greeting
    if is_greeting(question):
        conversation_manager.reset_counter()

        if "good morning" in question:
            greet_reply = "Good morning"
        elif "good afternoon" in question:
            greet_reply = "Good afternoon"
        elif "good evening" in question:
            greet_reply = "Good evening"
        elif "namaste" in question:
            greet_reply = "Namaste"
        else:
            greet_reply = "Hello"

        return {
            "answer": f"{greet_reply}! I'm {AGENT_NAME} 🤖. {random.choice(GREETING_FOLLOWUPS)}"
        }

    try:

        # ADVANCED ENGINE
        advanced = try_advanced_analytics(question)

        if advanced:
            conversation_manager.reset_counter()

            final_sql = advanced["sql"]

            with engine.connect() as conn:
                result = conn.execute(text(final_sql))
                rows = result.fetchall()
                columns = result.keys()

            data = [dict(zip(columns, row)) for row in rows]
            # 🔥 SPECIAL CAGR CALCULATION
            if "start_value" in data[0] and "end_value" in data[0]:

                start_value = float(data[0]["start_value"] or 0)
                end_value = float(data[0]["end_value"] or 0)
                num_years = int(data[0].get("num_years", 0))

                if start_value > 0 and num_years > 0:

                    cagr = ((end_value / start_value) ** (1 / num_years)) - 1
                    cagr_percent = round(cagr * 100, 2)

                    return {
                        "answer": (
                            f"The CAGR over {num_years} years is {cagr_percent}%.\n\n"
                            f"EV registrations increased from {int(start_value):,} "
                            f"to {int(end_value):,}."
                        ),
                        "chart": None,
                        "data": data
                    }
            chart = None
            if advanced.get("chart_type") and len(data) > 1:
                chart = {
                    "type": advanced["chart_type"],
                    "labels": [list(d.values())[0] for d in data],
                    "values": [float(list(d.values())[1]) for d in data]
                }

            return {
                "answer": advanced["summary"],
                "chart": chart,
                "data": data
            }

        # LANGCHAIN FALLBACK
        raw_sql = sql_chain.invoke({"question": question})
        generated_sql = clean_sql(raw_sql)

        if not is_valid_select(generated_sql):

            conversation_manager.register_general_response()

            if conversation_manager.should_suggest_help():
                suggestions = conversation_manager.generate_help_only()
                conversation_manager.reset_counter()

                return {
                    "answer": (
                        "I couldn't generate a proper EV analytics query.\n\n"
                        "Tip: You can type 'help' to see example prompts.\n\n"
                        f"{suggestions}"
                    ),
                    "chart": None,
                    "data": []
                }

            return {
                "answer": "I couldn't generate a proper EV analytics query.",
                "chart": None,
                "data": []
            }

        conversation_manager.reset_counter()

        final_sql = apply_guardrails(generated_sql)

        with engine.connect() as conn:
            result = conn.execute(text(final_sql))
            rows = result.fetchall()
            columns = result.keys()

        data = [dict(zip(columns, row)) for row in rows]

        if not data:
            return {
                "answer": "No EV data found for this query.",
                "chart": None,
                "data": []
            }

        answer = generate_human_answer(question, data)

        chart = None
        if len(data) > 1 and "state" in data[0]:
            chart = {
                "type": "bar",
                "labels": [d["state"] for d in data[:10]],
                "values": [
                    float(d.get("total_registrations") or d.get("estimated_ev_registrations", 0))
                    for d in data[:10]
                ]
            }

        return {
            "answer": answer,
            "chart": chart,
            "data": data[:20]
        }

    except Exception:

        conversation_manager.register_general_response()

        if conversation_manager.should_suggest_help():
            suggestions = conversation_manager.generate_help_only()
            conversation_manager.reset_counter()

            return {
                "answer": (
                    "I couldn't process that EV query right now.\n\n"
                    "Tip: You can type 'help' to see example prompts.\n\n"
                    f"{suggestions}"
                ),
                "chart": None,
                "data": []
            }

        return {
            "answer": "I couldn't process that EV query right now.",
            "chart": None,
            "data": []
        }