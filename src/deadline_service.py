
try:
    from Deadline.Scripting import RepositoryUtils
except ImportError:
    import sys
    sys.path.append(r"C:\Program Files\Thinkbox\Deadline10\python")
    from Deadline.Scripting import RepositoryUtils

import json

class DeadlineService:
    def __init__(self):
        self.repo_utils = RepositoryUtils()

    def get_enabled_workers(self):
        data = self.repo_utils.GetSlaveInfoSettings(True)
        workers = json.loads(data)
        enabled_workers = [worker for worker in workers if worker["SlaveSettings"]["SlaveEnabled"]]
        return enabled_workers
    
    def get_disabled_workers(self):
        workers = self.repo_utils.GetSlaveNames(True)
        disabled_workers = [worker for worker in workers if not worker["SlaveSettings"]["SlaveEnabled"]]
        return disabled_workers
    
    def get_jobs_by_state_and_pool(self, state, pool):
        jobs = self.repo_utils.GetJobsInState(state)
        production_jobs = [job for job in jobs if job["JobPool"] == pool]
        return production_jobs
    
    def get_pools(self):
        return self.repo_utils.GetPoolNames()