import PoolManagerConfig as config
from Deadline.Scripting import RepositoryUtils
import re

class DeadlinePoolManager:
    def __init__(self):
        self.workers = []
        self.all_pools = []
        self.current_pool_config = {}

    def load_deadline_data(self):
        self.workers = list(RepositoryUtils.GetSlaveNames(True))
        self.all_pools = list(RepositoryUtils.GetPoolNames())

        self.current_pool_config = {}
        for worker_name in self.workers:
            settings = RepositoryUtils.GetSlaveSettings(worker_name, False)
            pools = list(settings.SlavePools)
            self.current_pool_config[worker_name] = pools
    
    def get_workers_by_states(self, states):
        workers = []
        for worker in self.workers:
            info = RepositoryUtils.GetSlaveInfo(worker, False)
            if info.SlaveState in states:
                workers.append(worker)
        return workers
    
    def calculate_new_distribution(self, workers, pool_percentages):
        workers_scores = {worker_name: self.get_worker_hardware_info(worker_name) for worker_name in workers}
        sorted_scores = sorted(workers_scores.items(), key=lambda x: x[1], reverse=True)
        sorted_percentages = sorted(pool_percentages.items(), key=lambda x: x[1])
        return self.weighted_snake_draft_distribution(sorted_scores, sorted_percentages)

    def get_worker_hardware_info(self, worker_name):
        info = RepositoryUtils.GetSlaveInfo(worker_name, False)
        settings = RepositoryUtils.GetSlaveSettings(worker_name, False)
        cpu_nb = info.MachineCPUs
        ram_gb = info.MachineMemory / pow(1024.0, 3)
        vram_gb = self.extract_go_from_string(settings.SlaveComment)
        return cpu_nb * config.HARDWARE_WEIGHT_CPU + ram_gb * config.HARDWARE_WEIGHT_RAM + vram_gb * config.HARDWARE_WEIGHT_VRAM
    
    def extract_go_from_string(self, s):
        match = re.search(r"(\d+)", s)
        return float(match.group()) if match else 0
    
    def weighted_snake_draft_distribution(self, workers_scores, pool_percentages):
        worker_nb_per_pool = {}
        total_workers = len(workers_scores)
        total_percentages = 0.0
        for pool_name, percentage in pool_percentages.items():
            worker_nb = round(total_workers * percentage / (100.0 - total_percentages))
            worker_nb_per_pool[pool_name] = worker_nb
            total_workers -= worker_nb
            total_percentages += percentage

        worker_order = []
        scores = workers_scores.copy()
        pool_nb = len(pool_percentages)
        while scores:
            for i in range(pool_nb):
                if i < len(scores):
                    worker_order.append(scores.pop(0))
                else:
                    break
            for i in range(pool_nb):
                if i < len(scores):
                    worker_order.append(scores.pop(-1))
                else:
                    break

        pool_order = []
        total_workers = len(workers_scores)
        while total_workers > 0:
            for pool_name in worker_nb_per_pool.keys():
                if worker_nb_per_pool[pool_name] > 0:
                    pool_order.append(pool_name)
                    worker_nb_per_pool[pool_name] -= 1
                    total_workers -= 1

        pool_assignments = {pool: [] for pool in worker_nb_per_pool.keys()}
        for i in range(len(worker_order)):
            pool_name = pool_order[i]
            worker_name = worker_order[i]
            pool_assignments[pool_name].append(worker_name)

        return pool_assignments