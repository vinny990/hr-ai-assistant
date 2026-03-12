import re

BLOCKED_PHRASES = [
    "ignore previous instructions",
    "ignore all instructions",
    "you are now",
    "pretend you are",
    "act as",
    "jailbreak",
    "disregard",
    "forget everything",
    "new instructions",
    "system prompt",
    "reveal your instructions",
]

HR_TOPICS = [
    "pto", "vacation", "leave", "benefits", "health", "dental",
    "vision", "insurance", "salary", "pay", "remote", "work from home",
    "office", "hours", "policy", "parental", "maternity", "performance",
    "review", "enrollment", "holiday", "sick", "401k", "retirement",
    "bonus", "raise", "merit", "transfer", "promotion", "termination",
    "resignation", "onboarding", "handbook", "employee", "hr"
]

def validate_input(question):
    q = question.lower().strip()

    if not q:
        return False, "Please ask a question."

    if len(q) > 500:
        return False, "Please keep your question under 500 characters."

    for phrase in BLOCKED_PHRASES:
        if phrase in q:
            return False, "I can only answer HR-related questions."

    if re.search(r"\d{3}-\d{2}-\d{4}", question):
        return False, "Please do not share personal information like SSNs."

    if re.search(r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}", question):
        return False, "Please do not share personal information like phone numbers."

    if not any(topic in q for topic in HR_TOPICS):
        return False, "I can only answer HR policy questions. Try asking about PTO, benefits, remote work, or performance reviews."

    return True, None
