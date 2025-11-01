# slim_core_traits.py
"""
SLiM Core Trait Library (100 Traits)
- 시뮬레이션의 모든 생물학적 규칙과 계산 함수를 정의하는 핵심 라이브러리입니다.
- 이 파일은 다른 파일에서 import하여 사용하며, 직접 수정할 필요가 없습니다.
"""

# ==============================================================================
# 1. TRAIT DATA DEFINITIONS
# ==============================================================================

TRAIT_LIBRARY = [
    # --- Category 1: Life History & Fecundity (gid 1-20) ---
    {'gid': 1, 'category': 'Life History', 'description': '기대 수명 (Longevity).', 'value_type': 'float', 'value_range': (1.0, 1000.0)},
    {'gid': 2, 'category': 'Life History', 'description': '성적 성숙까지의 시간 (Age of Maturity).', 'value_type': 'float', 'value_range': (1, 500)},
    {'gid': 3, 'category': 'Life History', 'description': '번식 가능 수명 (Reproductive Lifespan).', 'value_type': 'float', 'value_range': (1, 1000)},
    {'gid': 4, 'category': 'Life History', 'description': '노화 속도 (Aging Rate).', 'value_type': 'float', 'value_range': (0.01, 1.0)},
    {'gid': 5, 'category': 'Fecundity', 'description': '한 배의 평균 자손 수 (Clutch Size / Fecundity).', 'value_type': 'float', 'value_range': (1, 1000)},
    {'gid': 6, 'category': 'Fecundity', 'description': '연간 번식 가능 횟수 (Breeding Frequency).', 'value_type': 'float', 'value_range': (0.1, 50.0)},
    {'gid': 7, 'category': 'Fecundity', 'description': '번식 간 최소 회복 시간 (Breeding Interval).', 'value_type': 'float', 'value_range': (1, 500)},
    {'gid': 8, 'category': 'Fecundity', 'description': '첫 번식 시 산자수 보너스/패널티.', 'value_type': 'float', 'value_range': (0.5, 1.5)},
    {'gid': 9, 'category': 'Fecundity', 'description': '나이에 따른 산자수 감소율.', 'value_type': 'float', 'value_range': (0.0, 0.5)},
    {'gid': 10, 'category': 'Offspring Viability', 'description': '초기 자손 생존율 (Initial Offspring Survival).', 'value_type': 'float', 'value_range': (0.01, 1.0)},
    {'gid': 11, 'category': 'Offspring Viability', 'description': '부모의 양육 투자 수준 (Parental Care Investment).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 12, 'category': 'Offspring Viability', 'description': '알/새끼의 포식 저항성.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 13, 'category': 'Offspring Viability', 'description': '자손에게 전달되는 초기 에너지량.', 'value_type': 'float', 'value_range': (1.0, 100.0)},
    {'gid': 14, 'category': 'Offspring Viability', 'description': '자손의 초기 질병 저항성.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 15, 'category': 'Reproductive Strategy', 'description': 'r/K 생존 전략 지수 (0:r, 1:K).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 16, 'category': 'Reproductive Strategy', 'description': '단성생식 성공률.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 17, 'category': 'Reproductive Strategy', 'description': '성비 조절 능력 (0=아들, 1=딸).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 18, 'category': 'Reproductive Strategy', 'description': '번식에 필요한 최소 신체 조건.', 'value_type': 'float', 'value_range': (0.5, 1.5)},
    {'gid': 19, 'category': 'Life History', 'description': '부상으로부터의 회복력.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 20, 'category': 'Fecundity', 'description': '자원 풍족도에 따른 산자수 가변성.', 'value_type': 'float', 'value_range': (0.1, 2.0)},

    # --- Category 2: Viability & Defense (gid 21-45) ---
    {'gid': 21, 'category': 'Defense', 'description': '물리적 방어력 (Physical Defense).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 22, 'category': 'Defense', 'description': '위장 효과 (Camouflage Efficiency).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 23, 'category': 'Defense', 'description': '포식자 회피 행동 효율 (Predator Avoidance).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 24, 'category': 'Defense', 'description': '경계 행동 수준 (Vigilance Level).', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 25, 'category': 'Defense', 'description': '화학적 방어력 (독성/악취).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 26, 'category': 'Defense', 'description': '무리 방어 효과 (Group Defense Bonus).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 27, 'category': 'Disease Resistance', 'description': '일반 병원체 저항성 (General Disease Resistance).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 28, 'category': 'Disease Resistance', 'description': '특정 바이러스 저항성.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 29, 'category': 'Disease Resistance', 'description': '특정 세균 저항성.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 30, 'category': 'Disease Resistance', 'description': '기생충 저항성.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 31, 'category': 'Disease Resistance', 'description': '감염 후 회복률.', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 32, 'category': 'Environmental Resistance', 'description': '고온 스트레스 저항성 (Heat Resistance).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 33, 'category': 'Environmental Resistance', 'description': '저온 스트레스 저항성 (Cold Resistance).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 34, 'category': 'Environmental Resistance', 'description': '건조 스트레스 저항성 (Drought Resistance).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 35, 'category': 'Environmental Resistance', 'description': '염분 스트레스 저항성 (Salinity Resistance).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 36, 'category': 'Environmental Resistance', 'description': '저산소 저항성 (Hypoxia Resistance).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 37, 'category': 'Environmental Resistance', 'description': '환경 독소 저항성 (Toxin Resistance).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 38, 'category': 'Viability', 'description': '기아 저항성 (Starvation Resistance).', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 39, 'category': 'Viability', 'description': '스트레스에 대한 전반적인 회복력.', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 40, 'category': 'Defense', 'description': '의태(Mimicry)로 인한 포식 회피율.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 41, 'category': 'Disease Resistance', 'description': '면역 반응으로 인한 피트니스 비용.', 'value_type': 'float', 'value_range': (0.0, 0.5)},
    {'gid': 42, 'category': 'Environmental Resistance', 'description': '자외선(UV) 저항성.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 43, 'category': 'Viability', 'description': '사고/재해에 대한 생존율.', 'value_type': 'float', 'value_range': (0.01, 1.0)},
    {'gid': 44, 'category': 'Defense', 'description': '경계 행동 시 포식자 탐지 확률.', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 45, 'category': 'Defense', 'description': '도주 성공률.', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    
    # --- Category 3: Resource Competition & Foraging (gid 46-65) ---
    {'gid': 46, 'category': 'Foraging', 'description': '먹이 탐색 효율 (Foraging Efficiency).', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 47, 'category': 'Foraging', 'description': '자원 탐지 거리.', 'value_type': 'float', 'value_range': (1.0, 1000.0)},
    {'gid': 48, 'category': 'Foraging', 'description': '먹이 처리 효율 (Handling Efficiency).', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 49, 'category': 'Foraging', 'description': '먹이 선택의 폭 (Diet Breadth).', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 50, 'category': 'Foraging', 'description': '고위험-고수익 먹이 선호도.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 51, 'category': 'Competition', 'description': '경쟁 우위 (Competitive Ability).', 'value_type': 'float', 'value_range': (0.1, 5.0)},
    {'gid': 52, 'category': 'Competition', 'description': '자원 방어 능력.', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 53, 'category': 'Competition', 'description': '공격성 (Aggressiveness).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 54, 'category': 'Competition', 'description': '밀도 의존적 피트니스 감소 민감도.', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 55, 'category': 'Metabolism', 'description': '대사 효율 (Metabolic Efficiency).', 'value_type': 'float', 'value_range': (0.5, 1.5)},
    {'gid': 56, 'category': 'Metabolism', 'description': '에너지 저장 능력.', 'value_type': 'float', 'value_range': (1.0, 1000.0)},
    {'gid': 57, 'category': 'Territoriality', 'description': '필요 세력권 크기 (Territory Size).', 'value_type': 'float', 'value_range': (1.0, 10000.0)},
    {'gid': 58, 'category': 'Territoriality', 'description': '세력권 방어 성공률.', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 59, 'category': 'Foraging', 'description': '탐색 중 포식 위험 감수 수준.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 60, 'category': 'Foraging', 'description': '사회적 학습을 통한 먹이 탐색 능력.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 61, 'category': 'Competition', 'description': '경쟁자 회피 능력.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 62, 'category': 'Competition', 'description': '착취적 경쟁 능력 (자원 선점).', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 63, 'category': 'Competition', 'description': '간섭 경쟁 능력 (직접 방해).', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 64, 'category': 'Metabolism', 'description': '특정 희귀 자원 활용 능력.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 65, 'category': 'Foraging', 'description': '기억력 기반 먹이 재탐색 성공률.', 'value_type': 'float', 'value_range': (0.0, 1.0)},

    # --- Category 4: Mating & Sexual Selection (gid 66-80) ---
    {'gid': 66, 'category': 'Sexual Selection', 'description': '성적 매력도 (Attractiveness).', 'value_type': 'float', 'value_range': (0.1, 5.0)},
    {'gid': 67, 'category': 'Sexual Selection', 'description': '구애 행동의 복잡성/효율성.', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 68, 'category': 'Sexual Selection', 'description': '성적 장식의 크기/화려함.', 'value_type': 'float', 'value_range': (0.1, 10.0)},
    {'gid': 69, 'category': 'Mating', 'description': '짝짓기 경쟁에서의 우위.', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 70, 'category': 'Mating', 'description': '배우자 탐색 효율.', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 71, 'category': 'Mating', 'description': '배우자 선택의 까다로움 (Mate Choice Selectivity).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 72, 'category': 'Mating', 'description': '수정 성공률.', 'value_type': 'float', 'value_range': (0.5, 1.0)},
    {'gid': 73, 'category': 'Mating', 'description': '정자/난자 경쟁력.', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 74, 'category': 'Mating', 'description': '짝짓기 후 배우자 지키기(Mate Guarding) 강도.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 75, 'category': 'Mating', 'description': '근친 교배 회피 경향.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 76, 'category': 'Sexual Selection', 'description': '성적 장식 유지 비용.', 'value_type': 'float', 'value_range': (0.0, 0.5)},
    {'gid': 77, 'category': 'Mating', 'description': '여러 상대와의 짝짓기 경향 (Polygamy).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 78, 'category': 'Mating', 'description': '구애 행동 시 에너지 소모.', 'value_type': 'float', 'value_range': (1.0, 100.0)},
    {'gid': 79, 'category': 'Sexual Selection', 'description': '성적 이형성 정도 (Sexual Dimorphism).', 'value_type': 'float', 'value_range': (1.0, 5.0)},
    {'gid': 80, 'category': 'Mating', 'description': '번식지(nesting site) 확보 능력.', 'value_type': 'float', 'value_range': (0.1, 1.0)},

    # --- Category 5: Morphology & Performance (gid 81-100) ---
    {'gid': 81, 'category': 'Morphology', 'description': '성체 체질량 (Body Size).', 'value_type': 'float', 'value_range': (0.1, 1000.0)},
    {'gid': 82, 'category': 'Morphology', 'description': '무기(뿔, 발톱 등)의 크기/효율.', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 83, 'category': 'Morphology', 'description': '은폐/보호색의 효과.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 84, 'category': 'Performance', 'description': '최대 이동 속도 (Maximum Speed).', 'value_type': 'float', 'value_range': (1, 100)},
    {'gid': 85, 'category': 'Performance', 'description': '지구력 (Stamina).', 'value_type': 'float', 'value_range': (1, 100)},
    {'gid': 86, 'category': 'Performance', 'description': '근력 (Strength).', 'value_type': 'float', 'value_range': (1, 100)},
    {'gid': 87, 'category': 'Performance', 'description': '민첩성 (Agility).', 'value_type': 'float', 'value_range': (1, 100)},
    {'gid': 88, 'category': 'Performance', 'description': '비행/수영 효율.', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 89, 'category': 'Sensory', 'description': '시각 능력 (탐지 거리/정확도).', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 90, 'category': 'Sensory', 'description': '청각 능력 (탐지 거리/정확도).', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 91, 'category': 'Sensory', 'description': '후각 능력 (탐지 거리/정확도).', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 92, 'category': 'Dispersal', 'description': '분산 능력 (Dispersal Ability).', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 93, 'category': 'Dispersal', 'description': '분산 시 사망률.', 'value_type': 'float', 'value_range': (0.0, 1.0)},
    {'gid': 94, 'category': 'Dispersal', 'description': '정착지 선택 능력.', 'value_type': 'float', 'value_range': (0.1, 1.0)},
    {'gid': 95, 'category': 'Morphology', 'description': '체지방률.', 'value_type': 'float', 'value_range': (0.01, 0.7)},
    {'gid': 96, 'category': 'Performance', 'description': '점프/도약 능력.', 'value_type': 'float', 'value_range': (0.1, 10.0)},
    {'gid': 97, 'category': 'Morphology', 'description': '몸의 유연성.', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 98, 'category': 'Performance', 'description': '가속도.', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 99, 'category': 'Sensory', 'description': '야간 시야 능력.', 'value_type': 'float', 'value_range': (0.1, 2.0)},
    {'gid': 100, 'category': 'Dispersal', 'description': '새로운 환경 적응력.', 'value_type': 'float', 'value_range': (0.1, 1.0)},
]
TRAIT_DICT_BY_GID = {trait['gid']: trait for trait in TRAIT_LIBRARY}

# ==============================================================================
# 2. TRAIT FUNCTION DEFINITIONS
# ==============================================================================
def calculate_trait_1(value: float) -> float: return value
def calculate_trait_2(value: float) -> float: return value
def calculate_trait_3(value: float) -> float: return value
def calculate_trait_4(value: float, base_viability_decline: float) -> float: return base_viability_decline * value
def calculate_trait_5(value: float) -> float: return value
def calculate_trait_6(value: float) -> float: return value
def calculate_trait_7(value: float) -> float: return value
def calculate_trait_8(value: float, base_fecundity: float) -> float: return base_fecundity * value
def calculate_trait_9(value: float, initial_fecundity: float) -> float: return initial_fecundity * (1.0 - value)
def calculate_trait_10(value: float, base_survival: float = 1.0) -> float: return base_survival * value
def calculate_trait_11(value: float, base_offspring_survival: float) -> float: return base_offspring_survival * (1.0 + value)
def calculate_trait_12(value: float, predation_risk: float) -> float: return predation_risk * (1.0 - value)
def calculate_trait_13(value: float) -> float: return value
def calculate_trait_14(value: float, infection_risk: float) -> float: return infection_risk * (1.0 - value)
def calculate_trait_15(value: float) -> float: return value
def calculate_trait_16(value: float, base_reproduction_chance: float) -> float: return base_reproduction_chance * value
def calculate_trait_17(value: float) -> float: return value
def calculate_trait_18(value: float) -> float: return value
def calculate_trait_19(value: float, base_recovery_rate: float) -> float: return base_recovery_rate * value
def calculate_trait_20(value: float, base_fecundity: float) -> float: return base_fecundity * value
def calculate_trait_21(value: float, initial_damage: float) -> float: return initial_damage * (1.0 - value)
def calculate_trait_22(value: float, detection_chance: float) -> float: return detection_chance * (1.0 - value)
def calculate_trait_23(value: float, encounter_rate: float) -> float: return encounter_rate * (1.0 - value)
def calculate_trait_24(value: float, base_detection_chance: float) -> float: return base_detection_chance * value
def calculate_trait_25(value: float, predation_attempt_rate: float) -> float: return predation_attempt_rate * (1.0 - value)
def calculate_trait_26(value: float, individual_survival_chance: float) -> float: return individual_survival_chance + (1.0 - individual_survival_chance) * value
def calculate_trait_27(value: float, infection_risk: float) -> float: return infection_risk * (1.0 - value)
def calculate_trait_28(value: float, virus_infection_risk: float) -> float: return virus_infection_risk * (1.0 - value)
def calculate_trait_29(value: float, bacteria_infection_risk: float) -> float: return bacteria_infection_risk * (1.0 - value)
def calculate_trait_30(value: float, parasite_infection_risk: float) -> float: return parasite_infection_risk * (1.0 - value)
def calculate_trait_31(value: float, base_recovery_rate: float) -> float: return base_recovery_rate * value
def calculate_trait_32(value: float, heat_stress_damage: float) -> float: return heat_stress_damage * (1.0 - value)
def calculate_trait_33(value: float, cold_stress_damage: float) -> float: return cold_stress_damage * (1.0 - value)
def calculate_trait_34(value: float, dehydration_damage: float) -> float: return dehydration_damage * (1.0 - value)
def calculate_trait_35(value: float, osmotic_damage: float) -> float: return osmotic_damage * (1.0 - value)
def calculate_trait_36(value: float, hypoxia_damage: float) -> float: return hypoxia_damage * (1.0 - value)
def calculate_trait_37(value: float, toxin_damage: float) -> float: return toxin_damage * (1.0 - value)
def calculate_trait_38(value: float, base_starvation_rate: float) -> float: return base_starvation_rate * (1.0 - value)
def calculate_trait_39(value: float, base_recovery_rate: float) -> float: return base_recovery_rate * value
def calculate_trait_40(value: float, predation_risk: float) -> float: return predation_risk * (1.0 - value)
def calculate_trait_41(value: float, base_fitness: float) -> float: return base_fitness * (1.0 - value)
def calculate_trait_42(value: float, uv_damage: float) -> float: return uv_damage * (1.0 - value)
def calculate_trait_43(value: float, base_survival_chance: float) -> float: return base_survival_chance * value
def calculate_trait_44(value: float, base_detection_chance: float) -> float: return base_detection_chance * value
def calculate_trait_45(value: float, capture_probability: float) -> float: return capture_probability * (1.0 - value)
def calculate_trait_46(value: float, base_resource_gain: float) -> float: return base_resource_gain * value
def calculate_trait_47(value: float) -> float: return value
def calculate_trait_48(value: float, base_energy_gain: float) -> float: return base_energy_gain * value
def calculate_trait_49(value: float) -> float: return value
def calculate_trait_50(value: float, base_preference: float) -> float: return base_preference * value
def calculate_trait_51(value: float, base_win_rate: float = 0.5) -> float: return base_win_rate * value
def calculate_trait_52(value: float, base_defense_success: float) -> float: return base_defense_success * value
def calculate_trait_53(value: float, base_attack_chance: float) -> float: return base_attack_chance * value
def calculate_trait_54(value: float, base_fitness_reduction: float) -> float: return base_fitness_reduction * value
def calculate_trait_55(value: float, base_energy_cost: float) -> float: return base_energy_cost / value
def calculate_trait_56(value: float) -> float: return value
def calculate_trait_57(value: float) -> float: return value
def calculate_trait_58(value: float, base_win_rate: float) -> float: return base_win_rate * value
def calculate_trait_59(value: float, base_risk_rate: float) -> float: return base_risk_rate * value
def calculate_trait_60(value: float, base_learning_rate: float) -> float: return base_learning_rate * value
def calculate_trait_61(value: float, encounter_rate: float) -> float: return encounter_rate * (1.0 - value)
def calculate_trait_62(value: float, base_foraging_rate: float) -> float: return base_foraging_rate * value
def calculate_trait_63(value: float, opponent_foraging_rate: float) -> float: return opponent_foraging_rate * (1.0 - value)
def calculate_trait_64(value: float, base_gain: float) -> float: return base_gain * value
def calculate_trait_65(value: float, base_success_rate: float) -> float: return base_success_rate * value
def calculate_trait_66(value: float, base_mating_success: float) -> float: return base_mating_success * value
def calculate_trait_67(value: float, base_mating_success: float) -> float: return base_mating_success * value
def calculate_trait_68(value: float) -> float: return value
def calculate_trait_69(value: float, base_win_rate: float) -> float: return base_win_rate * value
def calculate_trait_70(value: float, base_search_rate: float) -> float: return base_search_rate * value
def calculate_trait_71(value: float, acceptance_rate: float) -> float: return acceptance_rate * (1.0 - value)
def calculate_trait_72(value: float, base_rate: float) -> float: return base_rate * value
def calculate_trait_73(value: float, base_success_rate: float) -> float: return base_success_rate * value
def calculate_trait_74(value: float, base_success_rate: float) -> float: return base_success_rate * value
def calculate_trait_75(value: float, base_inbreeding_chance: float) -> float: return base_inbreeding_chance * (1.0 - value)
def calculate_trait_76(value: float, base_viability: float) -> float: return base_viability * (1.0 - value)
def calculate_trait_77(value: float) -> float: return value
def calculate_trait_78(value: float) -> float: return value
def calculate_trait_79(value: float) -> float: return value
def calculate_trait_80(value: float, base_success_rate: float) -> float: return base_success_rate * value
def calculate_trait_81(value: float) -> float: return value
def calculate_trait_82(value: float, base_damage: float) -> float: return base_damage * value
def calculate_trait_83(value: float, detection_chance: float) -> float: return detection_chance * (1.0 - value)
def calculate_trait_84(value: float) -> float: return value
def calculate_trait_85(value: float) -> float: return value
def calculate_trait_86(value: float) -> float: return value
def calculate_trait_87(value: float) -> float: return value
def calculate_trait_88(value: float, base_energy_cost: float) -> float: return base_energy_cost / value
def calculate_trait_89(value: float, base_range: float) -> float: return base_range * value
def calculate_trait_90(value: float, base_range: float) -> float: return base_range * value
def calculate_trait_91(value: float, base_range: float) -> float: return base_range * value
def calculate_trait_92(value: float, base_dispersal_chance: float) -> float: return base_dispersal_chance * value
def calculate_trait_93(value: float, base_survival: float) -> float: return base_survival * (1.0 - value)
def calculate_trait_94(value: float, base_success_rate: float) -> float: return base_success_rate * value
def calculate_trait_95(value: float) -> float: return value
def calculate_trait_96(value: float) -> float: return value
def calculate_trait_97(value: float) -> float: return value
def calculate_trait_98(value: float, base_speed: float) -> float: return base_speed * value
def calculate_trait_99(value: float, base_vision: float) -> float: return base_vision * value
def calculate_trait_100(value: float, base_survival_chance: float) -> float: return base_survival_chance * value

# ==============================================================================
# 3. FUNCTION REGISTRY
# ==============================================================================
TRAIT_FUNCTIONS = {
    1: calculate_trait_1, 2: calculate_trait_2, 3: calculate_trait_3, 4: calculate_trait_4, 5: calculate_trait_5,
    6: calculate_trait_6, 7: calculate_trait_7, 8: calculate_trait_8, 9: calculate_trait_9, 10: calculate_trait_10,
    11: calculate_trait_11, 12: calculate_trait_12, 13: calculate_trait_13, 14: calculate_trait_14, 15: calculate_trait_15,
    16: calculate_trait_16, 17: calculate_trait_17, 18: calculate_trait_18, 19: calculate_trait_19, 20: calculate_trait_20,
    21: calculate_trait_21, 22: calculate_trait_22, 23: calculate_trait_23, 24: calculate_trait_24, 25: calculate_trait_25,
    26: calculate_trait_26, 27: calculate_trait_27, 28: calculate_trait_28, 29: calculate_trait_29, 30: calculate_trait_30,
    31: calculate_trait_31, 32: calculate_trait_32, 33: calculate_trait_33, 34: calculate_trait_34, 35: calculate_trait_35,
    36: calculate_trait_36, 37: calculate_trait_37, 38: calculate_trait_38, 39: calculate_trait_39, 40: calculate_trait_40,
    41: calculate_trait_41, 42: calculate_trait_42, 43: calculate_trait_43, 44: calculate_trait_44, 45: calculate_trait_45,
    46: calculate_trait_46, 47: calculate_trait_47, 48: calculate_trait_48, 49: calculate_trait_49, 50: calculate_trait_50,
    51: calculate_trait_51, 52: calculate_trait_52, 53: calculate_trait_53, 54: calculate_trait_54, 55: calculate_trait_55,
    56: calculate_trait_56, 57: calculate_trait_57, 58: calculate_trait_58, 59: calculate_trait_59, 60: calculate_trait_60,
    61: calculate_trait_61, 62: calculate_trait_62, 63: calculate_trait_63, 64: calculate_trait_64, 65: calculate_trait_65,
    66: calculate_trait_66, 67: calculate_trait_67, 68: calculate_trait_68, 69: calculate_trait_69, 70: calculate_trait_70,
    71: calculate_trait_71, 72: calculate_trait_72, 73: calculate_trait_73, 74: calculate_trait_74, 75: calculate_trait_75,
    76: calculate_trait_76, 77: calculate_trait_77, 78: calculate_trait_78, 79: calculate_trait_79, 80: calculate_trait_80,
    81: calculate_trait_81, 82: calculate_trait_82, 83: calculate_trait_83, 84: calculate_trait_84, 85: calculate_trait_85,
    86: calculate_trait_86, 87: calculate_trait_87, 88: calculate_trait_88, 89: calculate_trait_89, 90: calculate_trait_90,
    91: calculate_trait_91, 92: calculate_trait_92, 93: calculate_trait_93, 94: calculate_trait_94, 95: calculate_trait_95,
    96: calculate_trait_96, 97: calculate_trait_97, 98: calculate_trait_98, 99: calculate_trait_99, 100: calculate_trait_100,
}