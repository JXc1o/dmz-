# post_processor.py (필터링 로직 제거 후 단순화된 버전)
"""
시뮬레이션 후처리기.
배치 실행으로 생성된 단일 결과 파일(CSV)을 읽어 평균 및 표준편차를 계산하고,
요약 데이터와 그래프로 저장합니다.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt

def process_batch_results(config, results_folder='results'):
    """
    지정된 단일 결과 파일을 읽어 평균 결과를 생성합니다.
    """
    print("\n--- Starting Post-Processing ---")
    
    log_file_path = config['simulation_settings']['results_filename']
    
    if not os.path.exists(log_file_path):
        print(f"Warning: Log file not found at '{log_file_path}'. Skipping post-processing.")
        return

    print(f"Processing log file: '{log_file_path}'")
    all_data = pd.read_csv(log_file_path)

    if all_data.empty:
        print("Warning: Log file is empty. No summary will be generated.")
        return

    # 'Run' 컬럼이 있으면 실행 횟수 보고
    num_runs = all_data['Run'].nunique() if 'Run' in all_data.columns else 1
    print(f"Calculating averages from {num_runs} successful run(s).")
    
    # Tick을 기준으로 그룹화하여 평균 계산
    mean_df = all_data.groupby('Tick').mean()
    if 'Run' in mean_df.columns:
        mean_df = mean_df.drop(columns=['Run'])
    
    # 평균 데이터 CSV 파일로 저장
    summary_csv_path = os.path.join(results_folder, 'summary_average_results.csv')
    mean_df.to_csv(summary_csv_path)
    print(f"Average results saved to '{summary_csv_path}'")

    # 평균 데이터로 그래프 생성
    summary_png_path = os.path.join(results_folder, 'summary_average_graph.png')
    visualize_summary(mean_df, summary_png_path, f'Averaged Results ({num_runs} Runs)')

def visualize_summary(df, output_image, title_suffix=""):
    print(f"Generating summary visualization...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), sharex=True)
    main_title = 'SERM Ecosystem Simulation - ' + title_suffix
    fig.suptitle(main_title, fontsize=16)

    ax1.set_title('Average Population Dynamics')
    ax1.set_ylabel('Population Size (Log Scale)')
    pop_cols = [col for col in df.columns if 'Pop' in col]
    for col in pop_cols:
        ax1.plot(df.index, df[col], label=col.replace('_', ' '), lw=2)
    ax1.legend(loc='upper left'); ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.set_yscale('log'); ax1.set_ylim(bottom=1)

    ax2.set_title('Average Environmental Change and Genetic Adaptation')
    ax2.set_xlabel('Tick (Time)'); ax2.set_ylabel('Temperature (°C)', color='tab:red')
    ax2.plot(df.index, df['Temperature'], color='tab:red', label='Temperature', linestyle='--')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    ax2_twin = ax2.twinx()
    ax2_twin.set_ylabel('Avg. Trait Value')
    
    if 'Avg_Heat_Resistance' in df.columns:
        ax2_twin.plot(df.index, df['Avg_Heat_Resistance'], color='tab:blue', label='Avg Heat Resistance')
    if 'Avg_Foraging_Efficiency' in df.columns:
        ax2_twin.plot(df.index, df['Avg_Foraging_Efficiency'], color='tab:green', label='Avg Foraging Eff.')
        
    lines, labels = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2_twin.legend(lines + lines2, labels + labels2, loc='upper right')
    
    fig.tight_layout(rect=[0, 0, 1, 0.96]); plt.savefig(output_image)
    print(f"Summary visualization saved to '{output_image}'")