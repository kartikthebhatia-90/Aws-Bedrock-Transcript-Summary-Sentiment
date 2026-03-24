from __future__ import annotations

from typing import Any

from llm.analyzer import TranscriptAnalyzer
from pipeline.preprocess import preprocess_transcript
from storage.sqlite_store import SQLiteStore


class TranscriptPipeline:
    def __init__(
        self,
        analyzer: TranscriptAnalyzer | None = None,
        store: SQLiteStore | None = None,
    ):
        self.analyzer = analyzer or TranscriptAnalyzer()
        self.store = store or SQLiteStore()

    def run(self, raw_transcript: str) -> dict[str, Any]:
        """
        End-to-end pipeline:
        raw transcript -> preprocess -> Bedrock analyze -> save to SQLite
        """
        cleaned_transcript = preprocess_transcript(raw_transcript)
        analyzed_result = self.analyzer.analyze_transcript(cleaned_transcript)

        # Make sure the cleaned version is what gets stored
        analyzed_result["raw_chat"] = cleaned_transcript

        record_id = self.store.insert_result(analyzed_result)

        final_result = dict(analyzed_result)
        final_result["id"] = record_id

        saved_row = self.store.fetch_result_by_id(record_id)
        if saved_row and "created_at" in saved_row:
            final_result["created_at"] = saved_row["created_at"]

        return final_result