"""OpenRouter LLM client (OpenAI models via LangChain)."""

from __future__ import annotations

from config.settings import AppSettings

# Forced for all agent summaries / chat — product is INR-first.
INR_CURRENCY_RULE = (
    "CURRENCY RULE (mandatory): All money amounts are in Indian Rupees (INR). "
    "Always write amounts with ₹ (e.g. ₹1,52,935). "
    "Never use $, USD, dollars, or any other currency symbol or name. "
    "If source numbers have no symbol, still format them as ₹INR."
)


def get_llm(settings: AppSettings):
    if not settings.openrouter_configured:
        return None

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=0.2,
    )


def _with_currency_rule(system: str) -> str:
    if "CURRENCY RULE" in system:
        return system
    return f"{system.strip()}\n\n{INR_CURRENCY_RULE}"


def _with_currency_data_note(user: str) -> str:
    note = "Data note: every numeric spend/budget/cost/value field below is in INR (₹)."
    if note in user:
        return user
    return f"{user.strip()}\n\n{note}"


def invoke_summary(settings: AppSettings, system: str, user: str) -> str:
    llm = get_llm(settings)
    if llm is None:
        return "AI summary unavailable — add OPENROUTER_API_KEY to `.env`."

    from langchain_core.messages import HumanMessage, SystemMessage

    try:
        response = llm.invoke(
            [
                SystemMessage(content=_with_currency_rule(system)),
                HumanMessage(content=_with_currency_data_note(user)),
            ]
        )
        return str(response.content).strip()
    except Exception as exc:
        return f"AI summary failed: {exc}"
