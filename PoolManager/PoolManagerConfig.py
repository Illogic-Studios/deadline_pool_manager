import os

# Pool qui doit toujours rester en première position
PRIORITY_POOL = "urgent"

# Pool qui doit toujours rester en dernière position (non distribué)
FALLBACK_POOL = "none"

# Statuts des workers
ACTIVE_STATUSES = ["Idle", "Rendering"]
DISABLED_STATUSES = ["Offline", "Stalled", "Disabled"]

# Status des jobs
JOB_PENDING_STATUSES = ["Active", "Pending", "Rendering"]

# Poids pour le calcul du score hardware
# Score = CPUs × HARDWARE_WEIGHT_CPU + RAM_GB × HARDWARE_WEIGHT_RAM + VRAM_GB × HARDWARE_WEIGHT_VRAM
HARDWARE_WEIGHT_CPU = 1.0   # CPUs: poids normal
HARDWARE_WEIGHT_RAM = 0.5   # RAM: poids moyen
HARDWARE_WEIGHT_VRAM = 2.0  # VRAM: poids élevé (souvent le facteur limitant pour le rendu GPU)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "pool_distribution_config.json")
LOG_PATH = os.path.join(os.path.dirname(__file__), "pool_distribution_log.txt")