# main_robust_runner.py (과학적 균형 함수 호출 및 50회 반복)
"""
이상적인 생태계 구성을 사용하고 초기 개체수 비율을 과학적 원리에 따라 조절하여
50회 반복 시뮬레이션을 실행하고, 평균 결과와 그래프를 생성하는 메인 실행기.
"""
import json
import os
import copy
from main_simulator import SimulationRunner
# [수정] generate_scientifically_balanced_ecosystem 함수를 임포트
from species_generator import generate_scientifically_balanced_ecosystem, generate_ideal_ecosystem_request
from post_processor import process_batch_results 

# --- 실험 설정 ---
TARGET_SUCCESSFUL_RUNS = 50
VALIDATION_TICKS = 100
MAX_GENERATION_ATTEMPTS = 150

def main():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            base_config = json.load(f)
            print("Configuration loaded successfully.")
    except FileNotFoundError:
        print("Error: config.json not found.")
        return

    results_folder = 'results'
    os.makedirs(results_folder, exist_ok=True)
    log_filename = base_config['simulation_settings']['results_filename']
    full_log_path = os.path.join(results_folder, log_filename)
    base_config['simulation_settings']['results_filename'] = full_log_path

    if os.path.exists(full_log_path):
        os.remove(full_log_path)
        print(f"Removed old log file: '{full_log_path}'")
    
    print('=' * 60)
    print(f'     Starting Scientifically Balanced Batch Runner')
    print(f'     Target: {TARGET_SUCCESSFUL_RUNS} successful runs')
    print('=' * 60)

    successful_runs = 0
    total_attempts = 0
    is_first_log = True

    while successful_runs < TARGET_SUCCESSFUL_RUNS and total_attempts < MAX_GENERATION_ATTEMPTS:
        total_attempts += 1
        print(f"\n--- [Attempt {total_attempts}/{MAX_GENERATION_ATTEMPTS}] ---")
        
        # [핵심 수정] 과학적 원리에 따라 개체 수 비율을 자동으로 조절하는 함수 호출
        eco_request = generate_ideal_ecosystem_request()
        species_list = generate_scientifically_balanced_ecosystem(
            eco_request,
            base_config
        )

        print(f"\nValidating ecosystem for {VALIDATION_TICKS} ticks...")
        validation_config = copy.deepcopy(base_config)
        validation_config['simulation_settings']['results_filename'] = "temp_validation_log.csv"
        
        validator = SimulationRunner(
            config=validation_config,
            species_list_override=species_list,
            is_first_run=False
        )
        last_tick, is_extinct = validator.run(verbose=False, ticks_override=VALIDATION_TICKS)

        if is_extinct and last_tick < VALIDATION_TICKS:
            print(f"[Result] FAILED: Ecosystem collapsed at tick {last_tick}. Generating a new one.")
            if os.path.exists("temp_validation_log.csv"):
                os.remove("temp_validation_log.csv")
            continue

        print(f"[Result] PASSED: Ecosystem is stable. Proceeding with full simulation.")
        
        successful_runs += 1
        print(f"--- Running Main Simulation {successful_runs}/{TARGET_SUCCESSFUL_RUNS} ---")
        
        runner = SimulationRunner(
            config=base_config, # 원본 config 사용
            run_number=successful_runs,
            is_first_run=is_first_log,
            species_list_override=species_list
        )
        is_first_log = False
        runner.run(verbose=True)

    print('\n' * 60)
    if successful_runs == TARGET_SUCCESSFUL_RUNS:
        print(f'     All {TARGET_SUCCESSFUL_RUNS} successful runs complete