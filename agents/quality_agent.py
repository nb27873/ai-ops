"""
Quality Agent for incident markdown validation.
Validates incident content against the expected template and reports missing sections.
"""

import re
from typing import Any, Dict, List
from .base_agent import BaseAgent, AgentInput, AgentOutput


class QualityAgent(BaseAgent):
    """Quality Agent validates incident documentation against a template."""

    REQUIRED_FIELDS = [
        ("title", "Title"),
        ("date", "Date"),
        ("requester", "Requester"),
        ("description", "Description"),
        ("diagnosis", "Diagnosis"),
        ("resolution", "Resolution / Actions Taken")
    ]

    OPTIONAL_FIELDS = [
        ("reference", "Reference"),
        ("additional_notes", "Additional Notes")
    ]

    FIELD_PATTERNS = {
        "date": r"^\s*(Date)\s*:",
        "requester": r"^\s*(Requester|Requestor|Opened by|Opened By)\s*:",
        "description": r"^\s*(Description)\s*:\s*|^\s*(Description)\s*$",
        "diagnosis": r"^\s*(Diagnosis)\s*:\s*|^\s*(Diagnosis)\s*$",
        "resolution": r"^\s*(Resolution|Actions Taken|Action Taken|Resolution / Actions Taken)\s*:\s*|^\s*(Resolution|Actions Taken|Action Taken)\s*$",
        "reference": r"^\s*(Reference|References|Related INC|Confluence|Docs?)\s*:\s*|^\s*(Reference|References)\s*$",
        "additional_notes": r"^\s*(Additional Notes|Notes)\s*:\s*|^\s*(Additional Notes|Notes)\s*$"
    }

    def __init__(self):
        super().__init__("Quality_Agent")

    async def process(self, input_data: AgentInput) -> AgentOutput:
        """Process raw incident input and compute template compliance."""
        self._log_processing(input_data.incident_id, "Starting quality validation")

        raw_content = input_data.data.get("raw_content") or input_data.data.get("content") or ""
        title = input_data.data.get("title", "")

        if raw_content and raw_content.strip():
            validation = self.validate_markdown(raw_content)
        else:
            validation = self.validate_structured(input_data.data)

        confidence = validation.get("required_field_score", 0) / 100.0
        return AgentOutput(
            incident_id=input_data.incident_id,
            result={"quality_validation": validation},
            confidence=confidence
        )

    def _match_field(self, text: str, field_name: str) -> bool:
        """Return whether a field pattern appears in the text."""
        pattern = self.FIELD_PATTERNS.get(field_name)
        if not pattern:
            return False
        return bool(re.search(pattern, text, re.IGNORECASE | re.MULTILINE))

    def validate_markdown(self, content: str) -> Dict[str, Any]:
        """Validate a markdown incident body against the template."""
        content = content.replace("\r", "")
        lines = [line.strip() for line in content.splitlines() if line.strip()]

        title_line = lines[0] if lines else ""
        title_present = bool(title_line and ("inc" in title_line.lower() or re.search(r"INC\d+", title_line, re.IGNORECASE)))

        field_presence = {
            "title": title_present
        }

        for field_name, _ in self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS:
            if field_name == "title":
                continue
            field_presence[field_name] = self._match_field(content, field_name)

        required_found = sum(1 for field_name, _ in self.REQUIRED_FIELDS if field_presence.get(field_name))
        missing_required = [label for field_name, label in self.REQUIRED_FIELDS if not field_presence.get(field_name)]

        optional_found = [label for field_name, label in self.OPTIONAL_FIELDS if field_presence.get(field_name)]
        optional_missing = [label for field_name, label in self.OPTIONAL_FIELDS if not field_presence.get(field_name)]

        score = int((required_found / len(self.REQUIRED_FIELDS)) * 100)

        return {
            "required_field_score": score,
            "required_fields_found": required_found,
            "total_required_fields": len(self.REQUIRED_FIELDS),
            "missing_required_fields": missing_required,
            "optional_fields_found": optional_found,
            "optional_fields_missing": optional_missing,
            "field_presence": field_presence,
            "summary": f"Found {required_found} of {len(self.REQUIRED_FIELDS)} required fields.",
            "recommendation": "Add missing sections to improve similarity matching and incident quality." if missing_required else "Incident document matches the expected template structure."
        }

    def validate_structured(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate structured input fields when markdown content is unavailable."""
        field_presence = {
            "title": bool(data.get("title")),
            "date": bool(data.get("date")),
            "requester": bool(data.get("requester")),
            "description": bool(data.get("description")),
            "diagnosis": bool(data.get("diagnosis")) or bool(data.get("initial_diagnosis")),
            "resolution": bool(data.get("resolution")) or bool(data.get("actions_taken"))
        }

        for field_name, _ in self.OPTIONAL_FIELDS:
            field_presence[field_name] = bool(data.get(field_name))

        required_found = sum(1 for field_name, _ in self.REQUIRED_FIELDS if field_presence.get(field_name))
        missing_required = [label for field_name, label in self.REQUIRED_FIELDS if not field_presence.get(field_name)]
        optional_found = [label for field_name, label in self.OPTIONAL_FIELDS if field_presence.get(field_name)]
        optional_missing = [label for field_name, label in self.OPTIONAL_FIELDS if not field_presence.get(field_name)]

        score = int((required_found / len(self.REQUIRED_FIELDS)) * 100)

        return {
            "required_field_score": score,
            "required_fields_found": required_found,
            "total_required_fields": len(self.REQUIRED_FIELDS),
            "missing_required_fields": missing_required,
            "optional_fields_found": optional_found,
            "optional_fields_missing": optional_missing,
            "field_presence": field_presence,
            "summary": f"Found {required_found} of {len(self.REQUIRED_FIELDS)} required fields.",
            "recommendation": "Add the missing required fields to align with the incident template." if missing_required else "Incident is complete with required fields."
        }
