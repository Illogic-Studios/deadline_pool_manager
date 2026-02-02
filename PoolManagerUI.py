import sys
import os
import json

from Deadline.Scripting import ClientUtils, RepositoryUtils

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
    valueChanged = Signal(str, int)

    def __init__(self, pool_name, parent=None):
        super().__init__(parent)
        self.pool_name = pool_name
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Pool name
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

        self.setWindowTitle("Deadline Pool Manager")
        self.setGeometry(100, 100, 1200, 800)

        self.manager.load_deadline_data()
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)

        # Deadline informations
        workers_count = len(self.manager.workers)
        pools_count = len(self.manager.all_pools)
        self.info_label = QLabel(f"{workers_count} workers | {pools_count} pools | Priority pool: '{config.PRIORITY_POOL}'")
        config_layout.addWidget(self.info_label)

        # Documentation link
        self.doc_link = QLabel('<a href="#" style="color: #0066cc;">📖 Documentation</a>')
        self.doc_link.setOpenExternalLinks(False)
        self.doc_link.linkActivated.connect(self.open_documentation)
        self.doc_link.setStyleSheet("QLabel { padding: 3px; }")
        self.doc_link.setCursor(Qt.PointingHandCursor)
        config_layout.addWidget(self.doc_link)

        # Pools configuration
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

        self.create_pool_sliders()

        # Buttons
        buttons_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh Deadline Data")
        self.refresh_btn.clicked.connect(self.load_deadline_data)
        buttons_layout.addWidget(self.refresh_btn)

        self.equal_btn = QPushButton("Set Equal Distribution")
        self.equal_btn.clicked.connect(self.set_equal_distribution)
        buttons_layout.addWidget(self.equal_btn)

        self.apply_sliders_btn = QPushButton("Apply and Save Distribution")
        self.apply_sliders_btn.clicked.connect(self.apply_and_save_distribution)
        buttons_layout.addWidget(self.apply_sliders_btn)

        config_layout.addLayout(buttons_layout)

        main_layout.addWidget(config_widget)

    def open_documentation(self):
        url = "https://www.notion.so/illogic/Dynamic-Priority-DeadlinePoolManager_GUI-2c49d24ae7e3804b858dffcbf16d76ee"
        QDesktopServices.openUrl(QUrl(url))

    def create_pool_sliders(self):
        available_pools = [pool for pool in self.manager.all_pools if pool != config.PRIORITY_POOL and pool != config.FALLBACK_POOL]

        self.pool_sliders = {}
        for pool in sorted(available_pools):
            slider_widget = PoolSlider(pool)
            self.pools_container_layout.addWidget(slider_widget)
            self.pool_sliders[pool] = slider_widget

        self.load_deadline_data()

    def load_deadline_data(self):
        available_pools = [pool for pool in self.manager.all_pools if pool != config.PRIORITY_POOL and pool != config.FALLBACK_POOL]

        pool_stats = {pool: 0 for pool in available_pools}
        for _, pools in self.manager.current_pool_config.items():
            if pools:
                if pools[0] != config.PRIORITY_POOL:
                    pool_stats[pools[0]] += 1
                elif len(pools) > 1:
                    pool_stats[pools[1]] += 1

        total_workers = len(self.manager.workers)
        for pool_name, count in pool_stats.items():
            percentage = int(count / total_workers * 100) if total_workers else 0
            self.pool_sliders[pool_name].set_value(percentage)

    def set_equal_distribution(self):
        for slider in self.pool_sliders.values():
            slider.set_value(50)

    def apply_and_save_distribution(self):
        available_workers = self.manager.get_workers_by_states(config.ACTIVE_STATUSES)
        available_new_distribution = self.manager.get_new_distribution(available_workers, self.pool_sliders)

        disabled_workers = self.manager.get_workers_by_states(config.DISABLED_STATUSES)
        disabled_new_distribution = self.manager.get_new_distribution(disabled_workers, self.pool_sliders)

        reply = QMessageBox.question(self, "Confirm", "Are you sure you want to apply the new pool distribution to the workers?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for worker_name, pools in available_new_distribution.items():
                    RepositoryUtils.SetPoolsForSlave(worker_name, pools)
            for worker_name, pools in disabled_new_distribution.items():
                    RepositoryUtils.SetPoolsForSlave(worker_name, pools)

            print("Available Workers New Distribution:")
            for worker, pools in available_new_distribution.items():
                print(f"{worker}: {pools}")

            print("\nDisabled Workers New Distribution:")
            for worker, pools in disabled_new_distribution.items():
                print(f"{worker}: {pools}")

            pool_percentages = {pool_name: slider.get_value() for pool_name, slider in self.pool_sliders.items() if slider.get_value() > 0}
            config_file = os.path.join(repo_path, "custom", "scripts", "General", "pool_distribution_config.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(pool_percentages, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Success", f"The new pool distribution has been applied successfully. \nThe configuration has also been saved to \n{config_file}")

            self.manager.load_deadline_data()
            self.load_deadline_data()

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