# visualizer.py
"""
시뮬레이션 결과 시각화 도구.
기록된 CSV 데이터를 읽어 Matplotlib을 사용하여 그래프를 생성하고 이미지 파일로 저장합니다.
"""
import pandas as pd
import matplotlib.pyplot as plt

def visualize_results(log_file, output_image):
    """
    로그 파일(CSV)을 읽어 시뮬레이션 결과를 시각화합니다.
    """
    try:
        df = pd.read_csv(log_file)
    except FileNotFoundError:
        print(f"Error: Log file not found at '{log_file}'. Cannot generate visualization.")
        return

    if df.empty:
        print("Warning: Log file is empty. No data to visualize.")
        return
        
    print(f"Generating visualization from '{log_file}'...")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), sharex=True)
    fig.suptitle('sSLiM Ecosystem Simulation Results', fontsize=16)

    # --- Plot 1: Population Dynamics ---
    ax1.set_title('Population Dynamics')
    ax1.set_ylabel('Population Size')
    pop_cols = [col for col in df.columns if 'Pop' in col]
    for col in pop_cols:
        ax1.plot(df['Tick'], df[col], label=col, lw=2)
    ax1.legend(loc='upper left')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.set_yscale('log') # 개체수 차이가 클 경우 로그 스케일이 유용
    ax1.set_ylim(bottom=1) # 로그 스케일에서 0이하 값 방지

    # --- Plot 2: Environmental & Genetic Adaptation ---
    ax2.set_title('Environmental Change and Genetic Adaptation')
    ax2.set_xlabel('Tick (Time)')
    
    # Left Y-axis for Temperature
    ax2.set_ylabel('Temperature (°C)', color='tab:red')
    ax2.plot(df['Tick'], df['Temperature'], color='tab:red', label='Temperature', linestyle='--')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    # Right Y-axis for Average Trait Values
    if 'Avg_Heat_Resistance' in df.columns:
        ax2_twin = ax2.twinx()
        ax2_twin.set_ylabel('Avg. Trait Value')
        
        # 고온 저항성 플롯
        ax2_twin.plot(df['Tick'], df['Avg_Heat_Resistance'], color='tab:blue', label='Avg Heat Resistance')
        
        # 먹이 탐색 효율 플롯
        if 'Avg_Foraging_Efficiency' in df.columns:
            ax2_twin.plot(df['Tick'], df['Avg_Foraging_Efficiency'], color='tab:green', label='Avg Foraging Eff.')
            
        ax2_twin.tick_params(axis='y')
        ax2_twin.legend(loc='upper right')
    
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save the figure
    plt.savefig(output_image)
    print(f"Visualization saved to '{output_image}'")
    # plt.show() # Uncomment to display the plot directly

if __name__ == '__main__':
    # 이 파일을 직접 실행할 경우, 기본 설정 파일 이름으로 시각화를 시도합니다.
    visualize_results('simulation_log.csv', 'simulation_results.png')