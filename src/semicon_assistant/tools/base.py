from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """
    Abstract interface for tool integrations.

    Tools expose structured functionality (e.g., data queries, analytics,
    simulations) that can be invoked by an LLM as part of a reasoning workflow.
    """

    name: str
    description: str

    @abstractmethod
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with validated inputs and return structured outputs.

        Implementations should be deterministic, side-effect free, and safe
        to call within an LLM-driven workflow.
        """
        raise NotImplementedError
