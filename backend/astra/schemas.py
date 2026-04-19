"""Pydantic schemas for MiroFish simulation system."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EntityType(str, Enum):
    COMPANY = "company"
    PRODUCT = "product"
    PERSON = "person"
    ORGANIZATION = "organization"
    MARKET = "market"
    EVENT = "event"
    TREND = "trend"
    POLICY = "policy"


class RelationshipType(str, Enum):
    COMPETES_WITH = "competes_with"
    SUPPLIES = "supplies"
    INFLUENCES = "influences"
    OPPOSES = "opposes"
    SUPPORTS = "supports"
    CAUSED_BY = "caused_by"
    LEADS_TO = "leads_to"
    PART_OF = "part_of"


class Entity(BaseModel):
    """An entity extracted from the scenario seed."""
    id: str = Field(..., description="Unique entity identifier")
    name: str = Field(..., description="Entity name")
    type: EntityType = Field(..., description="Entity type")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional attributes")
    importance: float = Field(default=1.0, ge=0.0, le=1.0, description="Entity importance (0-1)")


class Relationship(BaseModel):
    """A relationship between two entities."""
    source_id: str = Field(..., description="Source entity ID")
    target_id: str = Field(..., description="Target entity ID")
    type: RelationshipType = Field(..., description="Relationship type")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Relationship strength (0-1)")
    description: Optional[str] = Field(None, description="Relationship description")


class PersonaRole(str, Enum):
    COMPETITOR = "competitor"
    CUSTOMER = "customer"
    MEDIA = "media"
    REGULATOR = "regulator"
    INVESTOR = "investor"
    ANALYST = "analyst"
    SUPPLIER = "supplier"
    EXPERT = "expert"


class Persona(BaseModel):
    """A simulated agent persona."""
    id: str = Field(..., description="Unique persona identifier")
    name: str = Field(..., description="Persona name")
    role: PersonaRole = Field(..., description="Persona role in simulation")
    entity_id: Optional[str] = Field(None, description="Associated entity ID")
    system_prompt: str = Field(..., description="Persona system prompt")
    traits: List[str] = Field(default_factory=list, description="Personality traits")
    goals: List[str] = Field(default_factory=list, description="Persona goals")
    memory: List[str] = Field(default_factory=list, description="Persona memory/context")
    position: Dict[str, float] = Field(default_factory=dict, description="Position on various axes (-1 to 1)")


class SimulationConfig(BaseModel):
    """Configuration for a simulation run."""
    name: str = Field(..., description="Simulation name")
    description: Optional[str] = Field(None, description="Simulation description")
    seed_query: str = Field(..., description="Original user query/seed")
    horizon_days: int = Field(default=30, ge=1, le=365, description="Simulation horizon in days")
    num_personas: int = Field(default=50, ge=2, le=200, description="Number of personas to generate")
    rounds: int = Field(default=3, ge=1, le=10, description="Simulation rounds/interactions")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="LLM temperature for simulation")
    focus_areas: List[str] = Field(default_factory=list, description="Areas to focus on")


class SimulationRound(BaseModel):
    """A single round of simulation."""
    round_number: int = Field(..., description="Round number")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    interactions: List[Dict[str, Any]] = Field(default_factory=list, description="Agent interactions")
    events: List[str] = Field(default_factory=list, description="Key events this round")
    sentiment_shift: Dict[str, float] = Field(default_factory=dict, description="Sentiment changes")


class ScenarioDetail(BaseModel):
    """A detailed scenario with probability and explanation."""
    name: str = Field(..., description="Scenario name")
    probability: float = Field(default=0.5, ge=0.0, le=1.0, description="Probability of this scenario")
    description: str = Field(default="", description="Detailed scenario description")
    impact: str = Field(default="medium", description="Impact level: low, medium, high, critical")
    key_drivers: List[str] = Field(default_factory=list, description="Key drivers for this scenario")
    timeline: str = Field(default="", description="Expected timeline for this scenario")
    affected_entities: List[str] = Field(default_factory=list, description="Entities most affected")


class SourceReference(BaseModel):
    """A source reference used in the simulation."""
    title: str = Field(default="", description="Source title")
    url: str = Field(default="", description="Source URL")
    type: str = Field(default="api", description="Source type: api, rag, mcp, web")
    relevance: float = Field(default=0.5, ge=0.0, le=1.0, description="Relevance score")
    snippet: str = Field(default="", description="Relevant snippet from source")


class SimulationResult(BaseModel):
    """Final result of a simulation."""
    prediction: str = Field(..., description="Main prediction/outcome")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    key_factors: List[str] = Field(default_factory=list, description="Key factors influencing outcome")
    scenarios: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative scenarios")
    risks: List[str] = Field(default_factory=list, description="Identified risks")
    opportunities: List[str] = Field(default_factory=list, description="Identified opportunities")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    sources: List[SourceReference] = Field(default_factory=list, description="Sources used in simulation")
    detailed_explanation: str = Field(default="", description="Detailed explanation of the prediction")
    methodology: str = Field(default="", description="Methodology used for the simulation")
    assumptions: List[str] = Field(default_factory=list, description="Key assumptions made")
    data_quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Quality of data used")


class SimulationState(BaseModel):
    """Complete state of a simulation."""
    id: str = Field(..., description="Simulation unique ID")
    config: SimulationConfig = Field(..., description="Simulation configuration")
    status: str = Field(default="pending", description="Simulation status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Graph data
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    
    # Simulation data
    personas: List[Persona] = Field(default_factory=list)
    rounds: List[SimulationRound] = Field(default_factory=list)
    result: Optional[SimulationResult] = Field(None)
    
    # Metadata
    agent_type: str = Field(..., description="Agent that triggered simulation (brand/market)")
    parent_query: Optional[str] = Field(None, description="Original council query")

    model_config = {"arbitrary_types_allowed": True}
