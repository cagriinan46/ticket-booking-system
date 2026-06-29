import json
import os

from dotenv import load_dotenv
from ollama import Client

from constants.ai import INVALID_AI_VALUES


load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
try:
    OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", os.getenv("OLLAMA_TIMEOUT", "180")))
except ValueError:
    OLLAMA_TIMEOUT_SECONDS = 15.0

ollama_client = Client(
    host=OLLAMA_HOST,
    timeout=OLLAMA_TIMEOUT_SECONDS
)


def clean_ai_value(value):
    if value is None:
        return None

    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.lower() in INVALID_AI_VALUES:
            return None
        return cleaned

    return value


def parse_llm_json(content):
    cleaned = content.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(cleaned[start:end + 1])
