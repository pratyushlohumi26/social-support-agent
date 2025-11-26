"""
UAE Social Support AI System - Enhanced Streamlit UI
"""
import asyncio
import logging
import os
import streamlit as st
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
import re
from dotenv import load_dotenv 

try:
    from ..llm.ollama_client import llm_client  # type: ignore
except Exception:  # pragma: no cover - fallback for direct execution
    try:
        from llm.ollama_client import llm_client  # type: ignore
    except Exception:  # pragma: no cover - offline fallback
        llm_client = None
load_dotenv()

API_PORT = os.getenv("API_PORT", 8005)
API_HOST = os.getenv("API_HOST", "0.0.0.0")

logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="UAE Social Support AI",
    page_icon="🇦🇪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
def api_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None):
    """Make API request"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            try:
                error_payload = response.json()
            except ValueError:
                error_payload = {"detail": response.text}

            message = (
                error_payload.get("message")
                or error_payload.get("detail")
                or response.reason
                or "Unexpected error"
            )
            st.error(f"API Error {response.status_code}: {message}")

            errors = error_payload.get("errors") if isinstance(error_payload, dict) else None
            if errors:
                for error in errors:
                    field = error.get("field", "field")
                    msg = error.get("message", "Invalid value")
                    st.warning(f"{field}: {msg}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None


EMIRATE_OPTIONS = [
    {"label": "Abu Dhabi", "value": "abu_dhabi"},
    {"label": "Dubai", "value": "dubai"},
    {"label": "Sharjah", "value": "sharjah"},
    {"label": "Ajman", "value": "ajman"},
    {"label": "Fujairah", "value": "fujairah"},
    {"label": "Ras Al Khaimah", "value": "ras_al_khaimah"},
    {"label": "Umm Al Quwain", "value": "umm_al_quwain"},
]

RESIDENCY_STATUS_OPTIONS = [
    {"label": "Citizen", "value": "citizen"},
    {"label": "Resident", "value": "resident"},
    {"label": "Visit Visa", "value": "visit_visa"},
]

MARITAL_STATUS_OPTIONS = [
    {"label": "Single", "value": "single"},
    {"label": "Married", "value": "married"},
    {"label": "Divorced", "value": "divorced"},
    {"label": "Widowed", "value": "widowed"},
]

EMPLOYMENT_STATUS_OPTIONS = [
    {"label": "Employed", "value": "employed"},
    {"label": "Self-Employed", "value": "self_employed"},
    {"label": "Unemployed", "value": "unemployed"},
    {"label": "Retired", "value": "retired"},
    {"label": "Student", "value": "student"},
]

SUPPORT_TYPE_OPTIONS = [
    {"label": "Financial Assistance", "value": "financial_assistance"},
    {"label": "Economic Enablement", "value": "economic_enablement"},
    {"label": "Both", "value": "both"},
    {"label": "Emergency Support", "value": "emergency_support"},
]

URGENCY_OPTIONS = [
    {"label": "Low", "value": "low"},
    {"label": "Medium", "value": "medium"},
    {"label": "High", "value": "high"},
    {"label": "Critical", "value": "critical"},
]

SKIP_TOKENS = {"skip", "none", "na", "n/a", "not applicable"}

SECTION_TITLES = {
    "personal_info": "Personal Information",
    "employment_info": "Employment Information",
    "support_request": "Support Request",
}

APPLICATION_CHAT_FIELDS = [
    {
        "section": "personal_info",
        "key": "full_name",
        "label": "Full Name",
        "prompt": "Let's begin with the applicant's full name.",
        "type": "text",
        "min_length": 3,
        "ack": "Thanks, {value}.",
        "summary_transform": "title",
        "llm_value_type": "person_name",
    },
    {
        "section": "personal_info",
        "key": "emirates_id",
        "label": "Emirates ID",
        "prompt": "Please provide the Emirates ID (format 784-XXXX-XXXXXXX-X).",
        "type": "emirates_id",
        "ack": "Emirates ID recorded.",
    },
    {
        "section": "personal_info",
        "key": "mobile_number",
        "label": "Mobile Number",
        "prompt": "What's the applicant's mobile number? Include the country code if you can.",
        "type": "phone",
        "ack": "Mobile number noted.",
    },
    {
        "section": "personal_info",
        "key": "email",
        "label": "Email",
        "prompt": "Would you like to add an email address? Share it now or type 'skip'.",
        "type": "email",
        "optional": True,
        "ack": "Great, I'll use {value} as the contact email.",
        "ack_skip": "No problem, we'll proceed without an email.",
    },
    {
        "section": "personal_info",
        "key": "nationality",
        "label": "Nationality",
        "prompt": "What is the applicant's nationality?",
        "type": "text",
        "min_length": 3,
        "normalize": "lower",
        "summary_transform": "title",
        "ack": "Nationality recorded.",
        "llm_value_type": "nationality",
    },
    {
        "section": "personal_info",
        "key": "residency_status",
        "label": "Residency Status",
        "prompt": "What is the residency status? Choose from: Citizen, Resident, or Visit Visa.",
        "type": "choice",
        "choices": RESIDENCY_STATUS_OPTIONS,
        "ack": "Residency status recorded as {value}.",
    },
    {
        "section": "personal_info",
        "key": "emirate",
        "label": "Emirate",
        "prompt": "Which emirate does the applicant live in? (Abu Dhabi, Dubai, Sharjah, Ajman, Fujairah, Ras Al Khaimah, or Umm Al Quwain)",
        "type": "choice",
        "choices": EMIRATE_OPTIONS,
        "ack": "Residence emirate noted: {value}.",
    },
    {
        "section": "personal_info",
        "key": "marital_status",
        "label": "Marital Status",
        "prompt": "What is the applicant's marital status? (Single, Married, Divorced, Widowed)",
        "type": "choice",
        "choices": MARITAL_STATUS_OPTIONS,
        "ack": "Marital status recorded as {value}.",
    },
    {
        "section": "personal_info",
        "key": "family_size",
        "label": "Family Size",
        "prompt": "How many people are in the household in total?",
        "type": "int",
        "min": 1,
        "max": 20,
        "ack": "Got it, family size is {value}.",
    },
    {
        "section": "personal_info",
        "key": "dependents",
        "label": "Dependents",
        "prompt": "How many dependents rely on the applicant financially?",
        "type": "int",
        "min": 0,
        "max": 15,
        "ack": "Dependents recorded: {value}.",
    },
    {
        "section": "employment_info",
        "key": "employment_status",
        "label": "Employment Status",
        "prompt": "What is the current employment status? (Employed, Self-Employed, Unemployed, Retired, Student)",
        "type": "choice",
        "choices": EMPLOYMENT_STATUS_OPTIONS,
        "ack": "Employment status noted as {value}.",
    },
    {
        "section": "employment_info",
        "key": "employer_name",
        "label": "Employer Name",
        "prompt": "Who is the current employer? Type the name or 'skip'.",
        "type": "text",
        "optional": True,
        "ack": "Employer recorded as {value}.",
        "ack_skip": "All right, we'll leave the employer name blank.",
        "llm_value_type": "organization",
    },
    {
        "section": "employment_info",
        "key": "job_title",
        "label": "Job Title",
        "prompt": "What is the current job title? You can also type 'skip'.",
        "type": "text",
        "optional": True,
        "ack": "Job title captured as {value}.",
        "ack_skip": "Understood, we'll skip the job title.",
        "llm_value_type": "job_title",
    },
    {
        "section": "employment_info",
        "key": "monthly_salary",
        "label": "Monthly Salary",
        "prompt": "What is the monthly salary in AED?",
        "type": "float",
        "min": 0.0,
        "format": "currency",
        "currency": "AED",
        "decimals": 0,
        "ack": "Monthly salary noted: {value}.",
    },
    {
        "section": "employment_info",
        "key": "years_of_experience",
        "label": "Years of Experience",
        "prompt": "How many years of experience does the applicant have? You can also type 'skip'.",
        "type": "int",
        "min": 0,
        "max": 50,
        "optional": True,
        "format": "years",
        "ack": "Experience recorded: {value}.",
        "ack_skip": "No worries, we'll omit years of experience.",
    },
    {
        "section": "support_request",
        "key": "support_type",
        "label": "Support Type",
        "prompt": "Which type of support is needed? (Financial Assistance, Economic Enablement, Both, Emergency Support)",
        "type": "choice",
        "choices": SUPPORT_TYPE_OPTIONS,
        "ack": "Support type recorded as {value}.",
    },
    {
        "section": "support_request",
        "key": "amount_requested",
        "label": "Amount Requested",
        "prompt": "If there's a specific amount requested (in AED), share it or type 'skip'.",
        "type": "float",
        "min": 0.0,
        "max": 100000.0,
        "optional": True,
        "format": "currency",
        "currency": "AED",
        "decimals": 0,
        "ack": "Requested amount noted: {value}.",
        "ack_skip": "Okay, we'll proceed without a specific amount.",
    },
    {
        "section": "support_request",
        "key": "urgency_level",
        "label": "Urgency Level",
        "prompt": "How urgent is the request? (Low, Medium, High, Critical)",
        "type": "choice",
        "choices": URGENCY_OPTIONS,
        "ack": "Urgency level captured as {value}.",
    },
    {
        "section": "support_request",
        "key": "reason_for_support",
        "label": "Reason for Support",
        "prompt": "Please describe why support is needed (a few sentences are perfect).",
        "type": "text_long",
        "min_length": 10,
        "ack": "Thank you for explaining the situation.",
    },
    {
        "section": "support_request",
        "key": "career_goals",
        "label": "Career Goals",
        "prompt": "If there are specific career goals or training interests, share them now or type 'skip'.",
        "type": "text_long",
        "optional": True,
        "ack": "Career goals captured.",
        "ack_skip": "That's fine, we can leave out career goals.",
    },
]


LLM_TEXT_VALUE_GUIDANCE = {
    "default": {
        "instruction": (
            "Extract the specific value that should populate the named form field. "
            "Remove conversational phrases, politeness, or explanations."
        ),
    },
    "person_name": {
        "instruction": (
            "Extract only the individual's full name from the response. "
            "Remove phrases such as 'my name is' or 'I am'. Return the name in title case."
        ),
        "postprocess": "title",
    },
    "nationality": {
        "instruction": (
            "Identify the nationality or country of origin mentioned. "
            "Return only the demonym or country name without extra words."
        ),
        "postprocess": "title",
    },
    "organization": {
        "instruction": (
            "Extract the employer or organisation name referred to in the response. "
            "Exclude leading phrases."
        ),
        "postprocess": "title",
    },
    "job_title": {
        "instruction": (
            "Extract the professional job title described by the user. "
            "Return a concise job title in title case."
        ),
        "postprocess": "title",
    },
}


def llm_available() -> bool:
    return bool(llm_client and getattr(llm_client, "available", False))


def run_async_task(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            raise
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result()
        return loop.run_until_complete(coro)


def resolve_choice_with_llm(field: Dict[str, Any], user_input: str) -> Optional[Dict[str, str]]:
    if not llm_available():
        return None

    choices = field.get("choices", [])
    if not choices:
        return None

    options_description = "\n".join(
        f"- {option['label']} (value: {option['value']})"
        for option in choices
    )

    prompt = (
        "You help map applicant responses to official form options. "
        "Select the option that best matches the user's reply."
        f"\n\nAvailable options:\n{options_description}\n\n"
        f"User reply: " + json.dumps(user_input) + "\n\n"
        "Respond in JSON using the schema {\"value\": string}. "
        "Return the option's exact value from the list. "
        "If nothing matches, respond with {\"value\": \"unknown\"}."
    )

    async def _call_llm():
        expected = {"value": "string"}
        return await llm_client.generate_structured_response(
            prompt,
            "You are an assistant that chooses the best matching option for an intake form.",
            expected,
        )

    try:
        result = run_async_task(_call_llm())
    except Exception as exc:  # noqa: BLE001
        logger.debug("LLM choice resolution failed: %s", exc)
        return None

    if not isinstance(result, dict):
        return None

    value = str(result.get("value", "")).strip().lower()
    if not value or value == "unknown":
        return None

    for option in choices:
        if option["value"].lower() == value or option["label"].lower() == value:
            return option

    return None


def extract_name_heuristic(user_input: str) -> Optional[str]:
    patterns = [
        r"(?:my full name is\s+)([a-zA-Z'’\- ]{2,})",
        r"(?:my name is\s+)([a-zA-Z'’\- ]{2,})",
        r"(?:i am\s+)([a-zA-Z'’\- ]{2,})",
        r"(?:this is\s+)([a-zA-Z'’\- ]{2,})",
        r"(?:name[:\-]\s*)([a-zA-Z'’\- ]{2,})",
    ]
    lowered = user_input.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            extracted = match.group(1).strip()
            # Align with original casing where possible
            start = lowered.find(extracted)
            if start != -1:
                return user_input[start : start + len(extracted)].strip()
            return extracted
    return None


def refine_name_with_llm(user_input: str) -> Optional[str]:
    if not llm_available():
        return None

    prompt = (
        "Extract only the applicant's full name from the response below. "
        "Return the cleaned name in title case without surrounding text or punctuation. "
        "Response: " + json.dumps(user_input)
    )

    async def _call_llm():
        expected = {"full_name": "string"}
        return await llm_client.generate_structured_response(
            prompt,
            "You extract personal names for UAE support applications and respond in JSON.",
            expected,
        )

    try:
        result = run_async_task(_call_llm())
    except Exception as exc:  # noqa: BLE001
        logger.debug("LLM name extraction failed: %s", exc)
        return None

    if isinstance(result, dict):
        name_value = result.get("full_name")
        if isinstance(name_value, str) and name_value.strip():
            return name_value.strip()
    return None


def llm_extract_text_value(field: Dict[str, Any], user_input: str) -> Optional[str]:
    if not llm_available():
        return None

    value_type = field.get("llm_value_type") or "default"
    guidance = LLM_TEXT_VALUE_GUIDANCE.get(value_type, LLM_TEXT_VALUE_GUIDANCE["default"])
    instruction = guidance.get("instruction", "")

    label = field.get("label") or field.get("key", "field")
    field_type = field.get("type", "text")

    prompt = (
        "You extract concise values for a structured UAE social support intake form. "
        "Return only the value that should be saved for the field.\n\n"
        f"Field label: {label}\n"
        f"Expected field type: {field_type}\n"
        f"Guidance: {instruction}\n\n"
        f"User response: {json.dumps(user_input)}\n\n"
        "Respond in JSON with the schema {\"value\": string}. "
        "If the response does not contain the required information, return {\"value\": \"unknown\"}."
    )

    async def _call_llm():
        expected = {"value": "string"}
        return await llm_client.generate_structured_response(
            prompt,
            "You transform free-form chat answers into clean field values for UAE intake forms.",
            expected,
        )

    try:
        result = run_async_task(_call_llm())
    except Exception as exc:  # noqa: BLE001
        logger.debug("LLM text extraction failed: %s", exc)
        return None

    if not isinstance(result, dict):
        return None

    value = result.get("value")
    if not isinstance(value, str):
        return None

    cleaned_value = value.strip().strip("\n\r .,;:")
    if not cleaned_value or cleaned_value.lower() == "unknown":
        return None

    postprocess = guidance.get("postprocess")
    if postprocess == "title":
        cleaned_value = cleaned_value.title()
    elif postprocess == "upper":
        cleaned_value = cleaned_value.upper()

    return cleaned_value


def reset_intake_state() -> None:
    intro = (
        "Hello! I'm your intake assistant. I'll ask a few questions to build the application. "
        "You can type 'skip' to bypass optional questions or 'restart' at any time to begin again."
    )
    first_prompt = get_field_prompt(APPLICATION_CHAT_FIELDS[0])
    st.session_state.intake_state = {
        "messages": [
            {"role": "assistant", "content": intro},
            {"role": "assistant", "content": first_prompt},
        ],
        "current_step": 0,
        "collected": {
            "personal_info": {},
            "employment_info": {},
            "support_request": {},
        },
        "complete": False,
        "submitted": False,
        "submission_result": None,
    }


def get_field_prompt(field: Dict[str, Any]) -> str:
    prompt = field.get("prompt", "")
    if field.get("type") == "choice":
        options = ", ".join(option["label"] for option in field.get("choices", []))
        prompt = f"{prompt}\nOptions: {options}"
    return prompt


def format_field_value(field: Dict[str, Any], value: Any, for_ack: bool = False) -> str:
    if value is None:
        return "" if for_ack else "Pending"

    field_type = field.get("type")

    if field_type == "choice":
        for option in field.get("choices", []):
            if option["value"] == value:
                return option["label"]

    if field_type in {"float", "int"} and field.get("format") == "currency":
        decimals = field.get("decimals", 0)
        formatter = f"{{:,.{decimals}f}}"
        formatted = formatter.format(float(value))
        currency = field.get("currency", "AED")
        return f"{formatted} {currency}"

    if field_type == "int" and field.get("format") == "years":
        suffix = "year" if int(value) == 1 else "years"
        return f"{int(value)} {suffix}"

    summary_transform = field.get("summary_transform")
    if summary_transform == "title":
        return str(value).title()
    if summary_transform == "upper":
        return str(value).upper()

    return str(value)


def parse_field_response(field: Dict[str, Any], message: str, collected: Dict[str, Dict[str, Any]]) -> tuple[bool, Any, Optional[str], Optional[str]]:
    text = message.strip()
    if not text:
        return False, None, "I didn't catch that. Could you share it again?", None

    lowered = text.lower()
    if field.get("optional") and lowered in SKIP_TOKENS:
        return True, None, None, None

    field_type = field.get("type", "text")

    try:
        if field_type in {"text", "text_long"}:
            min_length = field.get("min_length", 1)
            if len(text) < min_length:
                return False, None, f"Please provide at least {min_length} characters.", None

            cleaned = text.strip()
            display_value = cleaned

            llm_value = None
            if field_type == "text":
                llm_value = llm_extract_text_value(field, text)
                if llm_value and llm_value.strip().lower() == text.strip().lower():
                    llm_value = None
            if llm_value:
                cleaned = llm_value.strip()
                display_value = cleaned

            if field.get("key") == "full_name" and not llm_value:
                candidate = extract_name_heuristic(text)
                if not candidate:
                    candidate = refine_name_with_llm(text)
                if candidate:
                    cleaned = candidate.strip()
                    display_value = cleaned
                else:
                    lowered_name = cleaned.lower()
                    for prefix in ["my full name is", "my name is", "i am", "this is", "name is"]:
                        if lowered_name.startswith(prefix):
                            cleaned = cleaned[len(prefix) :].strip()
                            display_value = cleaned
                            break

            normalize = field.get("normalize")
            if normalize == "lower":
                cleaned = cleaned.lower()
            elif normalize == "slug":
                cleaned = cleaned.lower().replace(" ", "_")

            if field.get("key") == "full_name":
                cleaned = cleaned.strip()
                display_value = cleaned.title()
                cleaned = display_value

            if not display_value:
                display_value = cleaned
            return True, cleaned, None, display_value

        if field_type == "choice":
            for option in field.get("choices", []):
                label = option["label"].lower()
                value = option["value"].lower()
                simplified_label = label.replace(" ", "")
                simplified_value = value.replace("_", "")
                if lowered in {label, value, simplified_label, simplified_value}:
                    cleaned_value = option["value"]
                    display_value = option["label"]
                    return True, cleaned_value, None, display_value
            resolved_option = resolve_choice_with_llm(field, text)
            if resolved_option:
                cleaned_value = resolved_option["value"]
                display_value = resolved_option["label"]
                return True, cleaned_value, None, display_value
            options_text = ", ".join(opt["label"] for opt in field.get("choices", []))
            return False, None, f"Please choose one of the available options: {options_text}.", None

        if field_type == "emirates_id":
            digits = re.sub(r"\D", "", text)
            if len(digits) != 15 or not digits.startswith("784"):
                return False, None, "Please provide a valid Emirates ID in the format 784-XXXX-XXXXXXX-X.", None
            formatted = f"{digits[0:3]}-{digits[3:7]}-{digits[7:14]}-{digits[14]}"
            return True, formatted, None, formatted

        if field_type == "phone":
            digits = re.sub(r"\D", "", text)
            if digits.startswith("971") and len(digits) == 12:
                formatted = f"+{digits}"
            elif len(digits) == 9:
                formatted = f"+971{digits}"
            elif len(digits) == 10 and digits.startswith("05"):
                formatted = f"+971{digits[1:]}"
            else:
                return False, None, "Please enter a UAE mobile number such as +971501234567.", None
            return True, formatted, None, formatted

        if field_type == "email":
            pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            if re.match(pattern, text):
                cleaned = text.strip().lower()
                return True, cleaned, None, cleaned
            return False, None, "That doesn't look like a valid email. Please try again or type 'skip'.", None

        if field_type == "int":
            numeric = text.replace(",", "")
            value = int(numeric)
            min_value = field.get("min")
            max_value = field.get("max")
            if min_value is not None and value < min_value:
                return False, None, f"Please provide a number greater than or equal to {min_value}.", None
            if max_value is not None and value > max_value:
                return False, None, f"Please provide a number less than or equal to {max_value}.", None
            display_value = format_field_value(field, value, for_ack=True)
            return True, value, None, display_value

        if field_type == "float":
            cleaned_text = re.sub(r"[^0-9.,]", "", text)
            cleaned_text = cleaned_text.replace(",", "")
            if cleaned_text in {"", "."}:
                raise ValueError
            value = float(cleaned_text)
            min_value = field.get("min")
            max_value = field.get("max")
            if min_value is not None and value < min_value:
                return False, None, f"Please provide a number greater than or equal to {min_value}.", None
            if max_value is not None and value > max_value:
                return False, None, f"Please provide a number less than or equal to {int(max_value)}.", None
            display_value = format_field_value(field, value, for_ack=True)
            return True, value, None, display_value

    except ValueError:
        if field_type in {"int", "float"}:
            return False, None, "Please share the number using digits only.", None
        return False, None, "I couldn't understand that input. Could you rephrase it?", None

    return False, None, "I'm not sure how to record that. Could you try again?", None


def store_collected_value(collected: Dict[str, Dict[str, Any]], field: Dict[str, Any], value: Any) -> None:
    section = field["section"]
    key = field["key"]
    if value is None:
        collected[section].pop(key, None)
    else:
        collected[section][key] = value


def build_application_payload(collected: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    payload = {}
    for section, data in collected.items():
        payload[section] = {key: value for key, value in data.items() if value not in (None, "")}
    return payload


def get_summary_entries(collected: Dict[str, Dict[str, Any]]) -> Dict[str, list[Dict[str, Any]]]:
    summary: Dict[str, list[Dict[str, Any]]] = {title: [] for title in SECTION_TITLES.values()}
    for field in APPLICATION_CHAT_FIELDS:
        section_title = SECTION_TITLES[field["section"]]
        value = collected[field["section"]].get(field["key"])
        display = format_field_value(field, value)
        summary[section_title].append(
            {
                "label": f"{field['label']}{' (optional)' if field.get('optional') else ''}",
                "value": display,
                "provided": value not in (None, ""),
                "optional": field.get("optional", False),
                "field": field,
            }
        )
    return summary


def _render_section_details(section: str, section_data: Dict[str, Any]) -> list[tuple[str, str]]:
    details: list[tuple[str, str]] = []
    for field in APPLICATION_CHAT_FIELDS:
        if field["section"] != section:
            continue
        key = field["key"]
        if key not in section_data:
            continue
        display_value = format_field_value(field, section_data[key])
        details.append((field["label"], display_value))
    return details

def main():
    """Main application"""

    # Header
    st.title("🇦🇪 UAE Social Support AI System")
    st.markdown("*Advanced Multimodal AI for Social & Economic Support Assessment*")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        [
            "🏠 Dashboard",
            "📄 New Application",
            "📜 Application Status",
            "💬 Chat Assistant",
            "📊 Analytics",
            "🔧 System Status",
        ],
    )

    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📄 New Application":
        show_application_form()
    elif page == "📜 Application Status":
        show_application_status()
    elif page == "💬 Chat Assistant":
        show_chat_interface()
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "🔧 System Status":
        show_system_status()

def show_dashboard():
    """Dashboard page"""
    st.header("Dashboard Overview")

    # Get system stats
    stats = api_request("/stats")

    if stats:
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Applications", stats.get("total_applications", 0))
        with col2:
            st.metric("Active Agents", stats.get("active_agents", 4))
        with col3:
            st.metric("Success Rate", stats.get("success_rate", "95%"))
        with col4:
            st.metric("Avg Processing Time", stats.get("processing_average_time", "15s"))

    # Recent activity
    st.subheader("Recent Activity")

    # Mock recent applications
    recent_apps = [
        {"ID": "UAE-2024-001", "Applicant": "Ahmed Al Mansouri", "Status": "Approved", "Amount": "15,000 AED"},
        {"ID": "UAE-2024-002", "Applicant": "Fatima Al Zahra", "Status": "Under Review", "Amount": "8,000 AED"},
        {"ID": "UAE-2024-003", "Applicant": "Mohammed Al Rashid", "Status": "Documents Required", "Amount": "12,000 AED"}
    ]

    df = pd.DataFrame(recent_apps)
    st.dataframe(df, use_container_width=True)

def fetch_applications(limit: int = 50, offset: int = 0) -> Optional[Dict[str, Any]]:
    """Helper to load paginated applications from the API."""

    query = f"/applications?limit={limit}&offset={offset}"
    return api_request(query)


def show_application_form():
    """Chat-based application intake"""
    st.header("🤖 Chat-Driven Application Intake")
    st.markdown(
        "Talk with the intake assistant to submit a new application. "
        "Type **skip** for optional questions or **restart** to begin again."
    )

    if "intake_state" not in st.session_state:
        reset_intake_state()

    intake_state = st.session_state.intake_state
    total_steps = len(APPLICATION_CHAT_FIELDS)
    completed_steps = intake_state["current_step"] if not intake_state.get("complete") else total_steps

    chat_column, summary_column = st.columns([2, 1])

    with chat_column:
        st.subheader("Assistant Conversation")
        if st.button("🔄 Restart conversation", key="restart_intake"):
            reset_intake_state()
            st.experimental_rerun()

        chat_container = st.container()
        with chat_container:
            for message in intake_state["messages"]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if intake_state.get("complete"):
            st.markdown("_Conversation complete. Review the summary to submit or restart above._")

    with summary_column:
        st.subheader("Application Snapshot")
        progress_fraction = completed_steps / total_steps if total_steps else 0
        st.progress(progress_fraction)
        st.caption(f"Answered {completed_steps} of {total_steps} questions")

        summary_entries = get_summary_entries(intake_state["collected"])
        for section_title, entries in summary_entries.items():
            st.markdown(f"**{section_title}**")
            for entry in entries:
                if entry["provided"]:
                    display_text = entry["value"]
                else:
                    display_text = "Optional" if entry["optional"] else "Awaiting input"
                st.write(f"- {entry['label']}: {display_text}")

        if intake_state.get("complete"):
            payload = build_application_payload(intake_state["collected"])
            st.markdown("**Ready to Submit**")

            for section, title in SECTION_TITLES.items():
                section_data = payload.get(section, {})
                if not section_data:
                    continue

                with st.container():
                    st.markdown(f"### {title}")
                    for display_label, display_value in _render_section_details(section, section_data):
                        st.markdown(f"**{display_label}:** {display_value}")
                st.markdown("---")

            submit_disabled = intake_state.get("submitted", False)
            if st.button("📤 Submit application", key="submit_application_button", disabled=submit_disabled):
                with st.spinner("Submitting application..."):
                    response = api_request("/applications/submit", method="POST", data=payload)

                if response and response.get("success"):
                    intake_state["submitted"] = True
                    intake_state["submission_result"] = response
                    ref_id = response.get("application_id", "")
                    confirmation = "Your application has been submitted successfully."
                    if ref_id:
                        confirmation = f"Your application has been submitted successfully. Reference ID: {ref_id}."
                    intake_state["messages"].append({"role": "assistant", "content": confirmation})
                    st.success("🎉 Application submitted successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Submission failed. Please review the details and try again.")

    user_reply: Optional[str] = None
    if intake_state.get("complete"):
        st.chat_input(
            "Conversation complete – use the restart button above to begin again.",
            key="intake_disabled",
            disabled=True,
        )
    else:
        user_reply = st.chat_input("Your response")

    if user_reply:
        normalized = user_reply.strip().lower()
        if normalized in {"restart", "start over", "reset"}:
            reset_intake_state()
            st.experimental_rerun()

        intake_state["messages"].append({"role": "user", "content": user_reply})
        current_field = APPLICATION_CHAT_FIELDS[intake_state["current_step"]]
        success, cleaned_value, error_message, display_value = parse_field_response(
            current_field, user_reply, intake_state["collected"]
        )

        if success and current_field["section"] == "personal_info" and current_field["key"] == "dependents":
            family_size = intake_state["collected"]["personal_info"].get("family_size")
            if family_size is not None and cleaned_value is not None and cleaned_value >= family_size:
                success = False
                error_message = (
                    "Dependents should be less than the total household size. Could you confirm the number again?"
                )

        if success:
            store_collected_value(intake_state["collected"], current_field, cleaned_value)

            ack_template = None
            if cleaned_value is None:
                ack_template = current_field.get("ack_skip")
            if not ack_template:
                ack_template = current_field.get("ack", "Noted.")

            value_token = display_value
            if not value_token and cleaned_value not in (None, ""):
                value_token = str(cleaned_value)
            if not value_token:
                value_token = user_reply

            ack_message = ack_template.format(value=value_token)

            intake_state["current_step"] += 1
            if intake_state["current_step"] < total_steps:
                next_field = APPLICATION_CHAT_FIELDS[intake_state["current_step"]]
                assistant_message = f"{ack_message}\n\n{get_field_prompt(next_field)}"
                intake_state["messages"].append({"role": "assistant", "content": assistant_message})
            else:
                intake_state["complete"] = True
                completion_message = (
                    f"{ack_message}\n\nThat's everything I need. Review the summary on the right and submit when you're ready."
                )
                intake_state["messages"].append({"role": "assistant", "content": completion_message})
            st.experimental_rerun()
        else:
            remediate = error_message or "I couldn't understand that. Could you try again?"
            intake_state["messages"].append({"role": "assistant", "content": remediate})
            st.experimental_rerun()

    submission_result = intake_state.get("submission_result")
    if submission_result:
        processing_result = submission_result.get("processing_result", {})
        final_decision = processing_result.get("final_decision", {})
        if final_decision:
            st.subheader("📋 Processing Results")
            status = final_decision.get("status", "unknown")

            if status == "approved":
                st.success("✅ Application Approved")
                financial_support = final_decision.get("financial_support", {})
                approved_amount = financial_support.get("approved_amount", 0)
                if approved_amount:
                    st.info(f"💰 Approved Amount: {approved_amount:,.0f} AED")
                    st.info(f"⏱️ Duration: {financial_support.get('duration_months', 0)} months")
            elif status == "conditional_approval":
                st.warning("⚠️ Conditional approval – additional requirements apply.")
            elif status == "review_required":
                st.info("🔄 Application requires manual review.")
            else:
                st.error("❌ Application needs additional information.")

            enablement = final_decision.get("economic_enablement", {})
            training_programs = enablement.get("training_programs")
            if training_programs:
                st.subheader("🎓 Recommended Training Programs")
                for program in training_programs:
                    st.write(f"- {program.get('name', 'Training Program')}")

            next_steps = final_decision.get("next_steps", [])
            if next_steps:
                st.subheader("📝 Next Steps")
                for step in next_steps:
                    st.write(f"• {step}")

def show_chat_interface_old():
    """Chat interface"""
    st.header("💬 Chat Assistant")
    st.markdown("*Get help with your application, documents, or eligibility questions*")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Chat input
    user_input = st.text_input("Ask me anything about UAE social support...", key="chat_input")

    if st.button("Send") and user_input:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "message": user_input})

        # Get AI response
        with st.spinner("Thinking..."):
            response = api_request("/chat", method="POST", data={"message": user_input})

            if response:
                ai_message = response.get("response", "Sorry, I couldn't process your request.")
                st.session_state.chat_history.append({"role": "assistant", "message": ai_message})

                # Show suggested actions
                suggested_actions = response.get("suggested_actions", [])
                if suggested_actions:
                    st.subheader("💡 Suggested Actions")
                    for action in suggested_actions:
                        st.button(action, key=f"action_{action}")

    # Display chat history
    if st.session_state.chat_history:
        st.subheader("Chat History")
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.markdown(f"**You:** {chat['message']}")
            else:
                st.markdown(f"**Assistant:** {chat['message']}")
def show_analytics():
    """Fixed analytics dashboard with proper chart handling"""
    st.header("📊 Analytics Dashboard")
    st.markdown("*System performance and application statistics*")
    
    try:
        # Get system stats from API
        stats = api_request("/stats")
        
        if stats:
            # Display key metrics
            st.subheader("📈 Key Performance Indicators")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Applications", 
                    stats.get("total_applications", 0),
                    help="Total applications processed"
                )
            
            with col2:
                st.metric(
                    "Active Agents", 
                    stats.get("active_agents", 0),
                    help="AI agents currently operational"
                )
            
            with col3:
                st.metric(
                    "Success Rate", 
                    stats.get("success_rate", "0%"),
                    help="Application processing success rate"
                )
            
            with col4:
                st.metric(
                    "Avg Processing Time", 
                    stats.get("processing_average_time", "N/A"),
                    help="Average time to process applications"
                )
        
        # Create two columns for charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Application Status Distribution")
            
            # Mock data for application status
            status_data = {
                "Approved": 45,
                "Under Review": 25, 
                "Conditional": 15,
                "Documents Required": 10,
                "Declined": 5
            }
            
            try:
                # Create bar chart using st.bar_chart
                status_df = pd.DataFrame(
                    list(status_data.items()), 
                    columns=['Status', 'Count']
                ).set_index('Status')
                
                st.bar_chart(status_df)
                
            except Exception as e:
                st.error(f"Error creating status chart: {e}")
                # Fallback: Display as table
                st.table(pd.DataFrame(list(status_data.items()), columns=['Status', 'Applications']))
        
        with col2:
            st.subheader("🏙️ Applications by Emirate")
            
            # Mock data for emirate distribution
            emirate_data = {
                "Dubai": 40,
                "Abu Dhabi": 25,
                "Sharjah": 15,
                "Ajman": 8,
                "Fujairah": 5,
                "Ras Al Khaimah": 4,
                "Umm Al Quwain": 3
            }
            
            try:
                # Create a proper chart using plotly or matplotlib alternative
                # Using st.bar_chart as it's more reliable than st.pie_chart
                emirate_df = pd.DataFrame(
                    list(emirate_data.items()), 
                    columns=['Emirate', 'Applications']
                ).set_index('Emirate')
                
                st.bar_chart(emirate_df)
                
            except Exception as e:
                st.error(f"Error creating emirate chart: {e}")
                # Fallback: Display as table
                st.table(pd.DataFrame(list(emirate_data.items()), columns=['Emirate', 'Applications']))
        
        # Additional analytics sections
        st.subheader("💰 Support Amount Analysis")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("📈 Monthly Trends")
            
            # Mock monthly data
            monthly_data = pd.DataFrame({
                'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'Applications': [120, 135, 145, 160, 180, 195],
                'Approved': [95, 110, 120, 135, 150, 165],
                'Amount (AED)': [1200000, 1350000, 1450000, 1600000, 1800000, 1950000]
            })
            
            try:
                # Display monthly trends
                chart_data = monthly_data.set_index('Month')[['Applications', 'Approved']]
                st.line_chart(chart_data)
                
            except Exception as e:
                st.error(f"Error creating trend chart: {e}")
                st.table(monthly_data)
        
        with col4:
            st.subheader("🎯 Support Categories")
            
            # Mock support category data
            category_data = {
                "Financial Assistance": 60,
                "Career Development": 25,
                "Emergency Support": 10,
                "Special Circumstances": 5
            }
            
            try:
                category_df = pd.DataFrame(
                    list(category_data.items()), 
                    columns=['Category', 'Percentage']
                ).set_index('Category')
                
                st.bar_chart(category_df)
                
            except Exception as e:
                st.error(f"Error creating category chart: {e}")
                st.table(pd.DataFrame(list(category_data.items()), columns=['Category', 'Percentage']))
        
        # System performance metrics
        st.subheader("🔧 System Performance")
        
        # Get debug information
        debug_info = api_request("/debug/system")
        
        if debug_info:
            col5, col6 = st.columns(2)
            
            with col5:
                st.subheader("🤖 AI System Status")
                
                llm_integration = debug_info.get("llm_integration", {})
                agents_status = debug_info.get("agents_status", {})
                
                # Display AI system metrics
                ai_metrics = {
                    "Ollama Cloud": "✅ Connected" if llm_integration.get("ollama_cloud") == "configured" else "❌ Not configured",
                    "LangGraph Workflow": "✅ Operational" if llm_integration.get("langgraph_workflow") == "operational" else "❌ Unavailable",
                    "Processing Mode": llm_integration.get("processing_mode", "unknown").replace("_", " ").title(),
                    "Active Agents": llm_integration.get("agents_count", 0)
                }
                
                for metric, value in ai_metrics.items():
                    st.write(f"**{metric}:** {value}")
            
            with col6:
                st.subheader("⚡ Performance Metrics")
                
                # Mock performance data
                performance_metrics = {
                    "Average Response Time": "2.3 seconds",
                    "API Uptime": "99.8%",
                    "Memory Usage": "450 MB",
                    "CPU Usage": "23%",
                    "Database Queries": "1,247",
                    "Cache Hit Rate": "94.5%"
                }
                
                for metric, value in performance_metrics.items():
                    st.write(f"**{metric}:** {value}")
        
        # Real-time activity log
        st.subheader("📋 Recent Activity")
        
        # Mock recent activity data
        recent_activity = [
            {"Time": "16:45", "Event": "New application submitted", "User": "Ahmed Al-*****", "Status": "Processing"},
            {"Time": "16:42", "Event": "Application approved", "User": "Fatima Al-*****", "Status": "Completed"},
            {"Time": "16:38", "Event": "Document uploaded", "User": "Mohammed *****", "Status": "Under Review"},
            {"Time": "16:35", "Event": "Training enrollment", "User": "Aisha *****", "Status": "Enrolled"},
            {"Time": "16:32", "Event": "Support disbursed", "User": "Omar *****", "Status": "Completed"},
        ]
        
        activity_df = pd.DataFrame(recent_activity)
        st.dataframe(activity_df, use_container_width=True)
        
        # Download analytics report
        st.subheader("📥 Export Analytics")
        
        col7, col8 = st.columns(2)
        
        with col7:
            if st.button("📊 Download Summary Report", use_container_width=True):
                # Create summary report
                summary_report = {
                    "report_date": datetime.now().isoformat(),
                    "total_applications": stats.get("total_applications", 0) if stats else 0,
                    "success_rate": stats.get("success_rate", "0%") if stats else "0%",
                    "status_distribution": status_data,
                    "emirate_distribution": emirate_data,
                    "category_distribution": category_data,
                    "system_status": debug_info.get("system_status", "unknown") if debug_info else "unknown"
                }
                
                import json
                report_json = json.dumps(summary_report, indent=2)
                
                st.download_button(
                    label="📄 Download JSON Report",
                    data=report_json,
                    file_name=f"uae_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col8:
            if st.button("📈 Download Raw Data", use_container_width=True):
                # Create CSV data
                combined_data = pd.DataFrame({
                    'Metric': list(status_data.keys()) + list(emirate_data.keys()),
                    'Value': list(status_data.values()) + list(emirate_data.values()),
                    'Type': ['Status'] * len(status_data) + ['Emirate'] * len(emirate_data)
                })
                
                csv_data = combined_data.to_csv(index=False)
                
                st.download_button(
                    label="📊 Download CSV Data",
                    data=csv_data,
                    file_name=f"uae_analytics_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    except Exception as e:
        st.error(f"❌ Error loading analytics: {e}")
        st.info("🔄 Please refresh the page or contact support if the issue persists.")
        
        # Show basic fallback analytics
        st.subheader("📊 Basic System Information")
        
        basic_info = {
            "System Status": "Operational",
            "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "Version": "3.0.0",
            "Environment": "Production"
        }
        
        for key, value in basic_info.items():
            st.write(f"**{key}:** {value}")

def show_system_status():
    """System status page"""
    st.header("🔧 System Status")

    # Get system debug info
    debug_info = api_request("/debug/system")

    if debug_info:
        st.subheader("🎛️ System Health")

        status = debug_info.get("system_status", "unknown")
        if status == "healthy":
            st.success("✅ System is running normally")
        else:
            st.error("❌ System issues detected")

        st.subheader("🤖 AI Agents Status")
        agents_status = debug_info.get("agents_status", {})

        for agent_name, agent_status in agents_status.items():
            if agent_status == "operational":
                st.success(f"✅ {agent_name.replace('_', ' ').title()}: {agent_status}")
            else:
                st.error(f"❌ {agent_name.replace('_', ' ').title()}: {agent_status}")

        st.subheader("📋 System Information")
        st.json(debug_info)
    else:
        st.error("❌ Unable to connect to system")

def show_chat_interface():
    """Fixed chat interface with proper suggested actions handling"""
    st.header("💬 Chat Assistant")
    st.markdown("*Get help with your application, documents, or eligibility questions*")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Initialize suggested actions
    if "last_suggested_actions" not in st.session_state:
        st.session_state.last_suggested_actions = []
    
    # Initialize pending message (for suggested actions)
    if "pending_message" not in st.session_state:
        st.session_state.pending_message = ""
    
    # Check for suggested action click
    suggested_action_clicked = None
    if st.session_state.last_suggested_actions:
        st.subheader("💡 Suggested Actions")
        st.markdown("*Click any suggestion below:*")
        
        # Create clickable buttons for suggested actions
        cols = st.columns(min(len(st.session_state.last_suggested_actions), 2))  # Max 2 columns
        
        for i, action in enumerate(st.session_state.last_suggested_actions):
            col_index = i % 2
            with cols[col_index]:
                if st.button(
                    action, 
                    key=f"suggest_action_{i}",
                    help="Click to send this question",
                    use_container_width=True
                ):
                    suggested_action_clicked = action
                    st.session_state.pending_message = action
                    break
    
    # Chat input with default value from suggested action
    default_value = st.session_state.pending_message if st.session_state.pending_message else ""
    user_input = st.text_input(
        "Ask me anything about UAE social support...", 
        key="chat_input",
        value=default_value,
        placeholder="Type your question or click a suggested action above..."
    )
    
    # Send button
    send_clicked = st.button("Send", type="primary", disabled=not user_input.strip())
    
    # Process message when send is clicked or suggested action is selected
    if send_clicked and user_input.strip():
        message_to_process = user_input.strip()
        
        # Clear pending message after processing
        st.session_state.pending_message = ""
        
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user", 
            "message": message_to_process,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get AI response
        with st.spinner("Getting response..."):
            response_data = api_request("/chat", method="POST", data={"message": message_to_process})
            
            if response_data and response_data.get("success"):
                ai_message = response_data.get("response", "I couldn't process your request.")
                suggested_actions = response_data.get("suggested_actions", [])
                intent = response_data.get("intent", "general")
                llm_powered = response_data.get("llm_powered", False)
                
                # Add AI response to history
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "message": ai_message,
                    "timestamp": datetime.now().isoformat(),
                    "intent": intent,
                    "llm_powered": llm_powered
                })
                
                # Update suggested actions for next interaction
                st.session_state.last_suggested_actions = suggested_actions
                
                # Show success message
                if llm_powered:
                    st.success("✅ Response generated using AI")
                else:
                    st.info("ℹ️ Response from knowledge base")
                    
            else:
                st.error("❌ Failed to get response. Please try again.")
                
        # Force rerun to clear input and show new messages
        st.rerun()
    
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("💬 Conversation History")
        
        # Show recent messages (last 8 for better performance)
        recent_messages = st.session_state.chat_history[-8:]
        
        for chat in recent_messages:
            if chat["role"] == "user":
                # User message
                with st.container():
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 15px;
                        border-radius: 15px 15px 5px 15px;
                        margin: 10px 0;
                        margin-left: 20%;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    ">
                        <strong>🧑‍💼 You</strong><br>
                        {chat['message']}
                        <br><small style="opacity: 0.8; font-size: 0.8em;">
                            {datetime.fromisoformat(chat['timestamp']).strftime('%I:%M %p')}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # Assistant message
                llm_indicator = "🤖" if chat.get("llm_powered") else "🔧"
                llm_text = "AI Assistant" if chat.get("llm_powered") else "Knowledge Base"
                intent_display = f" • {chat.get('intent', '').replace('_', ' ').title()}" if chat.get('intent') else ""
                
                with st.container():
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        color: white;
                        padding: 15px;
                        border-radius: 15px 15px 15px 5px;
                        margin: 10px 0;
                        margin-right: 20%;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    ">
                        <strong>{llm_indicator} {llm_text}{intent_display}</strong><br>
                        {chat['message'].replace(chr(10), '<br>')}
                        <br><small style="opacity: 0.8; font-size: 0.8em;">
                            {datetime.fromisoformat(chat['timestamp']).strftime('%I:%M %p')}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
    
    else:
        # Welcome message when no chat history
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            margin: 20px 0;
        ">
            <h3>👋 Welcome to UAE Social Support AI Assistant!</h3>
            <p>I'm here to help you with:</p>
            <ul style="text-align: left; display: inline-block;">
                <li>✅ Application eligibility and requirements</li>
                <li>📄 Required documents and preparation</li>
                <li>💰 Support amounts and calculations</li>
                <li>🎓 Training and career programs</li>
                <li>📊 Application status and process</li>
            </ul>
            <p><strong>Ask me anything about UAE social support!</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initial suggested actions
        st.subheader("💡 Popular Questions")
        initial_actions = [
            "Am I eligible for UAE social support?",
            "What documents do I need for my application?",
            "How much financial support can I get?",
            "What training programs are available?"
        ]
        
        cols = st.columns(2)
        for i, action in enumerate(initial_actions):
            col_index = i % 2
            with cols[col_index]:
                if st.button(
                    action, 
                    key=f"initial_action_{i}",
                    help="Click to ask this question",
                    use_container_width=True
                ):
                    st.session_state.pending_message = action
                    st.rerun()
    
    # Chat management in sidebar
    with st.sidebar:
        st.subheader("💬 Chat Management")
        
        # Chat statistics
        if st.session_state.chat_history:
            total_messages = len(st.session_state.chat_history)
            user_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "user"])
            ai_responses = len([msg for msg in st.session_state.chat_history if msg["role"] == "assistant" and msg.get("llm_powered")])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Messages", total_messages)
                st.metric("AI Responses", ai_responses)
            with col2:
                st.metric("Questions", user_messages)
                st.metric("Knowledge Base", total_messages - ai_responses - user_messages)
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("🆕 New Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.last_suggested_actions = []
            st.session_state.pending_message = ""
            st.rerun()
        
        if st.button("💾 Export Chat", use_container_width=True):
            if st.session_state.chat_history:
                # Create exportable chat log
                chat_export = []
                for msg in st.session_state.chat_history:
                    chat_export.append({
                        "timestamp": msg["timestamp"],
                        "role": msg["role"],
                        "message": msg["message"],
                        "intent": msg.get("intent", ""),
                        "ai_powered": msg.get("llm_powered", False)
                    })
                
                import json
                chat_json = json.dumps(chat_export, indent=2)
                
                st.download_button(
                    label="📥 Download Chat History",
                    data=chat_json,
                    file_name=f"uae_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.info("No chat history to export")
        
        # System status
        st.subheader("🔧 System Status")
        
        # Check API health
        health_status = api_request("/chat/health")
        if health_status:
            overall_status = health_status.get("overall_status", "unknown")
            if overall_status == "healthy":
                st.success("✅ All systems operational")
            elif overall_status == "partial":
                st.warning("⚠️ Limited functionality")
            else:
                st.error("❌ System issues detected")
            
            # Show detailed status
            with st.expander("View Details"):
                st.json(health_status)
        else:
            st.error("❌ Cannot connect to chat system")


def show_application_status():
    """New page that surfaces stored applications and their current status."""

    st.header("📜 Application Status")
    st.markdown(
        "View every stored application, its current decision status, and metadata "
        "directly from the database-backed API. Use the refresh button to pull the latest data."
    )

    limit = st.number_input("Items per page", value=50, min_value=1, max_value=200)
    offset = st.number_input("Offset", value=0, min_value=0)
    if st.button("🔄 Refresh list", key="refresh_application_status"):
        st.session_state.pop("application_status_data", None)
        st.experimental_rerun()

    cached_key = f"app_status_{limit}_{offset}"
    if cached_key not in st.session_state:
        st.session_state[cached_key] = fetch_applications(limit=int(limit), offset=int(offset))

    data = st.session_state.get(cached_key) or {}
    applications = data.get("applications", [])

    if not applications:
        st.info("No applications found. Submit a new application via the intake page first.")
        return

    df = pd.DataFrame(applications)
    df = df.sort_values(by="created_at", ascending=False)

    st.markdown(f"**Showing {len(df)} applications (limit={limit}, offset={offset})**")

    status_counts = df["status"].value_counts().to_dict()
    col1, col2, col3 = st.columns(3)
    col1.metric("Applications", len(df))
    col2.metric("Approved", len(df[df["status"] == "approved"]))
    col3.metric("Under Review", len(df[df["status"] == "review_required"]))

    st.dataframe(
        df[
            [
                "application_id",
                "applicant_name",
                "status",
                "decision",
                "priority",
                "support_type",
                "emirate",
                "approved_amount",
                "created_at",
                "updated_at",
            ]
        ],
        use_container_width=True,
    )

    st.subheader("Status Breakdown")
    status_df = pd.DataFrame(list(status_counts.items()), columns=["Status", "Count"]).set_index("Status")
    st.bar_chart(status_df)


if __name__ == "__main__":
    main()
