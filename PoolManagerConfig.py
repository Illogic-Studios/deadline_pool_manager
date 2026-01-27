# Pool qui doit toujours rester en première position
PRIORITY_POOL = "urgent"

# Pool qui doit toujours rester en dernière position (non distribué)
FALLBACK_POOL = "none"

# Poids pour le calcul du score hardware
# Score = CPUs × HARDWARE_WEIGHT_CPU + RAM_GB × HARDWARE_WEIGHT_RAM + VRAM_GB × HARDWARE_WEIGHT_VRAM
HARDWARE_WEIGHT_CPU = 1.0   # CPUs: poids normal
HARDWARE_WEIGHT_RAM = 0.5   # RAM: poids moyen
HARDWARE_WEIGHT_VRAM = 2.0  # VRAM: poids élevé (souvent le facteur limitant pour le rendu GPU)
