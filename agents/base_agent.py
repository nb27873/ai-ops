"""
Base Agent Class for AI Ops Copilot System
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict

# Setup logging
logger = logging.getLogger(__name__)


class AgentInput:
    """Input model for agents"""

    def __init__(self, incident_id: str, data: dict, context: dict = None):
        self.incident_id = incident_id
        self.data = data
        self.context = context or {}


class AgentOutput:
    """Output model for agents"""

    def __init__(self, incident_id: str, result: dict, confidence: float, recommendations: list = None):
        self.incident_id = incident_id
        self.result = result
        self.confidence = confidence
        self.recommendations = recommendations or []


class BaseAgent(ABC):
    """Abstract base class for all AI Ops agents"""

    def __init__(self, name: str, llm_model: str = "gpt-4"):
        self.name = name
        self.llm_model = llm_model
        self.logger = logger

    @abstractmethod
    async def process(self, input_data: AgentInput) -> AgentOutput:
        """Process incident data and return analysis results"""
        pass

    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        """Calculate confidence score based on various factors"""
        if not factors:
            return 0.5

        # Simple weighted average - can be made more sophisticated
        weights = {
            'similarity_score': 0.3,
            'historical_success': 0.3,
            'data_completeness': 0.2,
            'model_certainty': 0.2
        }

        confidence = 0.0
        total_weight = 0.0

        for factor, value in factors.items():
            if factor in weights:
                confidence += value * weights[factor]
                total_weight += weights[factor]

        return confidence / total_weight if total_weight > 0 else 0.5

    def _log_processing(self, incident_id: str, action: str):
        """Log agent processing steps"""
        self.logger.info(f"Agent {self.name}: {action} for incident {incident_id}")