# individual.py (수정 완료)

import random
# 'TRAIT_DICT_BY_GIDA' -> 'TRAIT_DICT_BY_GID'로 오타를 수정했습니다.
from slim_core_traits import TRAIT_DICT_BY_GID

class Individual:
    """
    유전 알고리즘의 개별 단위. 나이(age), 에너지, 유전 정보(genome) 등
    개체의 모든 상태를 관리합니다.
    """
    def __init__(self, species_id, genome=None, initial_energy=100.0):
        self.species_id = species_id
        self.age = 0
        self.fitness = 0.0 # 참고용 또는 다른 용도로 유지
        self.energy = float(initial_energy)
        self.genome = genome
        
        # --- 핵심 수정 사항 ---
        # 생존 확률과 자손 수를 별도로 저장할 속성 추가
        self.viability = 0.0
        self.fecundity = 0
        # --- 수정 끝 ---

        if self.genome is None:
            self.genome = {
                1: random.uniform(10.0, 20.0), 4: random.uniform(0.05, 0.2),
                32: random.uniform(0.0, 1.0), 33: random.uniform(0.0, 1.0),
                38: random.uniform(0.0, 1.0), 46: random.uniform(0.5, 1.5),
                48: random.uniform(0.5, 1.5), 2: random.uniform(2.0, 5.0),
                3: random.uniform(8.0, 15.0), 5: random.uniform(1.0, 2.0),
                9: random.uniform(0.01, 0.1), 20: random.uniform(0.5, 1.5)
            }

    def tick(self):
        """시뮬레이션의 한 틱이 지날 때마다 호출됩니다. 나이를 1 증가시킵니다."""
        self.age += 1

    def get_trait_value(self, gid: int, default=None) -> float:
        """자신의 genome에서 GID에 해당하는 특성 값을 반환합니다."""
        value = self.genome.get(gid)
        if value is not None:
            return value
        if default is not None:
            return default
        if gid in TRAIT_DICT_BY_GID:
            trait_info = TRAIT_DICT_BY_GID[gid]
            value_range = trait_info.get('value_range', (0, 0))
            return (value_range[0] + value_range[1]) / 2.0
        print(f"WARNING: GID {gid}를 찾을 수 없습니다. 0.0을 반환합니다.")
        return 0.0

    def add_energy(self, amount: float):
        self.energy += amount

    def consume_energy(self, amount: float) -> bool:
        self.energy -= amount
        return self.energy > 0