import json
import os
import requests

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
)

schema = {
    "type": "json_schema",
    "json_schema": {
        "name": "book_requirements",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "topics": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "reference_titles": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "exclude_titles": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "authors": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "language": {
                    "type": ["string", "null"]
                },
                "year_from": {
                    "type": ["integer", "null"]
                },
                "year_to": {
                    "type": ["integer", "null"]
                },
                "min_pages": {
                    "type": ["integer", "null"]
                },
                "max_pages": {
                    "type": ["integer", "null"]
                }
            },
            "required": [
                "topics",
                "reference_titles",
                "exclude_titles",
                "authors",
                "language",
                "year_from",
                "year_to",
                "min_pages",
                "max_pages"
            ],
            "additionalProperties": False
        }
    }
}

description = """
I want a book with an imaginary world and magic like Harry Potter.
I have already read Harry Potter, so don't recommend Harry Potter.
I want something adventurous and preferably suitable for adults.
"""

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": """
Extract book search requirements from the user's description.

Do not recommend books.

A mentioned book can be a reference example rather than the
desired result.

If the user already read a book or says not to recommend it,
put it in exclude_titles.

Extract broad concepts into topics.
"""
            },
            {
                "role": "user",
                "content": description,
            }
        ],
        "response_format": schema,
        "temperature": 0,
    },
    timeout=60,
)

print("Status:", response.status_code)

data = response.json()

if response.status_code != 200:
    print(json.dumps(data, indent=2))
    raise SystemExit(1)

content = data["choices"][0]["message"]["content"]

print("\nRaw result:")
print(content)

print("\nParsed JSON:")
print(json.dumps(json.loads(content), indent=2))