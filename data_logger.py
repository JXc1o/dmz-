# data_logger.py (Nutrient_Level 제거)
"""
시뮬레이션 데이터 로거.
매 tick의 상태를 지정된 CSV 파일에 기록하여,
시뮬레이션 종료 후 분석 및 시각화가 가능하도록 합니다.
"""
import csv
import os

class DataLogger:
    def __init__(self, filename, manager):
        self.filename = filename
        self.manager = manager
        self.file = None
        self.writer = None

    def setup(self, is_first_run):
        file_exists = os.path.exists(self.filename)
        open_mode = 'w' if is_first_run else 'a'
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        self.file = open(self.filename, open_mode, newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        
        if is_first_run:
            headers = ['Run', 'Tick', 'Temperature'] # [수정] Nutrient_Level 제거
            species_ids = sorted(self.manager.species_by_id.keys())
            for sp_id in species_ids:
                species = self.manager.get_species_by_id(sp_id)
                headers.append(f"ID_{sp_id}_Pop_({species.__class__.__name__})")

            genetic_engine = self._get_genetic_engine()
            if genetic_engine:
                headers.append("Avg_Heat_Resistance")
                headers.append("Avg_Foraging_Efficiency")
            
            self.writer.writerow(headers)
            self.file.flush()

    def log_tick(self, run_number, tick, environment):
        if not self.writer:
            print("Warning: DataLogger writer is not available. Cannot log tick.")
            return

        row = [run_number, tick, environment['temperature']] # [수정] Nutrient_Level 제거
        species_ids = sorted(self.manager.species_by_id.keys())
        for sp_id in species_ids:
            species = self.manager.get_species_by_id(sp_id)
            pop = len(species.population) if hasattr(species, 'population') and isinstance(species.population, list) else species.population
            row.append(int(pop))
        
        genetic_engine = self._get_genetic_engine()
        if genetic_engine:
            stats = genetic_engine.get_population_stats()
            row.append(stats.get('avg_heat_resistance', 0))
            row.append(stats.get('avg_foraging_efficiency', 0))
        
        try:
            self.writer.writerow(row)
            self.file.flush()
        except Exception as e:
            print(f"Error writing to log file: {e}")

    def close(self):
        if self.file and not self.file.closed:
            self.file.close()
            self.file = None
            self.writer = None

    def _get_genetic_engine(self):
        if not hasattr(self.manager, 'species_by_id') or not self.manager.species_by_id:
            return None
        return next((s for s in self.manager.species_by_id.values() if hasattr(s, 'run_generation_step')), None)