
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Цветовая палитра (Modern Dark Slate)
COLOR_BG = (15, 23, 42)
COLOR_GRID = (30, 41, 59)
COLOR_WALL = (71, 85, 105)
COLOR_PARKING = (22, 163, 74)
COLOR_PARKING_BORDER = (74, 222, 128)
COLOR_CAR_AI = (37, 99, 235)
COLOR_CAR_BEST = (239, 68, 68)
COLOR_CAR_MANUAL = (245, 158, 11)
COLOR_SENSOR = (148, 163, 184)
COLOR_TEXT = (241, 245, 249)

# Физика автомобиля
CAR_WIDTH = 34
CAR_HEIGHT = 60
MAX_SPEED = 4.0
REVERSE_MAX_SPEED = -2.0
ACCELERATION = 0.1
STEER_SPEED = 3.5

# Параметры датчиков (Raycasting)
NUM_RAYS = 5
RAY_LENGTH = 180
RAY_ANGLES = [-60, -30, 0, 30, 60]

# Параметры эволюции ИИ
POPULATION_SIZE = 25
MUTATION_RATE = 0.15
MAX_GENERATION_FRAMES = 360  # 6 секунд на поколение

# Путь к файлу хранения данных
DATA_FILE_PATH = "data/ai_progress.json"