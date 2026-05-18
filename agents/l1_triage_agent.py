"""
L1 Incident Triage Agent - AO Team
Responsible for initial classification and quick fixes
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentInput, AgentOutput
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from knowledge.knowledge_base import KnowledgeBase


class IncidentClassification:
    """Classification result for incidents"""

    def __init__(self, system: str, incident_type: str, severity: str, affected_components: List[str]):
        self.system = system
        self.incident_type = incident_type
        self.severity = severity
        self.affected_components = affected_components

    def dict(self):
        return {
            'system': self.system,
            'incident_type': self.incident_type,
            'severity': self.severity,
            'affected_components': self.affected_components
        }


class L1TriageAgent(BaseAgent):
    """L1 Incident Triage Agent for initial classification and quick resolution"""

    def __init__(self, knowledge_base: KnowledgeBase):
        super().__init__("L1_Triage")
        self.kb = knowledge_base
        self.systems = ["GCP", "Talend", "Kafka", "Batch", "Database", "Network"]
        self.incident_types = [
            "ingestion_failure", "authentication", "data_quality",
            "pipeline_delay", "connectivity", "resource_exhaustion",
            "configuration_error", "deployment_failure"
        ]
        self.severities = ["low", "medium", "high", "critical"]

    async def process(self, input_data: AgentInput) -> AgentOutput:
        """Process incident through L1 triage"""
        self._log_processing(input_data.incident_id, "Starting triage")

        # Extract incident description
        description = input_data.data.get('description', '')
        title = input_data.data.get('title', '')

        # Classify incident
        classification = await self._classify_incident(description, title)

        # Find similar incidents
        similar_incidents = await self._find_similar_incidents(description)

        # Suggest quick fixes
        quick_fixes = await self._suggest_quick_fixes(classification, similar_incidents)

        # Check for correlation with other incidents
        correlations = await self._correlate_incidents(input_data.incident_id, classification)

        # Determine if escalation needed
        needs_escalation = self._should_escalate(classification, similar_incidents, quick_fixes)

        # Calculate confidence
        confidence_factors = {
            'classification_certainty': 0.8 if classification.system else 0.3,
            'similar_incidents_found': min(len(similar_incidents) / 5.0, 1.0),
            'quick_fix_available': 1.0 if quick_fixes else 0.0
        }
        confidence = self._calculate_confidence(confidence_factors)

        result = {
            'classification': classification.dict(),
            'similar_incidents': similar_incidents,
            'quick_fixes': quick_fixes,
            'correlations': correlations,
            'needs_escalation': needs_escalation,
            'escalation_reason': self._get_escalation_reason(needs_escalation, classification, similar_incidents)
        }

        recommendations = []
        if quick_fixes:
            recommendations.extend([f"Try quick fix: {fix['description']}" for fix in quick_fixes])
        if needs_escalation:
            recommendations.append("Escalate to L2 Analysis Agent")

        return AgentOutput(
            incident_id=input_data.incident_id,
            result=result,
            confidence=confidence,
            recommendations=recommendations
        )

    async def _classify_incident(self, description: str, title: str) -> IncidentClassification:
        """Classify incident using LLM and rule-based matching"""
        # Simple keyword-based classification (can be enhanced with LLM)
        text = f"{title} {description}".lower()

        # Detect system
        detected_system = None
        for system in self.systems:
            if system.lower() in text:
                detected_system = system
                break

        # Detect incident type
        detected_type = None
        type_keywords = {
            "ingestion_failure": ["ingestion", "extract", "load", "etl", "failed to ingest"],
            "authentication": ["auth", "login", "credential", "permission", "access denied"],
            "data_quality": ["data quality", "corrupt", "invalid", "missing", "null"],
            "pipeline_delay": ["delay", "timeout", "slow", "performance", "latency"],
            "connectivity": ["connection", "network", "sftp", "tcp", "unreachable"],
            "resource_exhaustion": ["memory", "cpu", "disk", "out of memory", "resource"],
            "configuration_error": ["config", "configuration", "parameter", "setting"],
            "deployment_failure": ["deploy", "deployment", "build", "compilation"]
        }

        for inc_type, keywords in type_keywords.items():
            if any(keyword in text for keyword in keywords):
                detected_type = inc_type
                break

        # Determine severity (simplified)
        severity = "medium"  # default
        if any(word in text for word in ["critical", "p1", "emergency", "down"]):
            severity = "critical"
        elif any(word in text for word in ["high", "p2", "major"]):
            severity = "high"
        elif any(word in text for word in ["low", "p4", "minor"]):
            severity = "low"

        # Extract affected components (simplified)
        components = []
        if "sftp" in text:
            components.append("SFTP")
        if "database" in text or "db" in text:
            components.append("Database")
        if "kafka" in text:
            components.append("Kafka")

        return IncidentClassification(
            system=detected_system or "Unknown",
            incident_type=detected_type or "other",
            severity=severity,
            affected_components=components
        )

    async def _find_similar_incidents(self, description: str) -> List[Dict[str, Any]]:
        """Find similar historical incidents"""
        # Use knowledge base to find similar incidents
        similar = await self.kb.find_similar_incidents(description, limit=5)
        return similar

    async def _suggest_quick_fixes(self, classification: IncidentClassification,
                                 similar_incidents: List[Dict]) -> List[Dict[str, Any]]:
        """Suggest quick fixes based on classification and similar incidents"""
        fixes = []

        # Rule-based quick fixes
        if classification.incident_type == "connectivity":
            fixes.append({
                "description": "Check network connectivity and firewall rules",
                "steps": ["ping target host", "verify firewall rules", "check VPN connection"],
                "estimated_time": "15 minutes"
            })

        if "SFTP" in classification.affected_components:
            fixes.append({
                "description": "Restart SFTP service and verify credentials",
                "steps": ["Check SFTP service status", "Restart service", "Verify credentials"],
                "estimated_time": "10 minutes"
            })

        # Add fixes from similar incidents
        for incident in similar_incidents:
            if 'resolution_steps' in incident and incident.get('resolution_steps'):
                fixes.append({
                    "description": f"Apply resolution from similar incident {incident['id']}",
                    "steps": incident['resolution_steps'],
                    "estimated_time": "30 minutes",
                    "source_incident": incident['id']
                })

        return fixes[:3]  # Limit to top 3 fixes

    async def _correlate_incidents(self, incident_id: str, classification: IncidentClassification) -> List[str]:
        """Find correlated incidents"""
        # Simple correlation based on system and type
        correlated = await self.kb.find_correlated_incidents(
            incident_id, classification.system, classification.incident_type
        )
        return correlated

    def _should_escalate(self, classification: IncidentClassification,
                        similar_incidents: List, quick_fixes: List) -> bool:
        """Determine if incident should be escalated to L2"""
        # Escalate if:
        # - Critical severity
        # - Unknown system or type
        # - No similar incidents found
        # - No quick fixes available
        # - Multiple components affected

        reasons = []
        if classification.severity == "critical":
            reasons.append("critical_severity")
        if classification.system == "Unknown":
            reasons.append("unknown_system")
        if classification.incident_type == "other":
            reasons.append("unknown_type")
        if len(similar_incidents) == 0:
            reasons.append("no_similar_incidents")
        if len(quick_fixes) == 0:
            reasons.append("no_quick_fixes")
        if len(classification.affected_components) > 2:
            reasons.append("multiple_components")

        return len(reasons) > 0

    def _get_escalation_reason(self, needs_escalation: bool,
                             classification: IncidentClassification,
                             similar_incidents: List) -> str:
        """Get detailed escalation reason"""
        if not needs_escalation:
            return ""

        reasons = []
        if classification.severity == "critical":
            reasons.append("Critical severity incident")
        if classification.system == "Unknown":
            reasons.append("Unable to identify affected system")
        if len(similar_incidents) == 0:
            reasons.append("No similar historical incidents found")
        if classification.incident_type == "other":
            reasons.append("Unknown incident type requiring deeper analysis")

        return "; ".join(reasons)