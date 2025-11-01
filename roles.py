# roles.py

from slim_core_traits import TRAIT_DICT_BY_GID

class Species:
    """
    SLiM Core Trait 라이브러리를 기반으로 하는 종을 정의하는 클래스.
    각 개체는 GID(Global ID)로 식별되는 특성(trait) 값들의 집합을 가집니다.
    """
    def __init__(self, name: str, role: str, traits: dict):
        """
        Args:
            name (str): 종의 이름 (예: "사슴").
            role (str): 생태계에서의 역할 (예: "Primary Consumer").
            traits (dict): 특성 GID를 키로, 특성 값을 값으로 갖는 딕셔너리.
                           {'1': 150.0, '2': 5.0, ...}
        """
        self.name = name
        self.role = role
        # JSON에서 로드할 때 키가 문자열이므로, 정수형 GID로 변환하여 저장합니다.
        self.traits = {int(k): v for k, v in traits.items()}
        print(f"INFO: 종 '{self.name}'({self.role}) 객체가 생성되었습니다.")

    def get_trait_value(self, gid: int, default=None) -> float:
        """
        주어진 GID에 해당하는 특성 값을 반환합니다.
        만약 해당 GID가 종의 특성에 정의되어 있지 않으면,
        기본값을 반환하거나 SLiM 라이브러리의 기본 범위의 중간값을 반환합니다.

        Args:
            gid (int): 조회할 특성의 Global ID.
            default (float, optional): 해당 GID가 없을 때 반환할 기본값.

        Returns:
            float: 특성 값.
        """
        value = self.traits.get(gid)
        if value is not None:
            return value
        
        if default is not None:
            return default

        # 기본값도 없고 종의 특성에도 없는 경우, 라이브러리에서 찾아 기본값을 추정
        if gid in TRAIT_DICT_BY_GID:
            trait_info = TRAIT_DICT_BY_GID[gid]
            value_range = trait_info.get('value_range', (0, 0))
            # 범위의 중간값을 기본값으로 사용
            return (value_range[0] + value_range[1]) / 2.0
        
        # 라이브러리에도 없는 GID인 경우
        print(f"WARNING: GID {gid}를 찾을 수 없습니다. 0.0을 반환합니다.")
        return 0.0

def create_species_from_data(name: str, role: str, traits: dict) -> Species:
    """
    딕셔너리 데이터로부터 Species 객체를 생성하는 팩토리 함수.
    main_calculator.py에서 사용됩니다.
    """
    return Species(name, role, traits)

def get_default_deer_data() -> dict:
    """
    deer.json 파일을 찾지 못했을 때 사용할 기본 사슴 데이터.
    main_calculator.py에서 사용됩니다.
    """
    print("INFO: 기본 사슴 데이터를 생성합니다.")
    return {
        "name": "기본 사슴",
        "role": "Primary Consumer",
        "traits": {
            # Life History
            "1": 15.0,   # 기대 수명 (15년)
            "2": 2.0,    # 성적 성숙 (2년)
            "3": 10.0,   # 번식 가능 수명 (10년)
            "4": 0.1,    # 노화 속도
            "5": 1.2,    # 평균 자손 수 (1.2마리)
            "9": 0.05,   # 나이에 따른 산자수 감소율
            "20": 1.5,   # 자원 풍족도에 따른 산자수 가변성
            # Environmental Resistance
            "32": 0.6,   # 고온 저항성
            "33": 0.8,   # 저온 저항성
            # Viability
            "38": 0.7,   # 기아 저항성
            # Foraging
            "46": 1.2,   # 먹이 탐색 효율
            "48": 1.1    # 먹이 처리 효율
        }
    }