# main_simulator.py (fitness_calculator 전달 로직 추가)
"""
sSLiM 통합 시뮬레이션 러너.
모든 엔진과 관리자 모듈을 통합하여 시뮬레이션의 메인 루프를 실행합니다.
"""
import json
from ecosystem_manager import EcosystemManager
from species_generator import generate_species_from_archetypes
from climate_engine import ClimateEngine
from interaction_engine import resolve_interactions
from data_logger import DataLogger
import fitness_calculator as fc

class SimulationRunner:
    def __init__(self, config, run_number=1, is_first_run=True, species_list_override=None):
        self.config = config
        self.run_number = run_number
        self.settings = config['simulation_settings']

        if species_list_override is not None:
            species_list = species_list_override
        else:
            species_list = generate_species_from_archetypes(
                config['ecosystem_setup'],
                config.get('genetic_engine_params'),
                config.get('species_fixed_params')
            )

        self.manager = EcosystemManager(species_list, self.config)
        self.climate_engine = ClimateEngine(
            scenario_name=config['climate_scenario']['scenario_name'],
            initial_temp=config['climate_scenario']['initial_temp'],
            filepath=config['climate_scenario'].get('filepath')
        )
        self.logger = DataLogger(self.settings['results_filename'], self.manager)
        self.logger.setup(is_first_run)
        self.genetic_engines = {
            sid: obj for sid, obj in self.manager.species_by_id.items()
            if obj.__class__.__name__ == 'GeneticEngine'
        }

    def run(self, verbose=True, gui_callback=None, ticks_override=None):
        is_verbose = verbose and (gui_callback is None)
        if is_verbose: print("\n--- Simulation Start ---")

        total_ticks = ticks_override if ticks_override is not None else self.settings['total_ticks']
        if is_verbose and ticks_override:
            print(f"Running simulation with overridden ticks: {total_ticks}")

        is_extinct = False
        final_tick = 0

        try:
            for tick in range(1, total_ticks + 1):
                final_tick = tick
                self.climate_engine.update_environment_for_tick(tick)
                current_environment = self.climate_engine.get_environment()

                interaction_results = resolve_interactions(self.manager, current_environment, self.config)
                deltas = interaction_results['deltas']
                for species_id, delta in deltas.items():
                    species = self.manager.get_species_by_id(species_id)
                    if species:
                        species.update_population(delta)

                energy_gains = interaction_results.get('genetic_species_energy_gain', {})
                for sid, engine in self.genetic_engines.items():
                    engine.distribute_energy(energy_gains.get(sid, 0))

                for engine in self.genetic_engines.values():
                    if not engine.population: continue
                    
                    # 피트니스 계산에 필요한 환경 정보 구성
                    env_for_fitness = current_environment.copy()
                    prey_pop = sum(s.population for s in self.manager.species_by_id.values() if s.status.startswith('3-1'))
                    env_for_fitness['prey_availability'] = prey_pop
                    genetic_params = self.config.get('genetic_engine_params', {})
                    env_for_fitness['optimal_temperature'] = genetic_params.get('optimal_temperature', 15.0)
                    
                    # [핵심 수정] genetic_engine이 사용할 수 있도록 fitness_calculator 모듈을 전달
                    env_for_fitness['fitness_calculator'] = fc
                    
                    # 이제 run_generation_step이 내부적으로 viability와 fecundity를 모두 계산
                    engine.run_generation_step(env_for_fitness)

                if not ticks_override and (tick % self.settings['log_interval'] == 0):
                    if gui_callback:
                        log_data = self._create_aggregated_log_data_dict(tick, current_environment)
                        if not gui_callback(tick, total_ticks, log_data):
                            break
                    else:
                        self.logger.log_tick(self.run_number, tick, current_environment)

                if is_verbose and (tick % 50 == 0 or tick == 1):
                    print(f"--- Tick {tick}/{total_ticks} --- Temp: {current_environment['temperature']:.2f}°C")

                all_extinct = not any(
                    len(s.population) if isinstance(s.population, list) else s.population > 0
                    for s in self.manager.species_by_id.values()
                )
                if all_extinct:
                    if is_verbose: print(f"\nAll species have gone extinct at tick {tick}. Ending.")
                    is_extinct = True
                    if not ticks_override:
                        self.logger.log_tick(self.run_number, tick, current_environment)
                    break
        finally:
            if not ticks_override:
                self.logger.close()
            if is_verbose: print("--- Simulation End ---")

        return final_tick, is_extinct

    def _create_aggregated_log_data_dict(self, tick, environment):
        """
        GUI 시각화를 위해 역할군별로 집계된 데이터 딕셔너리를 생성합니다.
        """
        log_data = {'Tick': tick}; log_data.update(environment)

        producers = [s for s in self.manager.species_by_id.values() if s.__class__.__name__ == 'Producer']
        consumers = [s for s in self.manager.species_by_id.values() if s.__class__.__name__ == 'Consumer']
        apex_predators = [s for s in self.manager.species_by_id.values() if s.__class__.__name__ == 'GeneticEngine']

        log_data['Producers_Pop'] = max(1.0, float(sum(s.population for s in producers)))
        log_data['Consumers_Pop'] = max(1.0, float(sum(s.population for s in consumers)))
        log_data['Apex_Predators_Pop'] = max(1.0, float(sum(len(s.population) for s in apex_predators)))

        if apex_predators and apex_predators[0].population:
            stats = apex_predators[0].get_population_stats()
            log_data['Avg_Heat_Resistance'] = stats.get('avg_heat_resistance', 0)
            log_data['Avg_Foraging_Efficiency'] = stats.get('avg_foraging_efficiency', 0)
        else:
            log_data['Avg_Heat_Resistance'] = 0
            log_data['Avg_Foraging_Efficiency'] = 0

        return log_data