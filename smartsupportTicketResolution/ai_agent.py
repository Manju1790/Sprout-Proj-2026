import json
import os
import re

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
API_KEY = os.getenv("OPENROUTER_API_KEY")


def fallback_analysis(subject, description):
    text = f"{subject} {description}".lower()

    if any(word in text for word in [
        "payment", "refund", "charged", "transaction", "billing", "invoice"
    ]):
        category = "Payment"
        team = "Billing"
    elif any(word in text for word in [
        "password", "login", "sign in", "account", "otp", "authentication"
    ]):
        category = "Account"
        team = "Account Support"
    elif any(word in text for word in [
        "bug", "error", "crash", "exception", "not working", "failed"
    ]):
        category = "Technical"
        team = "Technical Support"
    elif any(word in text for word in [
        "delivery", "shipping", "order", "package", "courier"
    ]):
        category = "Delivery"
        team = "Operations"
    else:
        category = "General"
        team = "Customer Support"

    if any(word in text for word in [
        "fraud", "hacked", "money deducted", "urgent", "security"
    ]):
        priority = "Urgent"
    elif any(word in text for word in [
        "failed", "not working", "blocked", "cannot", "unable"
    ]):
        priority = "High"
    elif any(word in text for word in [
        "issue", "problem", "delay"
    ]):
        priority = "Medium"
    else:
        priority = "Low"

    sentiment = "Negative" if any(word in text for word in [
        "angry", "frustrated", "terrible", "worst", "upset", "failed",
        "not working", "problem", "issue"
    ]) else "Neutral"

    resolutions = {
        "Payment": "Verify the transaction ID and payment status. If the payment was captured but the order failed, follow the refund workflow.",
        "Account": "Verify the user's account and authentication details, then guide the customer through the account recovery process.",
        "Technical": "Collect error details, reproduce the issue, check recent service changes, and provide the relevant troubleshooting steps.",
        "Delivery": "Verify the order and delivery status, check the latest logistics update, and provide the customer with the next expected action.",
        "General": "Review the request, clarify missing information, and route the issue to the appropriate support team."
    }

    return {
        "category": category,
        "priority": priority,
        "sentiment": sentiment,
        "team": team,
        "suggested_resolution": resolutions[category]
    }


def _extract_json(text):
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("AI response did not contain JSON")

    return json.loads(match.group(0))


def ai_analysis(subject, description):
    if not API_KEY:
        return fallback_analysis(subject, description)

    llm = ChatOpenAI(
        model=MODEL,
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.1,
    )

    prompt = f"""
You are a customer support triage AI.

Analyze this ticket:

Subject:
{subject}

Description:
{description}

Return ONLY valid JSON with exactly these keys:
category
priority
sentiment
team
suggested_resolution

Allowed category values:
Payment, Account, Technical, Delivery, General

Allowed priority values:
Urgent, High, Medium, Low

Allowed sentiment values:
Positive, Neutral, Negative

Suggested team should be one of:
Billing, Account Support, Technical Support, Operations, Customer Support

The suggested_resolution should be concise and actionable.
"""

    try:
        response = llm.invoke(prompt)
        result = _extract_json(response.content)

        required = [
            "category",
            "priority",
            "sentiment",
            "team",
            "suggested_resolution",
        ]

        if not all(key in result for key in required):
            raise ValueError("Missing AI response fields")

        return result

    except Exception:
        # The application should still work if the model/API is unavailable.
        return fallback_analysis(subject, description)
