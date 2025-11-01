# producer.py (로지스틱 성장 모델 적용)

from ecological_role import EcologicalRole

DEFAULT_PARAMS = {
    'growth_rate': 0.2,
    'temp_optimum': 20.0,
    'temp_tolerance': 10.0,
    'carrying_capacity': 100000.0, # 환경 수용력
    'eaten_rate': 0.0002,
    'death_rate': 0.1
}

class Producer(EcologicalRole):
    """생산자 클래스 (온도와 환경수용력에 기반한 로지스틱 성장)"""
    def __init__(self, species_id, status, initial_population, params=None):
        if params is None:
            params = DEFAULT_PARAMS
        super().__init__(species_id, status, initial_population, params)

    def calculate_delta(self, temperature, consumer_population, total_producer_population):
        """
        [핵심 수정] 영양소 개념을 제거하고, 로지스틱 성장 모델을 적용합니다.
        """
        # 1. 온도에 따른 성장 효과 계산 (0~1)
        temp_effect = self._calculate_temperature_effect(temperature)
        
        # 2. 로지스틱 성장 항 계산 (밀도 의존적 효과)
        # carrying_capacity는 이 종 하나가 아닌, 전체 생산자 군집에 대한 값으로 해석
        capacity = self.params.get('carrying_capacity', 100000.0)
        logistic_factor = max(0, 1 - (total_producer_population / capacity))
        
        # 3. 최종 성장량 계산
        growth = self.params['growth_rate'] * self.population * temp_effect * logistic_factor
        
        # 4. 손실 요인 계산
        predation_loss = self.params['eaten_rate'] * self.population * consumer_population
        natural_death = self.params.get('death_rate', 0.1) * self.population
        
        return growth - predation_loss - natural_death

    def _calculate_temperature_effect(self, current_temp):
        opt = self.params['temp_optimum']
        tol = self.params['temp_tolerance']
        temp_diff = abs(current_temp - opt)
        if temp_diff > tol: return 0
        return max(0, 1 - (temp_diff / tol)**2)