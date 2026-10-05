import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

openrouter_key = os.getenv("OPENROUTER_API_KEY")
sheetdb_url = os.getenv("SHEETDB_API_URL")

candidate_text = """
Ravi Teja is a GenAI Engineer.
Email: raviteja@example.com
He has experience in Python, Java and Generative AI.
"""

extraction_prompt = f"""
Extract the candidate information from the text below.

Return only a valid JSON object with these fields:
Name
Email
Role

Do not add markdown, explanations, or extra text.

Candidate text:
{candidate_text}
"""

headers = {
    "Authorization": f"Bearer {openrouter_key}",
    "Content-Type": "application/json"
}

request_body = {
    "model": "openrouter/free",
    "messages": [
        {
            "role": "user",
            "content": extraction_prompt
        }
    ],
    "temperature": 0
}

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json=request_body,
    timeout=30
)

print("OpenRouter Status Code:", response.status_code)

if response.status_code == 200:
    response_data = response.json()

    message_data = response_data.get("choices", [{}])[0]
    message = message_data.get("message", {})
    llm_output = message.get("content", "")

    print("----- LLM Output -----")
    print(llm_output)

    try:
        candidate_data = json.loads(llm_output)

        print("----- Valid JSON -----")
        print(candidate_data)

        candidate_email = candidate_data.get("Email", "").strip()

        check_response = requests.get(
            sheetdb_url,
            headers={
                "Accept": "application/json"
            },
            timeout=10
        )

        if check_response.status_code == 200:
            existing_records = check_response.json()

            email_exists = any(
                record.get("Email", "").strip().lower() == candidate_email.lower()
                for record in existing_records
            )

            if email_exists:
                print(f"{candidate_email} already exists in Google Sheet.")
                print("Record not inserted.")

            else:
                sheetdb_payload = {
                    "data": [candidate_data]
                }

                sheetdb_headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }

                sheetdb_response = requests.post(
                    sheetdb_url,
                    json=sheetdb_payload,
                    headers=sheetdb_headers,
                    timeout=10
                )

                print("SheetDB Status Code:", sheetdb_response.status_code)

                if sheetdb_response.status_code == 201:
                    print("Candidate data stored successfully in SheetDB.")
                    print(sheetdb_response.json())
                else:
                    print("Failed to store candidate data.")
                    print(sheetdb_response.text)

        else:
            print("Failed to check existing records.")
            print(check_response.text)

    except json.JSONDecodeError as error:
        print("Invalid JSON received from OpenRouter.")
        print("JSON Error:", error)

else:
    print("OpenRouter request failed.")
    print(response.text)