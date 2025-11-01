# species_generator.py (사냥 비율 하향 조정)
import random
import numpy as np

SPECIES_ARCHETYPES = {
    'photosynthetic_autotroph': {
        'role_class': 'Producer',
        'status_prefix': '2',
        'base_pop': (30000, 60000),
        'param_ranges': {
            'growth_rate': (0.8, 1.5),
            'temp_optimum': (10.0, 25.0),
            'temp_tolerance': (5.0, 15.0),
            'carrying_capacity': (80000.0, 150000.0),
            # [핵심 수정] 초식동물이 생산자를 먹는 비율을 약 4-5배 낮춥니다.
            'eaten_rate': (0.00001, 0.00005),
            'death_rate': (0.1, 0.2)
        }
    },
    'primary_consumer_herbivore': {
        'role_class': 'Consumer',
        'status_prefix': '3-1',
        'base_pop': (100, 200),
        'param_ranges': {
            'reproduction_rate': (0.2, 0.4),
            'satiation_threshold': (80, 150),
            'death_rate': (0.1, 0.3),
            # [핵심 수정] 최상위 포식자가 초식동물을 먹는 비율을 약 5배 낮춥니다.
            'eaten_rate': (0.00002, 0.0001),
            'overcrowding_factor': (0.00001, 0.00005)
        }
    },
    'tertiary_consumer_apex': {
        'role_class': 'GeneticEngine',
        'status_prefix': '3-3',
        'base_pop': (10, 20),
        'param_ranges': {}
    }
}

def _resolve_fixed_value(value, index):
    if isinstance(value, list):
        if not value:
            return None
        idx = min(index, len(value) - 1)
        return value[idx]
    return value


def generate_species_from_archetypes(ecosystem_setup, genetic_engine_params=None, species_fixed_params=None):
    """(GUI 등에서 사용하는 기본 종 생성기)"""
    species_list = []
    species_id_counter = 0
    fixed_params = species_fixed_params or {}
    for archetype_name, count in ecosystem_setup.items():
        if archetype_name not in SPECIES_ARCHETYPES: continue
        archetype = SPECIES_ARCHETYPES[archetype_name]
        fixed_for_archetype = fixed_params.get(archetype_name, {})
        for i in range(count):
            initial_population = random.randint(*archetype['base_pop'])
            pop_override = _resolve_fixed_value(fixed_for_archetype.get('initial_population'), i)
            if pop_override is not None:
                initial_population = max(1, int(pop_override))
            species_data = {
                'id': species_id_counter, 'type': archetype['role_class'],
                'status': f"{archetype['status_prefix']}-{i+1}",
                'initial_population': initial_population,
                'params': {}
            }
            for param_name, value_range in archetype['param_ranges'].items():
                override = _resolve_fixed_value(fixed_for_archetype.get(param_name), i)
                if override is not None:
                    species_data['params'][param_name] = float(override)
                else:
                    species_data['params'][param_name] = random.uniform(*value_range)
            if archetype['role_class'] == 'GeneticEngine' and genetic_engine_params:
                species_data['mutation_rate'] = genetic_engine_params.get('mutation_rate', 0.1)
                species_data['mutation_strength'] = genetic_engine_params.get('mutation_strength', 0.05)
            species_list.append(species_data)
            species_id_counter += 1
    return species_list

def generate_scientifically_balanced_ecosystem(ecosystem_setup, config):
    """(main_robust_runner.py 전용)"""
    print("--- Enforcing extreme biomass pyramid ratio (several hundred to one) ---")
    species_list = generate_species_from_archetypes(
        ecosystem_setup,
        config.get('genetic_engine_params'),
        config.get('species_fixed_params')
    )
    producers = [s for s in species_list if s['type'] == 'Producer']
    if not producers: raise ValueError("Ecosystem must have producers.")
    total_producer_pop = sum(p['initial_population'] for p in producers)
    consumers = [s for s in species_list if s['type'] == 'Consumer']
    if consumers:
        ratio = random.uniform(0.0025, 0.005)
        total_consumer_pop = max(len(consumers) * 10, int(total_producer_pop * ratio))
        _distribute_population(consumers, total_consumer_pop)
        print(f"Total Producer Pop: {total_producer_pop} -> Total Consumer Pop set to: {total_consumer_pop} (Ratio ~{1/ratio:.1f}:1)")
    apex_predators = [s for s in species_list if s['type'] == 'GeneticEngine']
    if apex_predators:
        consumer_pop_for_apex = sum(c['initial_population'] for c in consumers)
        ratio = random.uniform(0.04, 0.08)
        total_apex_pop = max(len(apex_predators), int(consumer_pop_for_apex * ratio))
        _distribute_population(apex_predators, total_apex_pop)
        print(f"Total Consumer Pop: {consumer_pop_for_apex} -> Total Apex Predator Pop set to: {total_apex_pop}")
    print("--- Ecosystem tuning complete ---")
    return species_list

def _distribute_population(species_group, total_population):
    """총 개체 수를 해당 그룹의 종들에게 자연스럽게 분배합니다."""
    if not species_group: return
    num_species = len(species_group)
    if num_species == 1:
        species_group[0]['initial_population'] = max(1, total_population)
        return
    proportions = np.random.dirichlet(np.ones(num_species), size=1)[0]
    for i, species in enumerate(species_group):
        species['initial_population'] = max(1, int(total_population * proportions[i]))

def generate_ideal_ecosystem_request():
    """(main_robust_runner.py에서 사용하는 기본 생태계 구성 요청)"""
    return {
        'photosynthetic_autotroph': 3,
        'primary_consumer_herbivore': 2,
        'tertiary_consumer_apex': 1
    }