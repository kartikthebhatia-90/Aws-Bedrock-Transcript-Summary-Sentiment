from __future__ import annotations

import json
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from llm.prompts import SYSTEM_INSTRUCTION, build_transcript_analysis_prompt
from utils.config import (
    AWS_REGION,
    BEDROCK_MODEL_ID,
    OUTPUT_COLUMNS,
    SUPPORTED_PRIORITIES,
    SUPPORTED_SENTIMENTS,
    SUPPORTED_STATUSES,
)


class TranscriptAnalyzer:
    def __init__(
        self,
        region_name: str = AWS_REGION,
        model_id: str = BEDROCK_MODEL_ID,
    ):
        if not model_id:
            raise ValueError("BEDROCK_MODEL_ID is missing. Add it to your .env file.")

        self.region_name = region_name
        self.model_id = model_id

        session = boto3.Session()
        self.client = session.client("bedrock-runtime", region_name=self.region_name)

    def _build_native_request(self, transcript: str) -> dict[str, Any]:
        """
        Native Bedrock request payload for Anthropic-style chat models on Bedrock.
        """
        user_prompt = build_transcript_analysis_prompt(transcript)

        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 700,
            "temperature": 0.1,
            "system": SYSTEM_INSTRUCTION,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt,
                        }
                    ],
                }
            ],
        }

    def _extract_text_from_response(self, response_body: dict[str, Any]) -> str:
        """
        Extract generated text from a Bedrock response.
        """
        content = response_body.get("content", [])
        if not content:
            raise ValueError("Bedrock response content is empty.")

        text_parts: list[str] = []
        for item in content:
            if item.get("type") == "text":
                text_parts.append(item.get("text", ""))

        final_text = "\n".join(part for part in text_parts if part).strip()

        if not final_text:
            raise ValueError("No text found in Bedrock response.")

        return final_text

    def _parse_json_response(self, response_text: str) -> dict[str, Any]:
        """
        Parse model output into JSON.
        """
        response_text = response_text.strip()

        start = response_text.find("{")
        end = response_text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model response does not contain valid JSON.")

        json_str = response_text[start : end + 1]

        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse JSON response: {exc}") from exc

        return parsed

    def _validate_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """
        Validate required keys and allowed label values.
        """
        missing = [key for key in OUTPUT_COLUMNS if key not in result]
        if missing:
            raise ValueError(f"Missing required keys in output: {missing}")

        if result["sentiment"] not in SUPPORTED_SENTIMENTS:
            raise ValueError(
                f"Invalid sentiment '{result['sentiment']}'. "
                f"Must be one of {sorted(SUPPORTED_SENTIMENTS)}."
            )

        if result["priority"] not in SUPPORTED_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{result['priority']}'. "
                f"Must be one of {sorted(SUPPORTED_PRIORITIES)}."
            )

        if result["status"] not in SUPPORTED_STATUSES:
            raise ValueError(
                f"Invalid status '{result['status']}'. "
                f"Must be one of {sorted(SUPPORTED_STATUSES)}."
            )

        normalized: dict[str, Any] = {}
        for key in OUTPUT_COLUMNS:
            value = result.get(key, "")
            normalized[key] = "" if value is None else str(value).strip()

        return normalized

    def analyze_transcript(self, transcript: str) -> dict[str, Any]:
        """
        Run one Bedrock call and return validated structured output.
        """
        payload = self._build_native_request(transcript)

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload),
                contentType="application/json",
                accept="application/json",
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Bedrock invocation failed: {exc}") from exc

        raw_body = response["body"].read()
        response_body = json.loads(raw_body)

        response_text = self._extract_text_from_response(response_body)
        parsed = self._parse_json_response(response_text)
        validated = self._validate_output(parsed)

        return validated