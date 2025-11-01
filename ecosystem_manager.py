# ecosystem_manager.py (Decomposer 관련 코드 완전 제거)

from producer import Producer
from consumer import Consumer
# from decomposer import Decomposer # <-- 이 줄을 삭제했습니다.
from genetic_engine import GeneticEngine
from species_generator import generate_species_from_archetypes
import json

class EcosystemManager:
    """
    ID 코드로 종을 관리하고 역할군을 배정하는 중앙 컨트롤러입니다.
    """
    def __init__(self, species_config_list, config):
        self.species_by_id = {}
        self._build_from_config(species_config_list, config)

    def _build_from_config(self, species_config_list, config):
        for species_data in species_config_list:
            species_id = species_data.get('id')
            species_type = species_data.get('type')
            status = species_data.get('status')

            if species_id is None or not species_type or not status:
                print(f"Warning: Skipping invalid species data: {species_data}")
                continue
            
            if species_type == 'Producer':
                obj = Producer(
                    species_id=species_id, status=status,
                    initial_population=species_data.get('initial_population'),
                    params=species_data.get('params')
                )
            elif species_type == 'Consumer':
                obj = Consumer(
                    species_id=species_id, status=status,
                    initial_population=species_data.get('initial_population'),
                    params=species_data.get('params')
                )
            # [핵심 수정] Decomposer 생성 로직을 완전히 제거했습니다.
            # elif species_type == 'Decomposer':
            #     obj = Decomposer(...)
            elif species_type == 'GeneticEngine':
                genetic_params = config.get('genetic_engine_params', {})
                
                obj = GeneticEngine(
                    species_id=species_id, status=status,
                    population_size=species_data.get('initial_population'),
                    mutation_rate=species_data.get('mutation_rate'),
                    mutation_strength=species_data.get('mutation_strength'),
                    params=genetic_params
                )
            else:
                print(f"Warning: Unknown species type '{species_type}' for ID {species_id}. Skipping.")
                continue

            self.species_by_id[species_id] = obj

    def get_species_by_id(self, species_id):
        """ID 코드로 특정 종 객체를 반환합니다."""
        return self.species_by_id.get(species_id)