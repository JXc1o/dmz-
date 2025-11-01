# interaction_engine.py (단순 개체 수 비례 포식 모델 적용)
"""
생태계 상호작용 해결사 (Ecosystem Interaction Resolver)
"""

def _get_total_population_by_status(manager, target_status):
    total_pop = 0
    for species in manager.species_by_id.values():
        if species.status.startswith(target_status):
            pop = len(species.population) if hasattr(species, 'population') and isinstance(species.population, list) else species.population
            total_pop += pop
    return total_pop

def resolve_interactions(manager, environment, config):
    results = {'deltas': {}, 'genetic_species_energy_gain': {}}
    
    producer_pop = _get_total_population_by_status(manager, '2')
    primary_consumer_pop = _get_total_population_by_status(manager, '3-1')
    apex_predator_pop = _get_total_population_by_status(manager, '3-3') 
    
    # --- 1. 생산자 상호작용 계산 ---
    for species in manager.species_by_id.values():
        if species.status.startswith('2'):
            delta = species.calculate_delta(
                temperature=environment['temperature'],
                consumer_population=primary_consumer_pop,
                total_producer_population=producer_pop 
            )
            results['deltas'][species.id] = delta

    # --- 2. 소비자 상호작용 계산 ---
    total_consumed_by_apex = 0
    handling_time = config.get('interaction_settings', {}).get('predator_handling_time', 0.01)
    for species in manager.species_by_id.values():
        if species.status.startswith('3-1'):
            # [핵심 수정] 가장 단순한 개체 수 비례 포식 모델로 변경
            # 복잡한 밀도 효과를 제거하여 안정성 확보
            eaten_rate = species.params.get('eaten_rate', 0.0)
            functional_response = eaten_rate * apex_predator_pop
            if handling_time > 0:
                functional_response = (eaten_rate * apex_predator_pop) / (1.0 + handling_time * eaten_rate * apex_predator_pop)
            predation_loss = functional_response * species.population
            
            base_delta = species.calculate_delta(producer_population=producer_pop)
            results['deltas'][species.id] = base_delta - predation_loss
            total_consumed_by_apex += predation_loss

    # --- 3. 최상위 포식자(유전 엔진) 에너지 획득 ---
    interaction_settings = config.get('interaction_settings', {})
    energy_conversion_efficiency = interaction_settings.get('energy_conversion_efficiency', 0.2)
    prey_energy = interaction_settings.get('prey_energy_content', 100.0)
    total_energy_gain = total_consumed_by_apex * energy_conversion_efficiency * prey_energy
    max_energy_per_predator = interaction_settings.get('max_energy_per_predator', 400.0)
    if apex_predator_pop > 0 and max_energy_per_predator > 0:
        total_energy_gain = min(total_energy_gain, apex_predator_pop * max_energy_per_predator)
    
    for species in manager.species_by_id.values():
        if species.status.startswith('3-3'):
            results['genetic_species_energy_gain'][species.id] = total_energy_gain

    return results