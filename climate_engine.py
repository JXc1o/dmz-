# climate_engine.py (영양소 관리 기능 제거)
"""
기후 시나리오 관리 및 환경 데이터 제공 엔진.
내장 시나리오 또는 외부 CSV 파일로부터 기후 데이터를 로드하고,
요청에 따라 해당 시점의 환경 데이터를 반환합니다.
외부 CSV 파일은 다양한 형식을 자동으로 감지하고 처리합니다.
"""
import pandas as pd

class ClimateEngine:
    def __init__(self, scenario_name, initial_temp, filepath=None):
        self.scenario_name = scenario_name
        self.initial_temp = initial_temp
        self.climate_data = None
        self.use_csv = False

        if filepath:
            try:
                self._load_and_process_csv(filepath)
                first_row = self.climate_data.iloc[0]
                self.initial_temp = first_row['temperature']
                self.update_func = self._update_from_csv
                self.use_csv = True
                print(f"ClimateEngine initialized with processed CSV data from: '{filepath}'")

            except Exception as e:
                print(f"Warning: Failed to load or process climate CSV '{filepath}'. Error: {e}. Defaulting to '{scenario_name}'.")
                self.use_csv = False

        if not self.use_csv:
            if scenario_name == "Stable":
                self.update_func = self._update_stable
            elif scenario_name == "Linear_Warming":
                self.update_func = self._update_linear_warming
            elif scenario_name == "RCP_8.5_Extreme":
                self.update_func = self._update_rcp85_extreme
            else:
                print(f"Warning: Unknown climate scenario '{scenario_name}'. Defaulting to Stable.")
                self.update_func = self._update_stable

        self.environment = {
            "temperature": self.initial_temp
        }

    def _load_and_process_csv(self, filepath):
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(filepath, encoding='euc-kr')

        df.columns = [col.strip() for col in df.columns]

        if 'tick' in df.columns and 'temperature' in df.columns:
            print("Standard SERM climate file detected.")
            self.climate_data = df.set_index('tick')
            return

        temp_col_candidates = ['Tavg(c)', '평균기온(°C)', 'temperature_avg']
        temp_max_col_candidates = ['Tmax(c)', '최고기온(°C)', 'temperature_max']
        temp_min_col_candidates = ['Tmin(c)', '최저기온(°C)', 'temperature_min']

        temp_col = next((col for col in temp_col_candidates if col in df.columns), None)
        temp_max_col = next((col for col in temp_max_col_candidates if col in df.columns), None)
        temp_min_col = next((col for col in temp_min_col_candidates if col in df.columns), None)

        if ('Year' in df.columns and 'Mon' in df.columns and 'Day' in df.columns) or \
           ('일시' in df.columns or '날짜' in df.columns):
            
            print("KMA-style raw climate file detected. Processing...")
            df.replace(-99, pd.NA, inplace=True)

            if temp_col:
                df['temperature'] = df[temp_col]
            
            if 'temperature' not in df.columns and temp_max_col and temp_min_col:
                 df['temperature'] = (df[temp_max_col].astype(float) + df[temp_min_col].astype(float)) / 2
            
            if 'temperature' not in df.columns:
                raise ValueError("Could not find a usable temperature column (e.g., 'Tavg(c)') or combination of Tmax/Tmin.")

            df.dropna(subset=['temperature'], inplace=True)
            df.reset_index(drop=True, inplace=True)
            
            df['tick'] = df.index + 1
            processed_df = df[['tick', 'temperature']].copy()
            processed_df['temperature'] = processed_df['temperature'].round(2)
            
            self.climate_data = processed_df.set_index('tick')
            print(f"Successfully processed {len(self.climate_data)} data points.")
            return

        raise ValueError("Unsupported CSV format. File must contain either ('tick', 'temperature') columns or KMA-style date and temperature columns.")


    def get_environment(self):
        return self.environment

    def update_environment_for_tick(self, tick):
        self.update_func(tick)

    def _update_from_csv(self, tick):
        try:
            if tick in self.climate_data.index:
                row = self.climate_data.loc[tick]
            else:
                idx = self.climate_data.index.get_loc(tick, method='ffill')
                row = self.climate_data.iloc[idx]

            self.environment['temperature'] = row['temperature']
        except KeyError:
            pass

    def _update_stable(self, tick):
        pass

    def _update_linear_warming(self, tick):
        self.environment['temperature'] = self.initial_temp + (tick * 0.05)

    def _update_rcp85_extreme(self, tick):
        self.environment['temperature'] = self.initial_temp + (tick**1.5) * 0.005