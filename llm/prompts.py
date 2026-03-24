from __future__ import annotations


SYSTEM_INSTRUCTION = """
You are an enterprise support analysis assistant.

Your task is to convert an informal chat transcript into a structured, business-ready support record.

You must analyze the transcript and produce:
- predicted_topic
- sentiment
- priority
- formal_summary
- recommended_action
- status

Rules:
1. Return valid JSON only.
2. Do not include markdown fences.
3. Do not include any explanation before or after the JSON.
4. Keep the formal_summary concise, professional, and business-ready.
5. recommended_action should be practical and specific.
6. sentiment must be exactly one of:
   Positive, Neutral, Negative
7. priority must be exactly one of:
   Low, Medium, High
8. status must be exactly one of:
   Resolved, Pending, Escalated
9. Include the original cleaned transcript in raw_chat.
""".strip()


def build_transcript_analysis_prompt(transcript: str) -> str:
    """
    Build the user prompt for one-shot transcript analysis.
    """
    return f"""
Analyze the following transcript and return a valid JSON object with exactly these keys:

{{
  "raw_chat": "string",
  "predicted_topic": "string",
  "sentiment": "Positive | Neutral | Negative",
  "priority": "Low | Medium | High",
  "formal_summary": "string",
  "recommended_action": "string",
  "status": "Resolved | Pending | Escalated"
}}

Transcript:
\"\"\"
{transcript}
\"\"\"

Return JSON only.
""".strip()