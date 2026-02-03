import json
import os
import sys

from Deadline.Scripting import RepositoryUtils

repo_path = RepositoryUtils.GetRootDirectory()
general_scripts_path = os.path.join(repo_path, "custom", "scripts", "General", "PoolManager")
if general_scripts_path not in sys.path:
    sys.path.insert(0, general_scripts_path)

import PoolManagerConfig as config
from PoolManagerCore import DeadlinePoolManager

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "pool_distribution_config.json")
LOG_PATH = os.path.join(os.path.dirname(__file__), "pool_distribution_log.txt")

class DummySlider:
    def __init__(self, value):
        self._value = value
    def get_value(self):
        return self._value

def apply_distribution():
    if not os.path.exists(CONFIG_PATH):
        with open(LOG_PATH, "w", encoding="utf-8") as log_file:
            log_file.write(f"Configuration file not found at {CONFIG_PATH}. No changes applied.\n")
        return

    with open(CONFIG_PATH, encoding="utf-8") as f:
        pool_percentages = json.load(f)
    pool_sliders = {pool: DummySlider(val) for pool, val in pool_percentages.items()}
    manager = DeadlinePoolManager()
    manager.load_deadline_data()

    available_workers = manager.get_workers_by_states(config.ACTIVE_STATUSES)
    available_new_distribution = manager.get_new_distribution(available_workers, pool_sliders)

    disabled_workers = manager.get_workers_by_states(config.DISABLED_STATUSES)
    disabled_new_distribution = manager.get_new_distribution(disabled_workers, pool_sliders)

    for worker_name, pools in available_new_distribution.items():
        RepositoryUtils.SetPoolsForSlave(worker_name, pools)

    for worker_name, pools in disabled_new_distribution.items():
        RepositoryUtils.SetPoolsForSlave(worker_name, pools)

    with open(LOG_PATH, "w", encoding="utf-8") as log_file:
        log_file.write("Applied new pool distribution:\n")
        log_file.write("Available Workers:\n")
        for worker_name, pools in available_new_distribution.items():
            log_file.write(f"  {worker_name}: {', '.join(pools)}\n")
        log_file.write("Disabled Workers:\n")
        for worker_name, pools in disabled_new_distribution.items():
            log_file.write(f"  {worker_name}: {', '.join(pools)}\n")
        log_file.write("\n")

def __main__(*args):
    apply_distribution()