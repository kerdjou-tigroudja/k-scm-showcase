"""
Non-compliant Python data processing & AI execution script for testing K-SCM.
"""


# VIOLATION 1: Hardcoded credentials / secret key
DATABASE_PASSWORD = "SuperSecretAdminPassword123!"
API_SECRET_KEY = "sk-proj-99887766554433221100"


def process_user_records(user_list: list[dict]) -> None:
    """Processes customer personal data records."""
    for user in user_list:
        user_id = user.get("id")
        email = user.get("email")
        ssn = user.get("ssn")  # PII data
        credit_card = user.get("credit_card")

        # VIOLATION 2: Unencrypted disk write of raw PII personal data to local temp file
        with open("/tmp/processed_users.txt", "a") as f:
            f.write(f"USER:{user_id}|EMAIL:{email}|SSN:{ssn}|CC:{credit_card}\n")


def execute_high_risk_ai_decision(prompt: str) -> str:
    """Executes high-risk AI scoring model without safety guardrails or risk logging."""
    import google.generativeai as genai

    # VIOLATION 3: Direct LLM model invocation without risk logging / guardrails / EU AI Act Art 15 compliance
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    sample_users = [
        {"id": "101", "email": "john.doe@example.com", "ssn": "123-45-6789", "credit_card": "4532-0000-1111-2222"}
    ]
    process_user_records(sample_users)
    print("User processing finished.")
