import PoolManagerConfig as config
from Deadline.Scripting import RepositoryUtils


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