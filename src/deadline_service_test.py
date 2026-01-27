import unittest
from deadline_service import DeadlineService

class TestDeadlineService(unittest.TestCase):
    def setUp(self):
        self.deadline_service = DeadlineService()

    def test_get_enabled_workers(self):
        enabled_workers = deadline_service.get_enabled_workers()
        assert isinstance(enabled_workers, list)
        for worker in enabled_workers:
            assert worker.SlaveSettings.SlaveEnabled is True

    def test_get_disabled_workers(self):
        disabled_workers = deadline_service.get_disabled_workers()
        assert isinstance(disabled_workers, list)
        for worker in disabled_workers:
            assert worker.SlaveSettings.SlaveEnabled is False

if __name__ == "__main__":
    unittest.main()