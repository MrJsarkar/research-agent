import uuid
import random
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

class AgentCohort:
    def __init__(self, name: str, population: int, traits: Dict[str, float]):
        self.id = str(uuid.uuid4())
        self.name = name
        self.population = population
        self.traits = traits # e.g., "aggression": 0.8, "innovation": 0.5
        self.resources = 1000
        self.satisfaction = 1.0

class WorldState:
    def __init__(self, seed_text: str):
        self.world_id = str(uuid.uuid4())
        self.seed_text = seed_text
        self.epoch = 0
        self.total_population = 0
        self.cohorts: List[AgentCohort] = []
        self.global_stability = 1.0
        self.tech_level = 1.0
        self.event_log: List[Dict[str, Any]] = []

class SimulationEngine:
    def __init__(self):
        self.worlds: Dict[str, WorldState] = {}
        
    def generate_world_from_seed(self, seed_text: str) -> WorldState:
        """
        Parses reality seed and spawns a simulated world.
        Here we use heuristic keyword analysis to generate cohorts.
        """
        world = WorldState(seed_text)
        seed_lower = seed_text.lower()
        
        # Keyword based demographic generation
        base_pop = 1000000 # Million level simulation
        if "scarcity" in seed_lower or "post-apocalyptic" in seed_lower:
            base_pop = 100000
            world.global_stability = 0.4
        elif "utopia" in seed_lower or "abundance" in seed_lower:
            base_pop = 5000000
            world.global_stability = 0.95
            
        world.total_population = base_pop
        
        # Spawn cohorts
        factions = []
        if "corporate" in seed_lower or "business" in seed_lower:
            factions.append(("Corporate Elites", {"greed": 0.9, "innovation": 0.7, "empathy": 0.2}))
        if "rebel" in seed_lower or "resistance" in seed_lower:
            factions.append(("Resistance Fighters", {"aggression": 0.8, "solidarity": 0.9, "subservience": 0.1}))
        if "academic" in seed_lower or "research" in seed_lower:
            factions.append(("Techno-Scholars", {"innovation": 0.95, "logic": 0.8, "aggression": 0.2}))
            
        # Default cohorts if none matched
        if not factions:
            factions = [
                ("General Populace", {"compliance": 0.7, "productivity": 0.6, "innovation": 0.4}),
                ("Ruling Class", {"control": 0.9, "greed": 0.6, "empathy": 0.3}),
            ]
            
        # Distribute population
        for name, traits in factions:
            pop = int(base_pop * random.uniform(0.1, 0.5))
            world.cohorts.append(AgentCohort(name, pop, traits))
            
        # Adjust total to match distributed
        world.total_population = sum(c.population for c in world.cohorts)
        
        world.event_log.append({
            "epoch": 0,
            "timestamp": datetime.now().isoformat(),
            "type": "genesis",
            "message": f"World initialized from Reality Seed. {len(world.cohorts)} macro-cohorts spawned. Initial Population: {world.total_population:,}",
            "impact": 0.0
        })
        
        self.worlds[world.world_id] = world
        return world

    def advance_epoch(self, world_id: str) -> Dict[str, Any]:
        """
        Advances the simulation by one epoch and generates events/interactions between cohorts.
        """
        if world_id not in self.worlds:
            raise ValueError(f"World {world_id} not found.")
            
        world = self.worlds[world_id]
        world.epoch += 1
        
        epoch_events = []
        
        # 1. Tech Progression
        tech_growth = random.uniform(0.01, 0.05) * (world.global_stability + 0.5)
        world.tech_level *= (1.0 + tech_growth)
        
        if random.random() < 0.2:
            epoch_events.append({
                "type": "discovery",
                "message": f"Technological breakthrough. Global Tech Level reached {world.tech_level:.2f}.",
                "impact": 0.1
            })
            world.global_stability += 0.05
            
        # 2. Cohort Interactions (Million-level abstracted)
        impact_sum = 0
        for i in range(len(world.cohorts)):
            cohort_a = world.cohorts[i]
            
            # Internal events (Growth / Attrition)
            growth_rate = random.uniform(-0.02, 0.05) * world.global_stability
            cohort_a.population = int(cohort_a.population * (1.0 + growth_rate))
            
            # Interaction with another cohort
            if len(world.cohorts) > 1:
                target_idx = (i + 1) % len(world.cohorts)
                cohort_b = world.cohorts[target_idx]
                
                # Compare traits to generate conflict or cooperation
                a_aggression = cohort_a.traits.get("aggression", 0.5)
                b_aggression = cohort_b.traits.get("aggression", 0.5)
                
                conflict_chance = (a_aggression + b_aggression) / 2.0 * (1.0 - world.global_stability)
                
                if random.random() < conflict_chance:
                    # Conflict
                    casualty_a = int(cohort_a.population * random.uniform(0.01, 0.1))
                    casualty_b = int(cohort_b.population * random.uniform(0.01, 0.1))
                    cohort_a.population -= casualty_a
                    cohort_b.population -= casualty_b
                    
                    impact = -0.1
                    impact_sum += impact
                    epoch_events.append({
                        "type": "conflict",
                        "message": f"Clash between {cohort_a.name} and {cohort_b.name}. Casualties: {casualty_a + casualty_b:,}",
                        "impact": impact
                    })
                elif random.random() > 0.6:
                    # Cooperation
                    synergy = random.uniform(0.01, 0.05)
                    world.tech_level += synergy * 0.1
                    impact = 0.05
                    impact_sum += impact
                    epoch_events.append({
                        "type": "cooperation",
                        "message": f"Trade and cultural exchange between {cohort_a.name} and {cohort_b.name} yields prosperity.",
                        "impact": impact
                    })
                    
        # Update World State
        world.global_stability = max(0.0, min(1.0, world.global_stability + impact_sum))
        world.total_population = sum(max(0, c.population) for c in world.cohorts)
        
        # Summary event for the epoch
        summary_event = {
            "epoch": world.epoch,
            "timestamp": datetime.now().isoformat(),
            "type": "epoch_summary",
            "message": f"Epoch {world.epoch} concluded. Population: {world.total_population:,} | Stability: {world.global_stability:.2f}",
            "impact": impact_sum,
            "details": epoch_events
        }
        
        world.event_log.append(summary_event)
        
        return {
            "world_id": world.world_id,
            "epoch": world.epoch,
            "population": world.total_population,
            "stability": world.global_stability,
            "tech_level": world.tech_level,
            "new_events": [summary_event]
        }
        
    def get_world_status(self, world_id: str) -> Dict[str, Any]:
        if world_id not in self.worlds:
            raise ValueError(f"World {world_id} not found.")
        world = self.worlds[world_id]
        return {
            "world_id": world.world_id,
            "epoch": world.epoch,
            "population": world.total_population,
            "stability": world.global_stability,
            "tech_level": world.tech_level,
            "cohorts": [
                {
                    "name": c.name,
                    "population": c.population,
                    "traits": c.traits
                } for c in world.cohorts
            ],
            "recent_events": world.event_log[-5:] if world.event_log else []
        }
