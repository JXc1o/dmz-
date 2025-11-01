# consumer.py (로지스틱 성장 모델 적용)

from ecological_role import EcologicalRole

DEFAULT_PARAMS = {
    'reproduction_rate': 0.2,
    'satiation_threshold': 10,
    'death_rate': 0.2,
    'overcrowding_factor': 0.001 
}

class Consumer(EcologicalRole):
    """소비자 클래스 (생산자를 섭취하여 성장)"""
    def __init__(self, species_id, status, initial_population, params=None):
        if params is None:
            params = DEFAULT_PARAMS
        super().__init__(species_id, status, initial_population, params)

    def calculate_delta(self, producer_population):
        """
        [핵심 수정] '1인당 자원'에 기반한 로지스틱 성장 모델을 적용합니다.
        - reproduction_rate: 자원이 무한할 때의 최대 번식률
        - satiation_threshold: 번식률이 최대치에 도달하는 데 필요한 '1인당 생산자 수'
        """
        # 1. 1인당 자원(생산자)의 양을 계산합니다.
        # 소비자가 0마리일 경우 0으로 나눠지는 것을 방지합니다.
        producers_per_capita = producer_population / self.population if self.population > 0 else 0
        
        # 2. 1인당 자원에 기반하여 성장률 계수(0~1)를 계산합니다.
        # 1인당 자원이 '포만감 한계(satiation_threshold)'에 도달하면 성장률이 1(최대)이 됩니다.
        # 그 전까지는 자원의 양에 비례하여 성장률이 증가합니다.
        satiation_threshold = self.params.get('satiation_threshold', 10)
        growth_factor = min(1.0, producers_per_capita / satiation_threshold)
        
        # 3. 최종 성장량을 계산합니다.
        # (최대 번식률 * 현재 개체 수)에 성장률 계수를 곱합니다.
        reproduction_rate = self.params.get('reproduction_rate', 0.2)
        growth = reproduction_rate * self.population * growth_factor
        
        # 4. 사망 요인을 계산합니다.
        natural_death = self.params.get('death_rate', 0.2) * self.population
        overcrowding_death = self.params.get('overcrowding_factor', 0.001) * self.population * self.population
        
        return growth - natural_death - overcrowding_death