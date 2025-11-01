# fitness_calculator.py (수정 완료)
import random
import math
import slim_core_traits as sct
from individual import Individual

def calculate_viability(organism: Individual, env: dict) -> float:
    age = organism.age
    longevity = organism.get_trait_value(1, default=15.0)
    aging_rate = organism.get_trait_value(4, default=0.1)
    c = 0.005; a = 0.00005
    b = (5 / longevity * (1 + aging_rate)) if longevity > 0 else 5
    age_based_mortality = c + a * math.exp(b * age)
    viability = 1.0 - age_based_mortality

    T_current = env.get("temperature", 15.0)
    # CHANGED: 하드코딩된 최적 온도를 env에서 받아오도록 수정
    T_opt = env.get("optimal_temperature", 15.0)
    temp_stress = 0.0
    stress_multiplier = 0.1
    
    if T_current > T_opt:
        heat_res = organism.get_trait_value(32, default=0.5)
        stress_raw = 0.001 * (T_current - T_opt)**2
        temp_stress = sct.TRAIT_FUNCTIONS[32](heat_res, stress_raw) * stress_multiplier
    elif T_current < T_opt:
        cold_res = organism.get_trait_value(33, default=0.5)
        stress_raw = 0.002 * (T_opt - T_current)**2
        temp_stress = sct.TRAIT_FUNCTIONS[33](cold_res, stress_raw) * stress_multiplier
    viability -= temp_stress

    prey_availability = env.get("prey_availability", 500)
    energy_cost = 0.8
    
    if organism.energy < energy_cost * 200:
        starvation_res = organism.get_trait_value(38, default=0.5)
        starvation_stress = (1 - (organism.energy / (energy_cost * 200))) * 0.1
        viability -= sct.TRAIT_FUNCTIONS[38](starvation_res, starvation_stress)

    return max(0.0, viability)

# calculate_fecundity 함수는 변경사항 없음 (그대로 유지)
def calculate_fecundity(organism: Individual, env: dict) -> int:
    # ... (기존 코드와 동일) ...
    age = organism.age
    age_of_maturity = organism.get_trait_value(2, default=3.0)
    reproductive_lifespan = organism.get_trait_value(3, default=10.0)
    
    if not (age_of_maturity <= age <= age_of_maturity + reproductive_lifespan):
        return 0

    base_fecundity = organism.get_trait_value(5, default=1.2) * 1.5 
    
    prey_availability = env.get("prey_availability", 500)
    resource_factor = 1 + ((prey_availability / (prey_availability + 1000.0)) - 0.5) * 1.0

    resource_based_fecundity = base_fecundity * resource_factor

    decline_rate = organism.get_trait_value(9, default=0.05)
    age_effect = age - age_of_maturity
    final_fecundity = resource_based_fecundity * max(0, 1 - decline_rate * age_effect)
    
    energy_factor = max(0, (organism.energy - 100) / 100.0)
    final_fecundity *= energy_factor

    num_offspring = int(final_fecundity)
    if random.random() < (final_fecundity % 1):
        num_offspring += 1
        
    return num_offspring