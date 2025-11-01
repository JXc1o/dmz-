# optimizer.py (동적 파라미터 생성 기능 확장 버전)
import random
import json
import os
import pandas as pd
import numpy as np
from multiprocessing import Pool, cpu_count
from functools import partial
from objective import evaluate_fitness
from species_generator import SPECIES_ARCHETYPES

POPULATION_SIZE = 20
N_GENERATIONS = 50
BASE_MUTATION_RATE = 0.2
CROSSOVER_RATE = 0.9
ETA_C = 20
ETA_M = 20

def generate_dynamic_param_ranges(config):
    """
    config 파일을 동적으로 분석하여 최적화할 모든 파라미터의 이름과 범위를 생성합니다.
    """
    param_ranges = {}
    
    species_id_counter = 0
    ecosystem_setup = config.get('ecosystem_setup', {})
    fixed_params = config.get('species_fixed_params', {})
    
    for archetype_name, count in ecosystem_setup.items():
        if archetype_name not in SPECIES_ARCHETYPES:
            continue
        archetype = SPECIES_ARCHETYPES[archetype_name]
        fixed_for_archetype = fixed_params.get(archetype_name, {})
        
        for _ in range(count):
            if archetype['role_class'] != 'GeneticEngine':
                for param_name, value_range in archetype['param_ranges'].items():
                    fixed_value = fixed_for_archetype.get(param_name)
                    if fixed_value is not None:
                        continue
                    key = f"species_ID_{species_id_counter}_{param_name}"
                    param_ranges[key] = value_range
            species_id_counter += 1
            
    if 'climate_scenario' in config:
        param_ranges['config_climate_scenario_initial_temp'] = (10.0, 20.0)
        # [수정] initial_nutrients 파라미터 제거

    if 'genetic_engine_params' in config:
        param_ranges['config_genetic_engine_params_mutation_rate'] = (0.01, 0.2)
        param_ranges['config_genetic_engine_params_mutation_strength'] = (0.01, 0.1)
        param_ranges['config_genetic_engine_params_optimal_temperature'] = (10.0, 25.0)
        param_ranges['config_genetic_engine_params_base_metabolism_cost'] = (0.1, 1.0)
        param_ranges['config_genetic_engine_params_reproduction_energy_ratio'] = (0.2, 0.6)
        param_ranges['config_genetic_engine_params_reproduction_min_energy'] = (20.0, 100.0)

    if 'interaction_settings' in config:
        param_ranges['config_interaction_settings_energy_conversion_efficiency'] = (0.1, 0.5)
        
    return param_ranges

def initialize_population(param_ranges):
    """파라미터 범위 내에서 무작위로 초기 집단을 생성합니다."""
    population = []
    population_size = POPULATION_SIZE
    for _ in range(population_size):
        individual = {}
        for param_name, (min_val, max_val) in param_ranges.items():
            individual[param_name] = random.uniform(min_val, max_val)
        population.append(individual)
    return population

def tournament_selection(population, fitness_scores, k=3):
    """토너먼트 선택: k개의 개체를 무작위로 뽑아 가장 좋은 개체를 선택합니다."""
    best_idx = -1
    best_fitness = -1e9
    selected_indices = random.sample(range(len(population)), k)
    for idx in selected_indices:
        if best_idx == -1 or fitness_scores[idx] > best_fitness:
            best_idx = idx
            best_fitness = fitness_scores[idx]
    return population[best_idx]

def simulated_binary_crossover(parent1, parent2, param_ranges):
    """SBX 교차 연산자"""
    child1, child2 = parent1.copy(), parent2.copy()
    if random.random() > CROSSOVER_RATE:
        return child1, child2
        
    for key in param_ranges:
        if random.random() > 0.5:
            p1_val, p2_val = parent1[key], parent2[key]
            min_val, max_val = param_ranges[key]

            if abs(p1_val - p2_val) > 1e-14:
                y1, y2 = (p1_val, p2_val) if p1_val < p2_val else (p2_val, p1_val)
                
                u = random.random()
                beta = 1.0 + (2.0 * (y1 - min_val) / (y2 - y1)) if (y2 - y1) > 1e-9 else 1.0
                alpha = 2.0 - beta**-(ETA_C + 1.0)
                beta_q = (u * alpha)**(1.0 / (ETA_C + 1.0)) if u <= 1.0 / alpha else (1.0 / (2.0 - u * alpha))**(1.0 / (ETA_C + 1.0))
                c1 = 0.5 * ((y1 + y2) - beta_q * (y2 - y1))
                
                beta = 1.0 + (2.0 * (max_val - y2) / (y2 - y1)) if (y2 - y1) > 1e-9 else 1.0
                alpha = 2.0 - beta**-(ETA_C + 1.0)
                beta_q = (u * alpha)**(1.0 / (ETA_C + 1.0)) if u <= 1.0 / alpha else (1.0 / (2.0 - u * alpha))**(1.0 / (ETA_C + 1.0))
                c2 = 0.5 * ((y1 + y2) + beta_q * (y2 - y1))
                
                c1 = min(max(c1, min_val), max_val)
                c2 = min(max(c2, min_val), max_val)
                
                if random.random() <= 0.5:
                    child1[key], child2[key] = c2, c1
                else:
                    child1[key], child2[key] = c1, c2
    return child1, child2

def polynomial_mutation(individual, param_ranges, mutation_rate=None):
    """다항 변이 연산자"""
    if mutation_rate is None:
        mutation_rate = BASE_MUTATION_RATE

    mutated = individual.copy()
    num_params = len(param_ranges)
    
    for key in param_ranges:
        if random.random() < mutation_rate / num_params: 
            y = mutated[key]
            min_val, max_val = param_ranges[key]
            
            if abs(max_val - min_val) < 1e-9: continue

            delta1 = (y - min_val) / (max_val - min_val)
            delta2 = (max_val - y) / (max_val - min_val)
            u = random.random()
            
            mut_pow = 1.0 / (ETA_M + 1.0)
            if u <= 0.5:
                xy = 1.0 - delta1
                val = 2.0 * u + (1.0 - 2.0 * u) * (xy**(ETA_M + 1.0))
                delta_q = val**mut_pow - 1.0
            else:
                xy = 1.0 - delta2
                val = 2.0 * (1.0 - u) + 2.0 * (u - 0.5) * (xy**(ETA_M + 1.0))
                delta_q = 1.0 - val**mut_pow

            y += delta_q * (max_val - min_val)
            y = min(max(y, min_val), max_val)
            mutated[key] = y
    return mutated

def create_target_data_if_not_exists():
    """목표 데이터 파일이 없으면 예제 파일을 생성합니다."""
    filename = 'target_data.csv'
    if not os.path.exists(filename):
        print(f"Warning: '{filename}' not found. Creating a sample target file.")
        ticks = np.arange(1, 501)
        producer_pop = 5000 * np.exp(-ticks / 250) + np.random.normal(0, 100, 500)
        herbivore_pop = 1000 + 800 * np.sin(ticks / 80) * np.exp(-ticks/400) + np.random.normal(0, 50, 500)
        apex_pop = 50 + np.random.normal(0, 5, 500)
        
        df = pd.DataFrame({
            'Tick': ticks,
            'ID_0_Pop_(Producer)': np.maximum(0, producer_pop).astype(int),
            'ID_3_Pop_(Consumer)': np.maximum(0, herbivore_pop).astype(int),
            'ID_5_Pop_(GeneticEngine)': np.maximum(0, apex_pop).astype(int),
        })
        df.to_csv(filename, index=False)
        print(f"Sample '{filename}' created.")