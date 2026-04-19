"""Astra ⭐ - AI Simulation System for SupplyChainGPT Council.

Astra is a swarm intelligence engine that runs parallel to the Council of Debate,
providing predictive simulations through:
- Graph building with entity extraction
- Persona generation for simulation agents
- Parallel multi-agent simulation
- Report generation and analysis

When the Council runs, Astra automatically activates to provide:
- Future scenario predictions
- Multi-agent simulations
- Risk forecasting
- Opportunity identification
"""

from backend.astra.schemas import (
    SimulationState,
    Persona,
    Entity,
    Relationship,
    SimulationResult,
    SimulationConfig,
)
from backend.astra.graph_builder import GraphBuilder
from backend.astra.persona_generator import PersonaGenerator
from backend.astra.simulation_engine import SimulationEngine
from backend.astra.report_agent import ReportAgent
from backend.astra.memory_manager import MemoryManager

__all__ = [
    "SimulationState",
    "Persona",
    "Entity",
    "Relationship",
    "SimulationResult",
    "SimulationConfig",
    "GraphBuilder",
    "PersonaGenerator",
    "SimulationEngine",
    "ReportAgent",
    "MemoryManager",
]
