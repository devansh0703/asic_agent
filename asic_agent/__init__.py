"""
ASIC-Agent: Autonomous Multi-Agent System for ASIC Design
Built with Gemini 2.5 Flash, ChromaDB, and LangGraph
"""

__version__ = "1.0.0"
__author__ = "ASIC-Agent Development Team"

from .config import Config
from .agents.main_agent import MainAgent
from .agents.verification_agent import VerificationAgent
from .agents.hardening_agent import HardeningAgent
from .agents.caravel_agent import CaravelAgent
from .workflows.orchestrator import ASICOrchestrator
from .schemas import (
    RTLGenerationRequest,
    RTLGenerationResponse,
    LintingResult,
    TestbenchGenerationRequest,
    TestbenchGenerationResponse,
    SimulationResult,
    OpenLaneConfig,
    HardeningFlowResult,
    KnowledgeDocument,
    ErrorSolution,
)

__all__ = [
    "Config",
    "MainAgent",
    "VerificationAgent",
    "HardeningAgent",
    "CaravelAgent",
    "ASICOrchestrator",
    "RTLGenerationRequest",
    "RTLGenerationResponse",
    "LintingResult",
    "TestbenchGenerationRequest",
    "TestbenchGenerationResponse",
    "SimulationResult",
    "OpenLaneConfig",
    "HardeningFlowResult",
    "KnowledgeDocument",
    "ErrorSolution",
]
