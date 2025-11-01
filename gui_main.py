# gui_main.py (성능 개선 및 UI 조절 기능 추가)
import sys
import os
import json
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTabWidget, QGridLayout, QGroupBox, QLabel,
                             QComboBox, QSlider, QProgressBar, QTextEdit, QFileDialog,
                             QMessageBox, QDoubleSpinBox, QSpinBox, QCheckBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor
import pyqtgraph as pg
import pyqtgraph.exporters
import copy
import time
import traceback

# --- Module Imports ---
from main_simulator import SimulationRunner
from interaction_engine import resolve_interactions
import fitness_calculator as fc
from species_generator import (
    generate_species_from_archetypes,
    generate_scientifically_balanced_ecosystem,
    SPECIES_ARCHETYPES,
)

try:
    from optimizer import (initialize_population, tournament_selection,
                           simulated_binary_crossover, polynomial_mutation as pm_original,
                           create_target_data_if_not_exists, generate_dynamic_param_ranges,
                           POPULATION_SIZE, BASE_MUTATION_RATE)
    from objective import evaluate_fitness
    from multiprocessing import Pool, cpu_count
    from functools import partial
    OPTIMIZER_ENABLED = True
except ImportError as e:
    print(f"Warning: Optimizer modules could not be imported. Error: {e}")
    OPTIMIZER_ENABLED = False
    BASE_MUTATION_RATE = 0.2
    pm_original = None

pg.setConfigOption('background', '#1E1E1E')
pg.setConfigOption('foreground', 'w')

ECOSYSTEM_PRESETS = {
    "초원": {
        "setup": {
            "photosynthetic_autotroph": 4,
            "primary_consumer_herbivore": 3,
            "tertiary_consumer_apex": 1
        },
        "default_scenario": "Stable",
        "initial_temp": 18.0,
        "description": "생산자 비중이 높고 변동이 완만한 초원 생태계"
    },
    "숲": {
        "setup": {
            "photosynthetic_autotroph": 5,
            "primary_consumer_herbivore": 3,
            "tertiary_consumer_apex": 2
        },
        "default_scenario": "Linear_Warming",
        "initial_temp": 16.0,
        "description": "수직 구조가 복잡하고 경쟁이 높은 숲 생태계"
    },
    "해양": {
        "setup": {
            "photosynthetic_autotroph": 6,
            "primary_consumer_herbivore": 4,
            "tertiary_consumer_apex": 2
        },
        "default_scenario": "RCP_8.5_Extreme",
        "initial_temp": 14.0,
        "description": "플랑크톤 기반의 빠른 순환이 있는 해양 생태계"
    }
}

SPECIES_DISPLAY_NAMES = {
    "photosynthetic_autotroph": "생산자 (광합성)",
    "primary_consumer_herbivore": "초식 소비자",
    "tertiary_consumer_apex": "최상위 포식자"
}

def polynomial_mutation(individual, param_ranges, mutation_rate=None):
    if OPTIMIZER_ENABLED and pm_original is not None:
        rate = mutation_rate if mutation_rate is not None else BASE_MUTATION_RATE
        return pm_original(individual, param_ranges, mutation_rate=rate)
    return individual

class SimulationWorker(QThread):
    progress = pyqtSignal(int, int, dict)
    finished = pyqtSignal(str)

    def __init__(self, config, species_list=None):
        super().__init__()
        self.config = config
        self.species_list_override = species_list
        self.is_running = True

    def run(self):
        try:
            runner = SimulationRunner(
                self.config,
                is_first_run=True,
                run_number=1,
                species_list_override=self.species_list_override,
            )
            last_tick, is_extinct = runner.run(gui_callback=self.update_gui_progress)

            if not self.is_running:
                self.finished.emit("Execution stopped by user.")
            elif is_extinct:
                self.finished.emit(f"All species went extinct (Tick: {last_tick})")
            else:
                self.finished.emit("Simulation complete.")
        except Exception as e:
            self.finished.emit(f"Error occurred: {e}\n{traceback.format_exc()}")

    def update_gui_progress(self, tick, total_ticks, log_data):
        if not self.is_running:
            return False
        self.progress.emit(tick, total_ticks, log_data)
        self.msleep(5)
        return True

    def stop(self):
        self.is_running = False

class OptimizerWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict, str)
    update_progress_bar = pyqtSignal(int, int)

    def __init__(self, base_config, target_csv_path):
        super().__init__()
        self.base_config = base_config
        self.target_csv_path = target_csv_path
        self.is_running = True

        optim_settings = self.base_config.get('optimizer_settings', {})
        self.population_size = optim_settings.get('population_size', 20)
        self.MAX_GENERATIONS = 500
        self.FITNESS_TARGET = optim_settings.get('fitness_target', 0.95)
        self.STAGNATION_LIMIT = optim_settings.get('stagnation_limit', 10)
        self.ADAPTIVE_MUTATION_INCREASE = optim_settings.get('adaptive_mutation_increase_factor', 1.5)
        self.base_mutation_rate = optim_settings.get('base_mutation_rate', BASE_MUTATION_RATE)
        self.fitness_cache = {}
        self.eval_counter = 0

    def run(self):
        try:
            self.progress.emit("Starting optimization...")
            target_df = pd.read_csv(self.target_csv_path)
            optimizer_results_folder = "optimizer_runs"
            os.makedirs(optimizer_results_folder, exist_ok=True)
            param_ranges = generate_dynamic_param_ranges(self.base_config)
            self.progress.emit(f"Optimizing {len(param_ranges)} parameters.\nTarget Fitness: {self.FITNESS_TARGET:.2f}, Stagnation Limit: {self.STAGNATION_LIMIT} generations.")
            population = initialize_population(param_ranges)
            population_keys = [self._individual_to_key(ind) for ind in population]
            num_cores = max(1, cpu_count() - 1)
            self.progress.emit(f"Starting parallel evaluation using {num_cores} cores.")
            eval_func = partial(evaluate_fitness, base_config=self.base_config, target_df=target_df, results_folder=optimizer_results_folder)
            best_fitness_overall = -1
            best_individual_overall = None
            best_key_overall = None
            stagnation_counter = 0
            gen = 0
            with Pool(processes=num_cores) as pool:
                while self.is_running:
                    gen += 1
                    if gen > self.MAX_GENERATIONS:
                        self.progress.emit(f"\nSafety Stop: Reached max generations ({self.MAX_GENERATIONS}). Stopping optimization.")
                        break
                    self.update_progress_bar.emit(gen, self.MAX_GENERATIONS)
                    gen_start_time = time.time()
                    self.progress.emit(f"\n--- [Generation {gen}] ---")
                    current_mutation_rate = self.base_mutation_rate
                    if stagnation_counter >= self.STAGNATION_LIMIT:
                        self.progress.emit(f"Fitness stagnated! Increasing mutation rate by {self.ADAPTIVE_MUTATION_INCREASE}x.")
                        current_mutation_rate *= self.ADAPTIVE_MUTATION_INCREASE
                        stagnation_counter = 0
                    fitness_scores = [None] * len(population)
                    evaluations = []
                    evaluation_keys = []
                    for idx, (individual, key) in enumerate(zip(population, population_keys)):
                        if key in self.fitness_cache:
                            fitness_scores[idx] = self.fitness_cache[key]
                        else:
                            evaluations.append((self.eval_counter, individual))
                            evaluation_keys.append((idx, key))
                            self.eval_counter += 1
                    if evaluations:
                        chunk = max(1, len(evaluations) // (num_cores * 4) or 1)
                        results = pool.map(eval_func, evaluations, chunksize=chunk)
                        for (idx, key), score in zip(evaluation_keys, results):
                            fitness_scores[idx] = score
                            self.fitness_cache[key] = score
                    # fill any remaining None (should not happen)
                    fitness_scores = [score if score is not None else 0.0 for score in fitness_scores]
                    max_fitness_gen = max(fitness_scores)
                    if max_fitness_gen > best_fitness_overall:
                        best_fitness_overall = max_fitness_gen
                        best_idx = fitness_scores.index(max_fitness_gen)
                        best_individual_overall = population[best_idx]
                        best_key_overall = population_keys[best_idx]
                        stagnation_counter = 0
                    else:
                        stagnation_counter += 1
                    gen_time = time.time() - gen_start_time
                    self.progress.emit(f"Generation Best Fitness: {max_fitness_gen:.6f} (Time: {gen_time:.2f}s)\nOverall Best Fitness: {best_fitness_overall:.6f} (Stagnation: {stagnation_counter}/{self.STAGNATION_LIMIT})")
                    if best_fitness_overall >= self.FITNESS_TARGET:
                        self.progress.emit(f"\nTarget fitness ({self.FITNESS_TARGET}) reached! Stopping optimization.")
                        self.update_progress_bar.emit(self.MAX_GENERATIONS, self.MAX_GENERATIONS)
                        break
                    new_population = [best_individual_overall]
                    new_population_keys = [best_key_overall]
                    while len(new_population) < self.population_size:
                        p1 = tournament_selection(population, fitness_scores)
                        p2 = tournament_selection(population, fitness_scores)
                        c1, c2 = simulated_binary_crossover(p1, p2, param_ranges)
                        child1 = polynomial_mutation(c1, param_ranges, mutation_rate=current_mutation_rate)
                        new_population.append(child1)
                        new_population_keys.append(self._individual_to_key(child1))
                        if len(new_population) < self.population_size:
                            child2 = polynomial_mutation(c2, param_ranges, mutation_rate=current_mutation_rate)
                            new_population.append(child2)
                            new_population_keys.append(self._individual_to_key(child2))
                    population = new_population
                    population_keys = new_population_keys
            if self.is_running and best_individual_overall:
                self.finished.emit(best_individual_overall, "Optimization complete.")
            else:
                self.finished.emit(None, "Optimization stopped or failed.")
        except Exception as e:
            self.finished.emit(None, f"Optimization Error: {e}\n{traceback.format_exc()}")
    def stop(self):
        self.is_running = False

    @staticmethod
    def _individual_to_key(individual):
        return tuple(sorted((k, round(v, 6)) for k, v in individual.items()))

class SplashScreen(QWidget):
    finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.full_text = "SERM:\nSelection on Linked Mutations"
        self.current_text = ""
        self.char_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_text)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        font = QFont("Courier New", 45, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("white"))
        display_text = self.current_text
        if self.char_index < len(self.full_text):
            if int(time.time() * 2) % 2 == 0:
                display_text += "_"
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, display_text)
    def show_splash(self):
        self.showFullScreen()
        self.timer.start(100)
    def update_text(self):
        if self.char_index < len(self.full_text):
            self.current_text += self.full_text[self.char_index]
        else:
            self.timer.stop()
            QTimer.singleShot(1500, self.close_splash)
        self.char_index += 1
        self.update()
    def close_splash(self):
        self.close()
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SERM - Ecosystem Simulator")
        self.setGeometry(100, 100, 1600, 900)
        self.current_config_path = 'config.json'
        self.climate_csv_path = None
        self.target_csv_path = None
        self.plot_data_streams = {}
        self.optimized_config = None
        self.best_params = None
        self.config = self.load_config(self.current_config_path)
        if not self.config:
            QMessageBox.critical(self, "Config File Error", f"Could not find {self.current_config_path}. The program will exit.").exec()
            sys.exit(1)
        self._suppress_ecosystem_events = False
        self.config = self.ensure_config_defaults(self.config)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.sim_tab = QWidget()
        self.optim_tab = QWidget()
        self.tabs.addTab(self.sim_tab, "Interactive Simulator")
        self.tabs.addTab(self.optim_tab, "Parameter Optimizer")
        self.init_sim_ui()
        self.init_optim_ui()
        if not OPTIMIZER_ENABLED:
            self.tabs.setTabEnabled(1, False)
            self.tabs.setToolTip("Optimizer modules could not be imported.")

    def load_config(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def ensure_config_defaults(self, config):
        cfg = copy.deepcopy(config)
        ecosystem_setup = cfg.get('ecosystem_setup', {})
        detected_preset = self.detect_ecosystem_preset(ecosystem_setup)
        cfg.setdefault('ecosystem_preset', detected_preset)
        cfg.setdefault('species_fixed_params', {})
        cfg.setdefault('use_scientific_balancing', True)
        sim_settings = cfg.setdefault('simulation_settings', {})
        sim_settings.setdefault('stability_validation_ticks', 100)
        sim_settings.setdefault('stability_max_attempts', 20)
        interaction_settings = cfg.setdefault('interaction_settings', {})
        interaction_settings.setdefault('predator_handling_time', 0.01)
        interaction_settings.setdefault('max_energy_per_predator', 400.0)
        return cfg

    def detect_ecosystem_preset(self, setup_dict):
        for name, preset in ECOSYSTEM_PRESETS.items():
            if preset['setup'] == setup_dict:
                return name
        return "사용자 정의"

    def save_config(self, filepath):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            self.statusBar().showMessage(f"Configuration saved to '{filepath}'", 3000)
        except Exception as e:
            self.statusBar().showMessage(f"Failed to save configuration: {e}", 5000)

    def init_sim_ui(self):
        layout = QHBoxLayout(self.sim_tab)
        left_panel = QGroupBox("Settings & Controls")
        left_layout = QGridLayout()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(450)
        
        self.load_config_btn = QPushButton("Load Config")
        self.save_config_btn = QPushButton("Save Config")
        left_layout.addWidget(self.load_config_btn, 0, 0, 1, 2)
        left_layout.addWidget(self.save_config_btn, 0, 2, 1, 2)
        
        left_layout.addWidget(QLabel("Total Ticks:"), 1, 0)
        self.sim_ticks_slider = QSlider(Qt.Orientation.Horizontal)
        self.sim_ticks_slider.setRange(100, 2000)
        self.sim_ticks_label = QLabel()
        ticks_layout = QHBoxLayout()
        ticks_layout.addWidget(self.sim_ticks_slider)
        ticks_layout.addWidget(self.sim_ticks_label)
        left_layout.addLayout(ticks_layout, 1, 1, 1, 3)

        left_layout.addWidget(QLabel("GUI Update Interval:"), 2, 0)
        self.gui_update_slider = QSlider(Qt.Orientation.Horizontal)
        self.gui_update_slider.setRange(1, 20)
        self.gui_update_slider.setValue(1)
        self.gui_update_label = QLabel("Every 1 Tick")
        update_layout = QHBoxLayout()
        update_layout.addWidget(self.gui_update_slider)
        update_layout.addWidget(self.gui_update_label)
        left_layout.addLayout(update_layout, 2, 1, 1, 3)

        ecosystem_group = QGroupBox("Ecosystem Preset")
        ecosystem_layout = QGridLayout()
        ecosystem_group.setLayout(ecosystem_layout)
        self.ecosystem_combo = QComboBox()
        for name in ECOSYSTEM_PRESETS.keys():
            self.ecosystem_combo.addItem(name)
        self.ecosystem_combo.addItem("사용자 정의")
        self.ecosystem_description = QLabel("")
        self.ecosystem_description.setWordWrap(True)
        ecosystem_layout.addWidget(QLabel("Preset:"), 0, 0)
        ecosystem_layout.addWidget(self.ecosystem_combo, 0, 1)
        ecosystem_layout.addWidget(self.ecosystem_description, 1, 0, 1, 2)
        left_layout.addWidget(ecosystem_group, 3, 0, 1, 4)

        climate_group = QGroupBox("Climate Settings")
        climate_layout = QGridLayout()
        climate_group.setLayout(climate_layout)
        self.load_climate_btn = QPushButton("Load Climate CSV")
        self.clear_climate_btn = QPushButton("Reset")
        self.climate_file_label = QLabel("Using built-in scenario")
        self.climate_file_label.setWordWrap(True)
        climate_layout.addWidget(self.load_climate_btn, 0, 0)
        climate_layout.addWidget(self.clear_climate_btn, 0, 1)
        climate_layout.addWidget(self.climate_file_label, 1, 0, 1, 2)
        
        self.climate_scenario_label = QLabel("Built-in Scenario:")
        self.sim_scenario_combo = QComboBox()
        self.sim_scenario_combo.addItems(["Stable", "Linear_Warming", "RCP_8.5_Extreme"])
        self.initial_temp_label = QLabel("Initial Temp (°C):")
        self.initial_temp_spinbox = QDoubleSpinBox()
        self.initial_temp_spinbox.setRange(-50, 50)
        
        # [핵심 수정] 영양소 관련 UI 요소들을 제거합니다.
        # self.initial_nutrients_label = QLabel("Initial Nutrients:")
        # self.initial_nutrients_spinbox = QDoubleSpinBox()
        # self.initial_nutrients_spinbox.setRange(0, 10000)
        
        climate_layout.addWidget(self.climate_scenario_label, 2, 0)
        climate_layout.addWidget(self.sim_scenario_combo, 2, 1)
        climate_layout.addWidget(self.initial_temp_label, 3, 0)
        climate_layout.addWidget(self.initial_temp_spinbox, 3, 1)
        # climate_layout.addWidget(self.initial_nutrients_label, 4, 0)
        # climate_layout.addWidget(self.initial_nutrients_spinbox, 4, 1)
        left_layout.addWidget(climate_group, 4, 0, 1, 4)
        
        genetic_group = QGroupBox("Genetic Engine Parameters")
        genetic_layout = QGridLayout()
        genetic_group.setLayout(genetic_layout)
        genetic_layout.addWidget(QLabel("Initial Population:"), 0, 0)
        self.ge_pop_spinbox = QSpinBox()
        self.ge_pop_spinbox.setRange(1, 1000)
        genetic_layout.addWidget(self.ge_pop_spinbox, 0, 1)
        genetic_layout.addWidget(QLabel("Optimal Temp:"), 0, 2)
        self.ge_opttemp_spinbox = QDoubleSpinBox()
        self.ge_opttemp_spinbox.setRange(-50, 50)
        genetic_layout.addWidget(self.ge_opttemp_spinbox, 0, 3)
        genetic_layout.addWidget(QLabel("Mutation Rate:"), 1, 0)
        self.ge_mutrate_spinbox = QDoubleSpinBox()
        self.ge_mutrate_spinbox.setRange(0, 1)
        self.ge_mutrate_spinbox.setSingleStep(0.01)
        genetic_layout.addWidget(self.ge_mutrate_spinbox, 1, 1)
        genetic_layout.addWidget(QLabel("Mutation Strength:"), 1, 2)
        self.ge_mutstr_spinbox = QDoubleSpinBox()
        self.ge_mutstr_spinbox.setRange(0, 1)
        self.ge_mutstr_spinbox.setSingleStep(0.01)
        genetic_layout.addWidget(self.ge_mutstr_spinbox, 1, 3)
        left_layout.addWidget(genetic_group, 5, 0, 1, 4)

        species_fix_group = QGroupBox("Species Fixed Parameter")
        species_fix_layout = QGridLayout()
        species_fix_group.setLayout(species_fix_layout)
        self.species_fix_checkbox = QCheckBox("Enable fixed value")
        self.species_type_combo = QComboBox()
        for key, label in SPECIES_DISPLAY_NAMES.items():
            self.species_type_combo.addItem(label, userData=key)
        self.species_param_combo = QComboBox()
        self.species_fixed_value_spin = QDoubleSpinBox()
        self.species_fixed_value_spin.setDecimals(3)
        self.species_fixed_value_spin.setRange(0, 1000000)
        self.species_fixed_value_spin.setEnabled(False)
        self.species_param_combo.setEnabled(False)
        self.species_type_combo.setEnabled(False)
        species_fix_layout.addWidget(self.species_fix_checkbox, 0, 0, 1, 2)
        species_fix_layout.addWidget(QLabel("Species:"), 1, 0)
        species_fix_layout.addWidget(self.species_type_combo, 1, 1)
        species_fix_layout.addWidget(QLabel("Parameter:"), 2, 0)
        species_fix_layout.addWidget(self.species_param_combo, 2, 1)
        species_fix_layout.addWidget(QLabel("Value:"), 3, 0)
        species_fix_layout.addWidget(self.species_fixed_value_spin, 3, 1)
        left_layout.addWidget(species_fix_group, 6, 0, 1, 4)

        control_group = QGroupBox("Execution")
        control_layout = QHBoxLayout()
        control_group.setLayout(control_layout)
        self.sim_start_btn = QPushButton("▶ Start")
        self.sim_stop_btn = QPushButton("❚❚ Stop")
        self.sim_reset_btn = QPushButton("■ Reset")
        self.save_plots_btn = QPushButton("📈 Save Plots")
        self.sim_stop_btn.setEnabled(False)
        control_layout.addWidget(self.sim_start_btn)
        control_layout.addWidget(self.sim_stop_btn)
        control_layout.addWidget(self.sim_reset_btn)
        control_layout.addWidget(self.save_plots_btn)
        left_layout.addWidget(control_group, 7, 0, 1, 4)
        
        self.sim_progress_bar = QProgressBar()
        left_layout.addWidget(self.sim_progress_bar, 8, 0, 1, 4)
        left_layout.setRowStretch(9, 1)

        right_panel = QGroupBox("Real-time Visualization")
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        self.pop_plot_widget = pg.PlotWidget(title="Population Dynamics (Log Scale)")
        self.pop_plot_widget.addLegend(offset=(-10, 10))
        plot_item = self.pop_plot_widget.getPlotItem()
        plot_item.setLogMode(y=True)
        plot_item.getAxis('left').setLabel('Population')
        plot_item.getAxis('bottom').setLabel('Tick')
        plot_item.showGrid(x=True, y=True, alpha=0.3)
        plot_item.setLimits(yMin=0)
        
        self.env_plot_widget = pg.PlotWidget(title="Environment & Genetic Adaptation")
        self.env_plot_widget.addLegend(offset=(-10, 10))
        p = self.env_plot_widget.getPlotItem()
        p.getAxis('left').setLabel('Temperature (°C)', color='#FF6347')
        p.getAxis('bottom').setLabel('Tick')
        p.showGrid(x=True, y=True, alpha=0.3)
        p.showAxis('right')
        p.getAxis('right').setLabel('Avg. Trait Value', color='#1E90FF')
        
        right_layout.addWidget(self.pop_plot_widget)
        right_layout.addWidget(self.env_plot_widget)
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        
        self.load_config_btn.clicked.connect(self.on_load_config)
        self.save_config_btn.clicked.connect(self.on_save_config)
        self.sim_ticks_slider.valueChanged.connect(lambda v: self.sim_ticks_label.setText(f"{v} Ticks"))
        self.gui_update_slider.valueChanged.connect(lambda v: self.gui_update_label.setText(f"Every {v} Ticks"))
        self.load_climate_btn.clicked.connect(self.on_load_climate_csv)
        self.clear_climate_btn.clicked.connect(self.on_clear_climate_csv)
        self.ecosystem_combo.currentTextChanged.connect(self.on_ecosystem_changed)
        self.species_fix_checkbox.toggled.connect(self.on_species_fix_toggled)
        self.species_type_combo.currentIndexChanged.connect(self.on_species_type_changed)
        self.species_param_combo.currentIndexChanged.connect(self.on_species_param_changed)
        self.sim_start_btn.clicked.connect(self.start_simulation)
        self.sim_stop_btn.clicked.connect(self.stop_simulation)
        self.sim_reset_btn.clicked.connect(self.reset_simulation)
        self.save_plots_btn.clicked.connect(self.on_save_plots)
        
        self.update_ui_from_config()

    def init_optim_ui(self):
        layout = QVBoxLayout(self.optim_tab)
        control_group = QGroupBox("Controls & Status")
        control_layout = QGridLayout()
        control_group.setLayout(control_layout)
        control_group.setMaximumHeight(200)

        self.load_target_btn = QPushButton("Select Target Data")
        self.target_file_label = QLabel("Default: target_data.csv")
        control_layout.addWidget(self.load_target_btn, 0, 0)
        control_layout.addWidget(self.target_file_label, 0, 1, 1, 2)
        
        self.optim_start_btn = QPushButton("▶ Start Optimization")
        self.optim_stop_btn = QPushButton("❚❚ Stop")
        self.optim_stop_btn.setEnabled(False)
        self.optim_apply_btn = QPushButton("✔ Apply Best Results")
        self.optim_apply_btn.setEnabled(False)
        control_layout.addWidget(self.optim_start_btn, 1, 0)
        control_layout.addWidget(self.optim_stop_btn, 1, 1)
        control_layout.addWidget(self.optim_apply_btn, 1, 2)
        
        self.optim_progress_bar = QProgressBar()
        control_layout.addWidget(self.optim_progress_bar, 2, 0, 1, 3)
        
        results_group = QGroupBox("Log & Results")
        results_layout = QHBoxLayout()
        results_group.setLayout(results_layout)
        self.optim_log_text = QTextEdit()
        self.optim_log_text.setReadOnly(True)
        self.optim_log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.optim_results_text = QTextEdit()
        self.optim_results_text.setReadOnly(True)
        self.optim_results_text.setPlaceholderText("Best parameters will be displayed here upon completion.")
        results_layout.addWidget(self.optim_log_text, 2)
        results_layout.addWidget(self.optim_results_text, 1)
        layout.addWidget(control_group)
        layout.addWidget(results_group)
        
        self.load_target_btn.clicked.connect(self.on_load_target_csv)
        self.optim_start_btn.clicked.connect(self.start_optimization)
        self.optim_stop_btn.clicked.connect(self.stop_optimization)
        self.optim_apply_btn.clicked.connect(self.apply_optimized_params)

    def update_ui_from_config(self, config_to_use=None):
        config = config_to_use if config_to_use else self.config
        ss = config.get('simulation_settings', {})
        cs = config.get('climate_scenario', {})
        gp = config.get('genetic_engine_params', {})
        self.sim_ticks_slider.setValue(ss.get('total_ticks', 500))
        self.sim_ticks_label.setText(f"{ss.get('total_ticks', 500)} Ticks")
        self.sim_scenario_combo.setCurrentText(cs.get('scenario_name', 'Stable'))
        self.initial_temp_spinbox.setValue(cs.get('initial_temp', 15.0))
        # [핵심 수정] 영양소 관련 UI 업데이트 코드 제거
        # self.initial_nutrients_spinbox.setValue(cs.get('initial_nutrients', 100.0))
        if 'tertiary_consumer_apex' in config.get('ecosystem_setup', {}):
             self.ge_pop_spinbox.setValue(gp.get('initial_population', 100))
             self.ge_opttemp_spinbox.setValue(gp.get('optimal_temperature', 15.0))
             self.ge_mutrate_spinbox.setValue(gp.get('mutation_rate', 0.1))
             self.ge_mutstr_spinbox.setValue(gp.get('mutation_strength', 0.05))
        preset_name = config.get('ecosystem_preset', self.detect_ecosystem_preset(config.get('ecosystem_setup', {})))
        self._suppress_ecosystem_events = True
        if preset_name not in [*ECOSYSTEM_PRESETS.keys(), "사용자 정의"]:
            preset_name = "사용자 정의"
        self.ecosystem_combo.setCurrentText(preset_name)
        description = ECOSYSTEM_PRESETS.get(preset_name, {}).get('description', "사용자 정의 생태계 구성입니다.")
        self.ecosystem_description.setText(description)
        self._suppress_ecosystem_events = False

        fixed_params = config.get('species_fixed_params', {})
        if fixed_params:
            species_key, params = next(iter(fixed_params.items()))
            param_key, value = next(iter(params.items())) if params else (None, None)
            if species_key in SPECIES_DISPLAY_NAMES:
                self.species_fix_checkbox.setChecked(True)
                index = self.species_type_combo.findData(species_key)
                if index != -1:
                    self.species_type_combo.setCurrentIndex(index)
                self.populate_species_param_options()
                param_index = self.species_param_combo.findData(param_key)
                if param_index != -1:
                    self.species_param_combo.setCurrentIndex(param_index)
                self.update_species_value_spin_range(species_key, param_key)
                if value is not None:
                    self.species_fixed_value_spin.setValue(value)
            else:
                self.species_fix_checkbox.setChecked(False)
        else:
            self.species_fix_checkbox.setChecked(False)
            self.species_type_combo.setEnabled(False)
            self.species_param_combo.setEnabled(False)
            self.species_fixed_value_spin.setEnabled(False)
        self.setWindowTitle(f"SERM - {os.path.basename(self.current_config_path)}")

    def update_config_from_ui(self):
        self.config['simulation_settings']['total_ticks'] = self.sim_ticks_slider.value()
        cs = self.config.get('climate_scenario', {})
        cs['scenario_name'] = self.sim_scenario_combo.currentText()
        cs['initial_temp'] = self.initial_temp_spinbox.value()
        # [핵심 수정] 영양소 관련 config 업데이트 코드 제거
        # cs['initial_nutrients'] = self.initial_nutrients_spinbox.value()
        if 'genetic_engine_params' in self.config:
            gp = self.config['genetic_engine_params']
            gp['initial_population'] = self.ge_pop_spinbox.value()
            gp['optimal_temperature'] = self.ge_opttemp_spinbox.value()
            gp['mutation_rate'] = self.ge_mutrate_spinbox.value()
            gp['mutation_strength'] = self.ge_mutstr_spinbox.value()
        selected_preset = self.ecosystem_combo.currentText()
        if selected_preset in ECOSYSTEM_PRESETS:
            self.config['ecosystem_preset'] = selected_preset
            self.config['ecosystem_setup'] = copy.deepcopy(ECOSYSTEM_PRESETS[selected_preset]['setup'])
        else:
            self.config['ecosystem_preset'] = '사용자 정의'
        fixed_params_cfg = self.config.setdefault('species_fixed_params', {})
        if self.species_fix_checkbox.isChecked():
            species_key = self.species_type_combo.currentData()
            param_key = self.species_param_combo.currentData()
            value = self.species_fixed_value_spin.value()
            if isinstance(value, float) and param_key == 'initial_population':
                value = int(value)
            if species_key and param_key:
                fixed_params_cfg.clear()
                fixed_params_cfg[species_key] = {param_key: value}
        else:
            fixed_params_cfg.clear()

    def on_load_config(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Load Configuration File", "", "JSON Files (*.json)")
        if filepath:
            self.config = self.load_config(filepath)
            if self.config:
                self.config = self.ensure_config_defaults(self.config)
            self.current_config_path = filepath
            self.update_ui_from_config()
            self.statusBar().showMessage(f"Loaded configuration from '{filepath}'", 3000)

    def on_save_config(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Configuration File", self.current_config_path, "JSON Files (*.json)")
        if filepath:
            self.update_config_from_ui()
            self.save_config(filepath)
            self.current_config_path = filepath

    def on_load_climate_csv(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Load Climate Data", "", "CSV Files (*.csv)")
        if filepath:
            self.climate_csv_path = filepath
            self.climate_file_label.setText(f"Loaded: {os.path.basename(filepath)}")
            self.toggle_climate_controls(False)

    def on_clear_climate_csv(self):
        self.climate_csv_path = None
        self.climate_file_label.setText("Using built-in scenario")
        self.toggle_climate_controls(True)
        self.update_ui_from_config()

    def on_load_target_csv(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Load Optimizer Target Data", "", "CSV Files (*.csv)")
        if filepath:
            self.target_csv_path = filepath
            self.target_file_label.setText(f"Loaded: {os.path.basename(filepath)}")

    def toggle_climate_controls(self, enabled):
        self.climate_scenario_label.setEnabled(enabled)
        self.sim_scenario_combo.setEnabled(enabled)
        self.initial_temp_label.setEnabled(enabled)
        self.initial_temp_spinbox.setEnabled(enabled)
        # [핵심 수정] 영양소 관련 UI 활성화/비활성화 코드 제거
        # self.initial_nutrients_label.setEnabled(enabled)
        # self.initial_nutrients_spinbox.setEnabled(enabled)

    def generate_validated_species_list(self, config):
        sim_settings = config.get('simulation_settings', {})
        validation_ticks = sim_settings.get('stability_validation_ticks', 100)
        max_attempts = sim_settings.get('stability_max_attempts', 20)
        use_balancing = config.get('use_scientific_balancing', True)
        os.makedirs('results', exist_ok=True)
        temp_log_path = os.path.join('results', 'temp_gui_validation.csv')

        for attempt in range(1, max_attempts + 1):
            if use_balancing:
                species_list = generate_scientifically_balanced_ecosystem(
                    config.get('ecosystem_setup', {}),
                    config
                )
            else:
                species_list = generate_species_from_archetypes(
                    config.get('ecosystem_setup', {}),
                    config.get('genetic_engine_params'),
                    config.get('species_fixed_params')
                )

            if validation_ticks <= 0:
                return species_list

            validation_config = copy.deepcopy(config)
            validation_config['simulation_settings'] = copy.deepcopy(config.get('simulation_settings', {}))
            validation_config['simulation_settings']['results_filename'] = temp_log_path

            validator = SimulationRunner(
                config=validation_config,
                species_list_override=copy.deepcopy(species_list),
                is_first_run=False
            )
            last_tick, is_extinct = validator.run(verbose=False, ticks_override=validation_ticks)

            apex_alive = any(len(engine.population) > 0 for engine in validator.genetic_engines.values())

            if os.path.exists(temp_log_path):
                try:
                    os.remove(temp_log_path)
                except OSError:
                    pass

            if (not is_extinct or last_tick >= validation_ticks) and apex_alive:
                return species_list

        raise RuntimeError("Unable to generate a stable ecosystem after multiple attempts.")

    def on_ecosystem_changed(self, preset_name):
        if self._suppress_ecosystem_events:
            return
        if preset_name in ECOSYSTEM_PRESETS:
            preset = ECOSYSTEM_PRESETS[preset_name]
            self.config['ecosystem_setup'] = copy.deepcopy(preset['setup'])
            self.config['ecosystem_preset'] = preset_name
            scenario = self.config.setdefault('climate_scenario', {})
            scenario['scenario_name'] = preset.get('default_scenario', scenario.get('scenario_name', 'Stable'))
            scenario['initial_temp'] = preset.get('initial_temp', scenario.get('initial_temp', 15.0))
            self.update_ui_from_config()
        else:
            self.config['ecosystem_preset'] = '사용자 정의'
            self.ecosystem_description.setText("사용자 정의 생태계 구성입니다.")

    def populate_species_param_options(self):
        species_key = self.species_type_combo.currentData()
        self.species_param_combo.blockSignals(True)
        self.species_param_combo.clear()
        if not species_key:
            self.species_param_combo.blockSignals(False)
            return
        archetype = SPECIES_ARCHETYPES.get(species_key, {})
        self.species_param_combo.addItem("초기 개체수", userData='initial_population')
        for param_name in archetype.get('param_ranges', {}).keys():
            self.species_param_combo.addItem(param_name, userData=param_name)
        self.species_param_combo.blockSignals(False)
        self.on_species_param_changed(self.species_param_combo.currentIndex())

    def update_species_value_spin_range(self, species_key, param_key):
        archetype = SPECIES_ARCHETYPES.get(species_key, {})
        if param_key == 'initial_population':
            base_range = archetype.get('base_pop', (1, 1000))
            self.species_fixed_value_spin.setDecimals(0)
            self.species_fixed_value_spin.setSingleStep(10)
            self.species_fixed_value_spin.setRange(base_range[0], base_range[1])
        else:
            value_range = archetype.get('param_ranges', {}).get(param_key, (0.0, 1.0))
            self.species_fixed_value_spin.setDecimals(4)
            self.species_fixed_value_spin.setSingleStep(max((value_range[1] - value_range[0]) / 100.0, 0.0001))
            self.species_fixed_value_spin.setRange(value_range[0], value_range[1])
        current_value = self.species_fixed_value_spin.value()
        if (current_value < self.species_fixed_value_spin.minimum() or
                current_value > self.species_fixed_value_spin.maximum()):
            self.species_fixed_value_spin.setValue(self.species_fixed_value_spin.minimum())

    def on_species_fix_toggled(self, checked):
        self.species_type_combo.setEnabled(checked)
        self.species_param_combo.setEnabled(checked)
        self.species_fixed_value_spin.setEnabled(checked)
        if checked:
            self.populate_species_param_options()

    def on_species_type_changed(self, _index):
        if not self.species_fix_checkbox.isChecked():
            return
        self.populate_species_param_options()

    def on_species_param_changed(self, _index):
        if not self.species_fix_checkbox.isChecked():
            return
        species_key = self.species_type_combo.currentData()
        param_key = self.species_param_combo.currentData()
        if not species_key or not param_key:
            return
        self.update_species_value_spin_range(species_key, param_key)
    
    def start_simulation(self):
        self.sim_start_btn.setEnabled(False)
        self.sim_stop_btn.setEnabled(True)
        self.reset_simulation()
        if self.optimized_config:
            source_config = self.optimized_config
            self.statusBar().showMessage("Starting simulation with optimized parameters.", 5000)
            self.optimized_config = None
        else:
            self.update_config_from_ui()
            source_config = self.config
            self.statusBar().showMessage("Starting simulation with current settings.", 3000)
        
        current_config = copy.deepcopy(source_config)
        if self.climate_csv_path:
            current_config['climate_scenario']['filepath'] = self.climate_csv_path
        elif 'filepath' in current_config['climate_scenario']:
             del current_config['climate_scenario']['filepath']

        try:
            species_list = self.generate_validated_species_list(current_config)
        except RuntimeError as e:
            self.sim_start_btn.setEnabled(True)
            self.sim_stop_btn.setEnabled(False)
            QMessageBox.warning(self, "Initialization Failed", str(e))
            return

        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        current_config['simulation_settings']['results_filename'] = os.path.join(results_dir, "gui_sim_log.csv")
        self.sim_worker = SimulationWorker(current_config, species_list=species_list)
        self.sim_worker.progress.connect(self.update_sim_progress)
        self.sim_worker.finished.connect(self.finish_simulation)
        self.sim_worker.start()

    def stop_simulation(self):
        if hasattr(self, 'sim_worker') and self.sim_worker.isRunning():
            self.sim_worker.stop()

    def reset_simulation(self):
        self.plot_data_streams = {}
        self.pop_plot_widget.clear()
        self.env_plot_widget.clear()
        self.pop_plot_widget.addLegend(offset=(-10, 10))
        self.env_plot_widget.addLegend(offset=(-10, 10))
        self.sim_progress_bar.setValue(0)
        self.plot_lines = {}
        self.statusBar().clearMessage()

    def update_sim_progress(self, tick, total_ticks, data):
        self.sim_progress_bar.setValue(int((tick / total_ticks) * 100))

        if not self.plot_lines:
            self.plot_data_streams = {key: [] for key in data}
            self.plot_lines = {}
            
            plot_configs = {
                'Producers_Pop': {'pen': pg.mkPen('#4CAF50', width=2), 'name': 'Producers'},
                'Consumers_Pop': {'pen': pg.mkPen('#FFC107', width=2), 'name': 'Primary Consumers'},
                'Apex_Predators_Pop': {'pen': pg.mkPen('#F44336', width=2), 'name': 'Apex Predators'},
                # Decomposer는 제거되었으므로 관련 코드 삭제
            }
            for key, config in plot_configs.items():
                if key in data:
                    self.plot_lines[key] = self.pop_plot_widget.plot(pen=config['pen'], name=config['name'])
            
            if 'Temperature' in data:
                self.plot_lines['Temperature'] = self.env_plot_widget.plot(pen=pg.mkPen('#FF6347', style=Qt.PenStyle.DashLine, width=2), name='Temperature')
            if 'Avg_Heat_Resistance' in data:
                self.plot_lines['Avg_Heat_Resistance'] = self.env_plot_widget.plot(pen=pg.mkPen('#1E90FF', style=Qt.PenStyle.DotLine, width=2), name='Avg Heat Resistance')
            if 'Avg_Foraging_Efficiency' in data:
                self.plot_lines['Avg_Foraging_Efficiency'] = self.env_plot_widget.plot(pen=pg.mkPen('#32CD32', style=Qt.PenStyle.DotLine, width=2), name='Avg Foraging Efficiency')

        for key, value in data.items():
            if key in self.plot_data_streams:
                self.plot_data_streams[key].append(value)

        if tick % self.gui_update_slider.value() == 0:
            ticks_so_far = self.plot_data_streams.get('Tick', [])
            for key, line in self.plot_lines.items():
                if key in self.plot_data_streams:
                    line.setData(x=ticks_so_far, y=self.plot_data_streams[key])

    def finish_simulation(self, message):
        self.sim_start_btn.setEnabled(True)
        self.sim_stop_btn.setEnabled(False)
        self.statusBar().showMessage(message, 5000)
        if self.plot_data_streams:
            ticks_so_far = self.plot_data_streams.get('Tick', [])
            for key, line in self.plot_lines.items():
                if key in self.plot_data_streams:
                    line.setData(x=ticks_so_far, y=self.plot_data_streams[key])
    
    def on_save_plots(self):
        if not self.plot_data_streams:
            QMessageBox.warning(self, "No Data", "There is no simulation data to save.")
            return
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Plots (Base Name)", "simulation_plot", "PNG Image (*.png)")
        if not filepath:
            return
        base_filepath, ext = os.path.splitext(filepath)
        pop_plot_path = f"{base_filepath}_population{ext}"
        env_plot_path = f"{base_filepath}_environment{ext}"
        try:
            pg.exporters.ImageExporter(self.pop_plot_widget.plotItem).export(pop_plot_path)
            pg.exporters.ImageExporter(self.env_plot_widget.plotItem).export(env_plot_path)
            self.statusBar().showMessage(f"Plots saved: {pop_plot_path} and {env_plot_path}", 5000)
            QMessageBox.information(self, "Save Complete", f"Two plot files have been saved successfully:\n\n1. {os.path.basename(pop_plot_path)}\n2. {os.path.basename(env_plot_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"An error occurred while saving plots: {e}\n{traceback.format_exc()}")

    def start_optimization(self):
        self.optim_start_btn.setEnabled(False)
        self.optim_stop_btn.setEnabled(True)
        self.optim_apply_btn.setEnabled(False)
        self.optim_log_text.clear()
        self.optim_results_text.clear()
        self.best_params = None
        self.optimized_config = None
        
        target_file = self.target_csv_path if self.target_csv_path else 'target_data.csv'
        if not os.path.exists(target_file):
            create_target_data_if_not_exists()
            if not self.target_csv_path:
                self.optim_log_text.append(f"Notice: '{target_file}' not found, created a new sample file.")
        
        self.optim_worker = OptimizerWorker(self.config, target_file)
        self.optim_worker.progress.connect(self.optim_log_text.append)
        self.optim_worker.update_progress_bar.connect(lambda cur, tot: self.optim_progress_bar.setValue(int(cur / tot * 100)))
        self.optim_worker.finished.connect(self.finish_optimization)
        self.optim_worker.start()

    def stop_optimization(self):
        if hasattr(self, 'optim_worker') and self.optim_worker.isRunning():
            self.optim_worker.stop()
            self.optim_log_text.append("\n... Requesting stop ...")
            
    def finish_optimization(self, best_params, message):
        self.optim_start_btn.setEnabled(True)
        self.optim_stop_btn.setEnabled(False)
        self.optim_log_text.append(f"\n--- {message} ---")
        if best_params:
            self.best_params = best_params
            self.optim_results_text.setText(json.dumps(best_params, indent=4))
            self.optim_apply_btn.setEnabled(True)
            self.optim_progress_bar.setValue(100)
        else:
            self.optim_progress_bar.setValue(0)
            self.optim_results_text.setPlaceholderText("Optimization failed or was stopped.")

    def apply_optimized_params(self):
        if not self.best_params:
            QMessageBox.warning(self, "Error", "No optimized results to apply.")
            return
        try:
            new_config = copy.deepcopy(self.config)
            for key, value in self.best_params.items():
                if key.startswith('config_'):
                    parts = key.split('_')
                    config_path = parts[1:]
                    sub_dict = new_config
                    try:
                        for part in config_path[:-1]:
                            sub_dict = sub_dict[part]
                        sub_dict[config_path[-1]] = value
                    except KeyError:
                        print(f"Warning: Could not apply optimized param '{key}'.")
            species_list = generate_species_from_archetypes(
                new_config['ecosystem_setup'],
                new_config.get('genetic_engine_params'),
                new_config.get('species_fixed_params')
            )
            for sp_data in species_list:
                sp_id = sp_data['id']
                if 'params' in sp_data:
                    for param_name, value in self.best_params.items():
                        if param_name.startswith(f'species_ID_{sp_id}_'):
                            sp_data['params'][param_name.replace(f'species_ID_{sp_id}_', '')] = value
            new_config['species_list_override'] = species_list
            self.optimized_config = new_config
            self.update_ui_from_config(config_to_use=self.optimized_config)
            self.optim_apply_btn.setEnabled(False)
            self.statusBar().showMessage("✔ Optimized parameters applied. Press 'Start' in the Simulator tab to run.", 10000)
            self.tabs.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "Apply Failed", f"An error occurred while applying parameters: {e}\n\n{traceback.format_exc()}")

if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
    
    sys.path.append(os.getcwd())
    app = QApplication(sys.argv)
    
    main_window = None
    splash = SplashScreen()

    def show_main_window():
        global main_window
        main_window = MainWindow()
        main_window.show()

    splash.finished.connect(show_main_window)
    splash.show_splash()
    
    sys.exit(app.exec())