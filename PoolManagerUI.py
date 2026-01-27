import sys
import os
import json

# Imports Deadline
from Deadline.Scripting import ClientUtils, RepositoryUtils

# Import module commun
repo_path = RepositoryUtils.GetRootDirectory()
general_scripts_path = os.path.join(repo_path, "custom", "scripts", "General")
if general_scripts_path not in sys.path:
    sys.path.insert(0, general_scripts_path)

try:
    from PySide2.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                   QHBoxLayout, QLabel, QPushButton, QSlider,
                                   QSpinBox, QTableWidget, QTableWidgetItem,
                                   QGroupBox, QScrollArea, QTextEdit, QMessageBox,
                                   QFileDialog, QSplitter, QCheckBox)
    from PySide2.QtCore import Qt, Signal, QUrl
    from PySide2.QtGui import QColor, QFont, QDesktopServices
except ImportError:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                 QHBoxLayout, QLabel, QPushButton, QSlider,
                                 QSpinBox, QTableWidget, QTableWidgetItem,
                                 QGroupBox, QScrollArea, QTextEdit, QMessageBox,
                                 QFileDialog, QSplitter, QCheckBox)
    from PyQt5.QtCore import Qt, pyqtSignal as Signal, QUrl
    from PyQt5.QtGui import QColor, QFont, QDesktopServices

import PoolManagerConfig as config
from PoolManagerCore import DeadlinePoolManager


class PoolSlider(QWidget):
    """Widget personnalisé : pool + slider + spinbox"""

    valueChanged = Signal(str, int)

    def __init__(self, pool_name, parent=None):
        super().__init__(parent)
        self.pool_name = pool_name
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Nom de la pool
        label = QLabel(self.pool_name)
        label.setMinimumWidth(150)
        font = QFont()
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(10)
        self.slider.valueChanged.connect(self.on_value_changed)
        layout.addWidget(self.slider)

        # SpinBox
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(0)
        self.spinbox.setMaximum(100)
        self.spinbox.setValue(0)
        self.spinbox.valueChanged.connect(self.on_spinbox_changed)
        layout.addWidget(self.spinbox)

    def on_value_changed(self, value):
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(value)
        self.spinbox.blockSignals(False)
        self.valueChanged.emit(self.pool_name, value)

    def on_spinbox_changed(self, value):
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self.valueChanged.emit(self.pool_name, value)

    def get_value(self):
        return self.slider.value()

    def set_value(self, value):
        self.slider.setValue(value)


class DeadlinePoolManagerGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.manager = DeadlinePoolManager()
        self.new_distribution = {}
        self.pool_sliders = {}

        self.setWindowTitle("Deadline Pool Manager V2")
        self.setGeometry(100, 100, 1200, 800)

        self.setup_ui()
        self.load_deadline_data()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Splitter vertical
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # === PARTIE HAUTE : Configuration ===
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)

        # Infos Deadline
        self.info_label = QLabel("Loading data...")
        config_layout.addWidget(self.info_label)

        # Documentation link
        self.doc_link = QLabel('<a href="#" style="color: #0066cc;">📖 Documentation</a>')
        self.doc_link.setOpenExternalLinks(False)
        self.doc_link.linkActivated.connect(self.open_documentation)
        self.doc_link.setStyleSheet("QLabel { padding: 3px; }")
        self.doc_link.setCursor(Qt.PointingHandCursor)
        config_layout.addWidget(self.doc_link)

        # Zone des sliders de pools
        pools_group = QGroupBox("Pools configuration (weights)")
        pools_layout = QVBoxLayout()

        self.pools_scroll = QScrollArea()
        self.pools_scroll.setWidgetResizable(True)
        self.pools_container = QWidget()
        self.pools_container_layout = QVBoxLayout(self.pools_container)
        self.pools_scroll.setWidget(self.pools_container)

        pools_layout.addWidget(self.pools_scroll)

        pools_group.setLayout(pools_layout)
        config_layout.addWidget(pools_group)

        # Boutons d'action
        buttons_layout = QHBoxLayout()

        self.equal_btn = QPushButton("Automatic Equal Distribution")
        self.equal_btn.clicked.connect(self.set_equal_distribution)
        buttons_layout.addWidget(self.equal_btn)

        self.save_config_btn = QPushButton("Save Configuration")
        self.save_config_btn.clicked.connect(self.save)
        buttons_layout.addWidget(self.save_config_btn)

        config_layout.addLayout(buttons_layout)

        splitter.addWidget(config_widget)

    def open_documentation(self):
        url = "https://www.notion.so/illogic/Dynamic-Priority-DeadlinePoolManager_GUI-2c49d24ae7e3804b858dffcbf16d76ee"
        QDesktopServices.openUrl(QUrl(url))

    def load_deadline_data(self):
        self.manager.load_deadline_data()
        workers_count = len(self.manager.workers)
        pools_count = len(self.manager.all_pools)
        
        self.info_label.setText(f"{workers_count} workers | {pools_count} pools | Pool prioritaire: '{config.PRIORITY_POOL}'")

        # Créer les sliders seulement si nécessaire (première fois ou si pools ont changé)
        # Exclure la pool prioritaire et la pool fallback
        available_pools = [pool for pool in self.manager.all_pools if pool != config.PRIORITY_POOL and pool != config.FALLBACK_POOL]
        if not self.pool_sliders or set(self.pool_sliders.keys()) != set(available_pools):
            self.create_pool_sliders()

        # Calculer et afficher la distribution actuelle sur les sliders
        self.display_current_distribution_on_sliders()

    def create_pool_sliders(self):
        """Crée les sliders pour chaque pool"""
        # Supprimer les anciens widgets
        for i in reversed(range(self.pools_container_layout.count())):
            item = self.pools_container_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        self.pool_sliders = {}

        # Pools disponibles (sans la pool prioritaire et la pool fallback)
        available_pools = [p for p in self.manager.all_pools
                         if p != config.PRIORITY_POOL and p != config.FALLBACK_POOL]

        for pool in sorted(available_pools):
            slider_widget = PoolSlider(pool)
            self.pools_container_layout.addWidget(slider_widget)
            self.pool_sliders[pool] = slider_widget

        self.pools_container_layout.addStretch()

        # Ajuster automatiquement la taille de la section des pools
        # Chaque slider fait environ 50 pixels de hauteur + marges
        num_pools = len(available_pools)
        slider_height = 50
        base_height = 100  # Hauteur de base pour les marges et le titre
        calculated_height = base_height + (num_pools * slider_height)

        # Limiter entre 200 et 500 pixels
        optimal_height = max(200, min(500, calculated_height))

        # Trouver le parent QGroupBox et définir sa hauteur minimale
        pools_group = self.pools_scroll.parent().parent()
        if pools_group:
            pools_group.setMinimumHeight(optimal_height)

    def display_current_distribution_on_sliders(self):
        """Calcule la distribution actuelle et ajuste les sliders en conséquence"""
        if not self.manager.workers or not self.manager.current_pool_config:
            return

        # Calculer les statistiques actuelles (pools en priorité, excluant la pool prioritaire et fallback)
        pool_stats = {}
        available_pools = [p for p in self.manager.all_pools
                         if p != config.PRIORITY_POOL and p != config.FALLBACK_POOL]

        for pool in available_pools:
            pool_stats[pool] = 0

        total_workers = len(self.manager.workers)

        # Compter combien de workers ont chaque pool en priorité (après la pool prioritaire)
        for worker_name, pools in self.manager.current_pool_config.items():
            if not pools:
                continue

            # Trouver la première pool après la pool prioritaire
            priority_pool_index = 0
            if pools[0] == config.PRIORITY_POOL and len(pools) > 1:
                priority_pool_index = 1

            if priority_pool_index < len(pools):
                first_pool = pools[priority_pool_index]
                if first_pool in pool_stats:
                    pool_stats[first_pool] += 1

        # Calculer les pourcentages et ajuster les sliders
        print("\n" + "="*80)
        print("DISTRIBUTION ACTUELLE DETECTEE")
        print("="*80)

        # Bloquer les signaux pendant la mise à jour pour éviter les bugs graphiques
        for slider in self.pool_sliders.values():
            slider.blockSignals(True)

        for pool_name, count in pool_stats.items():
            percentage = int((count / total_workers * 100)) if total_workers > 0 else 0
            if pool_name in self.pool_sliders:
                self.pool_sliders[pool_name].set_value(percentage)
            print(f"{pool_name:20s} : {count:3d} workers ({percentage}%)")

        # Réactiver les signaux
        for slider in self.pool_sliders.values():
            slider.blockSignals(False)

        print("="*80 + "\n")

    def set_equal_distribution(self):
        pass

    def save(self):
        pass


_window_instance = None

def __main__(*args):
    global _window_instance

    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    _window_instance = DeadlinePoolManagerGUI()
    _window_instance.show()
    _window_instance.raise_()
    _window_instance.activateWindow()

if __name__ == '__main__':
    __main__()