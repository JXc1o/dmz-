# genetic_engine.py (안정적인 에너지 분배 모델)
import random
import numpy as np
from individual import Individual

class GeneticEngine:
    def __init__(self, species_id, status, population_size=100, mutation_rate=0.05, mutation_strength=0.05, params=None):
        self.id = species_id
        self.status = status
        self.initial_population_size = population_size
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
        self.population = [Individual(species_id=self.id) for _ in range(self.initial_population_size)]
        self.dead_this_tick = 0
        
        self.params = params if params else {}

    def distribute_energy(self, total_energy_gain):
        """
        [핵심 수정] 사냥 실패/성공 시나리오를 제거하고,
        사냥 능력(foraging_efficiency)에 따라 획득한 에너지를 안정적으로 차등 분배합니다.
        """
        if not self.population or total_energy_gain <= 0:
            return

        # foraging_efficiency(46) 특성값에 따라 에너지 분배 가중치를 계산
        foraging_traits = np.array([ind.get_trait_value(46, 1.0) for ind in self.population])
        total_foraging_effort = np.sum(foraging_traits)

        if total_foraging_effort > 0:
            # 가중치에 따라 모든 개체에게 에너지 차등 분배
            for i, individual in enumerate(self.population):
                share = foraging_traits[i] / total_foraging_effort
                energy = total_energy_gain * share
                individual.add_energy(energy)
        else: 
            # 모든 개체의 사냥 능력이 0일 경우 (예외 처리), 균등 분배
            energy_per_individual = total_energy_gain / len(self.population)
            for individual in self.population:
                individual.add_energy(energy_per_individual)

    def run_generation_step(self, environment):
        """
        개체별 생존, 사망, 번식을 시뮬레이션하여 개체 수를 역동적으로 변화시킵니다.
        """
        if not self.population:
            return

        base_metabolism = self.params.get('base_metabolism_cost', 0.5)
        repro_energy_ratio = self.params.get('reproduction_energy_ratio', 0.4)
        repro_min_energy = self.params.get('reproduction_min_energy', 50.0)
        environment['reproduction_min_energy'] = repro_min_energy

        next_generation = []
        self.dead_this_tick = 0
        
        for individual in self.population:
            individual.consume_energy(base_metabolism)
            if individual.energy <= 0:
                self.dead_this_tick += 1
                continue

            # 개체별 생존/번식 확률 업데이트
            individual.tick()
            individual.viability = environment['fitness_calculator'].calculate_viability(individual, environment)
            individual.fecundity = environment['fitness_calculator'].calculate_fecundity(individual, environment)

            if random.random() < individual.viability:
                next_generation.append(individual)

                num_offspring = individual.fecundity
                
                for _ in range(num_offspring):
                    parent1 = individual
                    
                    parent_energy_investment = parent1.energy * repro_energy_ratio
                    if parent1.energy > parent_energy_investment + repro_min_energy:
                        parent1.consume_energy(parent_energy_investment)
                        child_initial_energy = parent_energy_investment * 0.8

                        child_genome = parent1.genome.copy()
                        if random.random() < self.mutation_rate:
                            gene_to_mutate = random.choice(list(child_genome.keys()))
                            mutation_effect = child_genome[gene_to_mutate] * random.normalvariate(0, self.mutation_strength)
                            child_genome[gene_to_mutate] += mutation_effect
                            if child_genome[gene_to_mutate] < 0:
                                child_genome[gene_to_mutate] = 0
                        
                        offspring = Individual(
                            species_id=self.id, 
                            genome=child_genome, 
                            initial_energy=child_initial_energy
                        )
                        next_generation.append(offspring)
            else:
                 self.dead_this_tick += 1

        self.population = next_generation

    def get_dead_count_and_clear(self):
        count = self.dead_this_tick
        self.dead_this_tick = 0
        return count

    def get_population_stats(self):
        current_pop_size = len(self.population)
        if current_pop_size == 0:
            return {"population_size": 0, "avg_heat_resistance": 0, "avg_foraging_efficiency": 0}

        avg_heat = sum(ind.get_trait_value(32, 0) for ind in self.population) / current_pop_size
        avg_forage = sum(ind.get_trait_value(46, 0) for ind in self.population) / current_pop_size
        
        return {
            "population_size": current_pop_size, 
            "avg_heat_resistance": avg_heat, 
            "avg_foraging_efficiency": avg_forage
        }