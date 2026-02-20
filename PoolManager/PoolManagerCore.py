import PoolManagerConfig as config
from Deadline.Scripting import RepositoryUtils
import re
from datetime import datetime

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
    
    def get_new_distribution(self, workers, slider_percentages):
        active_pool_percentages = {}
        disabled_pools = []
        for pool_name, slider in slider_percentages.items():
            if slider.get_value() > 0:
                active_pool_percentages[pool_name] = slider.get_value()
            else:
                disabled_pools.append(pool_name)
        
        normalized_percentages = self.get_normalized_percentages(active_pool_percentages)
        adjusted_percentages = self.get_adjusted_pool_percentages(normalized_percentages)
        workers_scores = {worker_name: self.get_worker_hardware_info(worker_name) for worker_name in workers}
        # We sort workers by best hardware score to assign them to the most important pools first
        sorted_scores = sorted(workers_scores.items(), key=lambda x: x[1], reverse=True)
        sorted_percentages = sorted(adjusted_percentages.items(), key=lambda x: x[1], reverse=True)
        new_distribution = self.get_weighted_snake_draft_distribution(sorted_scores, sorted_percentages)
        
        for _, pools in new_distribution.items():
            if disabled_pools:
                pools.extend(disabled_pools)
                disabled_pools.append(disabled_pools.pop(0)) # Shift disabled pools for next worker
            pools.insert(0, config.PRIORITY_POOL)
            pools.append(config.FALLBACK_POOL)
        
        return new_distribution

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
    
    def get_adjusted_pool_percentages(self, pool_percentages):
        job_percentages = self.get_job_percentages()
        new_pool_percentages = pool_percentages.copy()
        for pool in new_pool_percentages.keys():
            job_percentage = job_percentages.get(pool, 0)
            if job_percentage == 0:
                new_pool_percentages[pool] = 0
        return self.get_normalized_percentages(new_pool_percentages)
    
    def get_normalized_percentages(self, pool_percentages):
        total = sum(pool_percentages.values())
        if total > 0:
            normalization_factor = 100. / total
            return {pool_name: value * normalization_factor for pool_name, value in pool_percentages.items()}
        return pool_percentages

    def get_job_percentages(self):
        job_counts = {pool: 0 for pool in self.all_pools}
        total_jobs = 0
        for job in RepositoryUtils.GetJobs(True):
            job_counts[job.JobPool] += 1
            total_jobs += 1
        return job_counts
    
    def get_weighted_snake_draft_distribution(self, workers_scores, pool_percentages):
        """
        Distributes workers to pools by alternating between the highest and lowest scored workers,
        ensuring a balanced assignment according to specified pool percentages.
         Args:
             workers_scores (list of tuples): List of (worker_name, score) tuples
             pool_percentages (list of tuples): List of (pool_name, percentage) tuples
         Returns:
             dict: A dictionary mapping each worker to a list of pools ordered by assignment preference
        """
        worker_nb_per_pool = {}
        total_workers = len(workers_scores)
        total_percentages = 100.0
        for pool_name, percentage in pool_percentages:
            worker_nb = round(total_workers * percentage / total_percentages) if total_percentages > 0 else 0
            worker_nb_per_pool[pool_name] = worker_nb
            total_workers -= worker_nb
            total_percentages -= percentage

        worker_pool_assignement = {}
        scores = workers_scores.copy()
        pools = [pool_name for pool_name, _ in pool_percentages]
        pool_nb = len(pool_percentages)
        while scores:
            for i in range(pool_nb):
                if i < len(scores):
                    worker_pool_assignement[scores.pop(0)[0]] = pools.copy()
                else:
                    break
            for i in range(pool_nb):
                if i < len(scores):
                    worker_pool_assignement[scores.pop(-1)[0]] = pools.copy()
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

        for _, pools in worker_pool_assignement.items():
            assigned_pool = pool_order.pop(0)
            pools.remove(assigned_pool)
            pools.insert(0, assigned_pool)

        return worker_pool_assignement
    
    def log_pool_application(self, user, pool_percentages):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(config.LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{now}] Utilisateur: {user}\n")
            f.write("Pourcentages appliqués:\n")
            for pool, pct in pool_percentages.items():
                f.write(f"  {pool}: {pct}\n")
            f.write("\n")