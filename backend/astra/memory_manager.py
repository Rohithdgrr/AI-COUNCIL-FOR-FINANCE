"""Memory Manager for MiroFish - Manages temporal memory updates during simulation."""

import logging
from typing import List

from backend.astra.schemas import Persona, SimulationRound

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages persona memory updates during simulation rounds."""

    def update_memories(
        self,
        personas: List[Persona],
        round_result: SimulationRound,
    ) -> None:
        """Update persona memories with round results.

        Args:
            personas: List of personas to update
            round_result: Results from the completed round
        """
        for persona in personas:
            # Add key events from this round to persona memory
            for event in round_result.events[:3]:
                memory_entry = f"Round {round_result.round_number}: {event}"
                persona.memory.append(memory_entry)

            # Add sentiment shifts as memory context
            if round_result.sentiment_shift:
                shifts = "; ".join(
                    f"{k}: {v:+.1f}" for k, v in round_result.sentiment_shift.items()
                )
                persona.memory.append(
                    f"Round {round_result.round_number} sentiment: {shifts}"
                )

            # Keep memory bounded (last 15 entries)
            if len(persona.memory) > 15:
                persona.memory = persona.memory[-15:]

        logger.debug(f"Updated memories for {len(personas)} personas after round {round_result.round_number}")

    def inject_temporal_context(
        self,
        personas: List[Persona],
        round_num: int,
        horizon_days: int,
    ) -> None:
        """Inject temporal context into persona memories.

        Simulates the passage of time by adding context about
        what day/time it is in the simulation.

        Args:
            personas: List of personas to update
            round_num: Current round number
            horizon_days: Total simulation horizon in days
        """
        day = int((round_num / max(round_num, 1)) * horizon_days)
        temporal_context = f"Current simulation time: Day {day} of {horizon_days}"

        for persona in personas:
            # Prepend temporal context to memory (not append, so it's prominent)
            persona.memory = [temporal_context] + persona.memory[-14:]

        logger.debug(f"Injected temporal context: Day {day}/{horizon_days}")

    def inject_individual_memory(
        self,
        persona: Persona,
        memory_item: str,
    ) -> None:
        """Inject a specific memory item into a persona.

        Used for GraphRAG-style individual memory injection.

        Args:
            persona: Target persona
            memory_item: Memory content to inject
        """
        persona.memory.append(memory_item)
        if len(persona.memory) > 15:
            persona.memory = persona.memory[-15:]

    def inject_collective_memory(
        self,
        personas: List[Persona],
        memory_item: str,
    ) -> None:
        """Inject a shared memory item into all personas.

        Simulates collective/collective memory injection from GraphRAG.

        Args:
            personas: All personas
            memory_item: Shared memory content
        """
        for persona in personas:
            persona.memory.append(f"[COLLECTIVE] {memory_item}")
            if len(persona.memory) > 15:
                persona.memory = persona.memory[-15:]

        logger.debug(f"Injected collective memory into {len(personas)} personas")
