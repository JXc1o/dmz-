# ecological_role.py

class EcologicalRole:
    """모든 생태학적 역할의 기반이 되는 부모 클래스입니다."""
    def __init__(self, species_id, status, initial_population, params):
        self.id = species_id
        self.status = status
        self.population = float(initial_population)
        self.params = params

    def update_population(self, delta):
        """계산된 변화량을 현재 개체수에 적용합니다."""
        self.population += delta
        if self.population < 1:  # 개체수가 1 미만이면 멸종으로 간주
            self.population = 0
            
    def calculate_deaths(self):
        """자연 사망으로 인한 개체수 감소량을 계산합니다."""
        # Consumer, Decomposer는 이미 delta 계산에 death_rate가 포함되어 있지만,
        # 사체 총량(dead_matter_pool) 계산을 위해 별도 메서드로 분리하는 것이 명확함
        death_rate = self.params.get('death_rate', 0.1)
        return self.population * death_rate