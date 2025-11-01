# objective.py (수정 완료)
import pandas as pd
import numpy as np
import os
import traceback
import copy

from main_simulator import SimulationRunner
from species_generator import generate_species_from_archetypes

def calculate_fitness_score(sim_df, target_df):
    """두 데이터프레임 간의 오차를 계산하여 피트니스 점수를 반환합니다."""
    # --- 핵심 수정 사항: 올바른 데이터 병합(merge) 로직 ---
    # target_df와 sim_df의 컬럼 이름 충돌을 방지하기 위해, target_df의 컬럼에 접미사를 붙임
    target_cols = {col: f"{col}_target" for col in target_df.columns if col != 'Tick'}
    target_df_renamed = target_df.rename(columns=target_cols)

    # 오직 'Tick'을 기준으로 병합 (how='inner'로 하여 양쪽에 모두 있는 Tick만 비교)
    merged_df = pd.merge(target_df_renamed, sim_df, on='Tick', how='inner')
    merged_df = merged_df.fillna(0) # 시뮬레이션에서 종이 멸종하면 NaN이 될 수 있음
    
    if merged_df.empty:
        # 공통된 Tick이 하나도 없는 경우
        return 0.0

    error = 0.0
    num_cols = 0
    
    # 목표 데이터의 컬럼을 기준으로 오차 계산
    for col_target in merged_df.columns:
        if not col_target.endswith('_target'):
            continue
        
        # 원본 컬럼 이름 (예: 'ID_0_Pop_(Producer)')
        base_col_name = col_target.replace('_target', '')
        
        # 시뮬레이션 결과에서 해당하는 컬럼 찾기
        # target_df의 컬럼 이름 형식과 sim_df의 컬럼 이름 형식이 정확히 일치한다고 가정
        col_sim = base_col_name
        
        if col_sim in merged_df.columns:
            # 스케일링을 위한 정규화 (최대값으로 나눔)
            max_val = max(merged_df[col_target].max(), merged_df[col_sim].max())
            if max_val == 0: continue
            
            norm_target = merged_df[col_target] / max_val
            norm_sim = merged_df[col_sim] / max_val
            
            # 제곱근 평균 제곱 오차 (RMSE)
            error += np.sqrt(np.mean((norm_target - norm_sim) ** 2))
            num_cols += 1
    # --- 수정 끝 ---

    if num_cols == 0:
        # 비교할 공통 컬럼이 없는 경우
        return 0.0

    # 평균 오차 계산 후 피트니스로 변환 (오차가 작을수록 높음)
    avg_error = error / num_cols
    fitness = 1.0 / (1.0 + avg_error)
    
    return fitness

def evaluate_fitness(args, base_config, target_df, results_folder):
    """
    하나의 파라미터 셋으로 시뮬레이션을 실행하고 피트니스를 계산하는 워커 함수.
    """
    run_id, params_dict = args
    
    current_config = copy.deepcopy(base_config)
    
    for key, value in params_dict.items():
        if key.startswith('config_'):
            parts = key.split('_')
            config_path = parts[1:]
            
            sub_dict = current_config
            try:
                for part in config_path[:-1]:
                    sub_dict = sub_dict[part]
                sub_dict[config_path[-1]] = value
            except KeyError:
                pass
    
    species_list = generate_species_from_archetypes(
        current_config['ecosystem_setup'], 
        current_config.get('genetic_engine_params'),
        current_config.get('species_fixed_params')
    )
    
    for sp_data in species_list:
        sp_id = sp_data['id']
        if 'params' in sp_data:
            for param_name, value in params_dict.items():
                if param_name.startswith(f'species_ID_{sp_id}_'):
                    key = param_name.replace(f'species_ID_{sp_id}_', '')
                    sp_data['params'][key] = value

    sim_log_filename = os.path.join(results_folder, f"run_{run_id}_log.csv")
    current_config['simulation_settings']['results_filename'] = sim_log_filename

    validation_ticks = current_config['simulation_settings'].get('stability_validation_ticks', 0)
    if validation_ticks and validation_ticks > 0:
        temp_validation_path = os.path.join(results_folder, f"run_{run_id}_validation.csv")
        validation_config = copy.deepcopy(current_config)
        validation_config['simulation_settings'] = copy.deepcopy(current_config['simulation_settings'])
        validation_config['simulation_settings']['results_filename'] = temp_validation_path
        validator = SimulationRunner(
            config=validation_config,
            run_number=run_id,
            is_first_run=False,
            species_list_override=copy.deepcopy(species_list)
        )
        last_tick, is_extinct = validator.run(verbose=False, ticks_override=validation_ticks)
        apex_alive = any(len(engine.population) > 0 for engine in validator.genetic_engines.values())
        if os.path.exists(temp_validation_path):
            try:
                os.remove(temp_validation_path)
            except OSError:
                pass
        if (is_extinct and last_tick < validation_ticks) or not apex_alive:
            return 0.0

    try:
        runner = SimulationRunner(
            config=current_config,
            run_number=run_id,
            is_first_run=True,
            species_list_override=species_list
        )
        runner.run(verbose=False)
        
        if not os.path.exists(sim_log_filename) or os.path.getsize(sim_log_filename) < 10: # 파일이 너무 작으면 유효하지 않음
            # print(f"Warning: Simulation for run {run_id} did not produce a valid log file.")
            return 0.0
            
        sim_result_df = pd.read_csv(sim_log_filename)
        if sim_result_df.empty:
            # print(f"Warning: Simulation for run {run_id} produced an empty log file.")
            return 0.0

        fitness = calculate_fitness_score(sim_result_df, target_df)
        
    except Exception:
        print(f"--- ERROR in simulation run {run_id} ---")
        traceback.print_exc()
        print("------------------------------------")
        fitness = 0.0
    finally:
        if os.path.exists(sim_log_filename):
            try:
                os.remove(sim_log_filename)
            except OSError:
                pass # 파일이 다른 프로세스에 의해 사용 중일 수 있음
            
    return fitness