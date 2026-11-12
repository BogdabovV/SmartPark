"""Модуль графического интерфейса и главного цикла симуляции SmartPark AI."""

import math
import random
import sys
import pygame
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLOR_BG, COLOR_GRID, COLOR_WALL,
    COLOR_PARKING, COLOR_PARKING_BORDER, COLOR_CAR_BEST, COLOR_SENSOR,
    COLOR_TEXT, RAY_ANGLES, RAY_LENGTH, CAR_HEIGHT, POPULATION_SIZE,
    MAX_GENERATION_FRAMES
)
from src.physics import Car
from src.ai_brain import SimpleBrain
from src.storage import ProgressStorage


class SmartParkApp:
    """Главный класс приложения, связывающий физику, ИИ, хранение данных и UI."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("SmartPark AI — Прототип симулятора автопарковки")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 16)
        self.font_title = pygame.font.SysFont("Segoe UI", 20, bold=True)

        self.storage = ProgressStorage()
        self.target_rect = pygame.Rect(1080, 310, 120, 100)

        self.base_obstacles = [
            (20, 65, SCREEN_WIDTH - 20, 65),
            (SCREEN_WIDTH - 20, 65, SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20),
            (SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20, 20, SCREEN_HEIGHT - 20),
            (20, SCREEN_HEIGHT - 20, 20, 65),
            (1050, 200, 1260, 200),
            (1050, 520, 1260, 520),
            (1050, 200, 1050, 520)
        ]
        self.obstacles = list(self.base_obstacles)

        self.mode = "TRAIN"
        self.generation = 1
        self.timer = 0
        self.best_fitness_ever = 0.0
        self.status_message = "Система готова. Нажмите 'S' для сохранения, 'L' для загрузки."

        self.spawn_x, self.spawn_y, self.spawn_angle = 120, 360, 0
        self.population = [Car(self.spawn_x, self.spawn_y, self.spawn_angle) for _ in range(POPULATION_SIZE)]
        self.manual_car = Car(self.spawn_x, self.spawn_y, self.spawn_angle, is_ai=False)

        self._load_saved_state()

    def _load_saved_state(self):
        saved = self.storage.load_progress()
        if saved:
            self.generation = saved.get("generation", 1)
            self.best_fitness_ever = saved.get("best_fitness", 0.0)
            loaded_brain = SimpleBrain(weights=saved["weights"])

            new_pop = [Car(self.spawn_x, self.spawn_y, self.spawn_angle, brain=loaded_brain)]
            new_pop[0].color = COLOR_CAR_BEST
            for _ in range(POPULATION_SIZE - 1):
                new_pop.append(Car(self.spawn_x, self.spawn_y, self.spawn_angle, brain=loaded_brain.mutate()))
            self.population = new_pop
            self.status_message = f"Загружено поколение #{self.generation} (Рекорд: {self.best_fitness_ever})"
        else:
            self.status_message = "Сохранений не найдено. Начато новое обучение."

    def next_generation(self):
        self.generation += 1
        self.timer = 0

        for car in self.population:
            car.calculate_fitness(self.target_rect)

        self.population.sort(key=lambda c: c.fitness, reverse=True)
        best_car = self.population[0]

        if best_car.fitness > self.best_fitness_ever:
            self.best_fitness_ever = best_car.fitness
            parked_now = sum(1 for c in self.population if c.parked)
            self.storage.save_progress(self.generation, self.best_fitness_ever, best_car.brain.weights, parked_now)

        new_pop = [Car(self.spawn_x, self.spawn_y, self.spawn_angle, brain=best_car.brain)]
        new_pop[0].color = COLOR_CAR_BEST

        top_pool = self.population[:5]
        while len(new_pop) < POPULATION_SIZE:
            parent = random.choice(top_pool)
            new_pop.append(Car(self.spawn_x, self.spawn_y, self.spawn_angle, brain=parent.brain.mutate()))

        self.population = new_pop

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                if 70 < my < SCREEN_HEIGHT - 60 and 200 < mx < 1030:
                    size = 30
                    self.obstacles.extend([
                        (mx - size, my - size, mx + size, my - size),
                        (mx + size, my - size, mx + size, my + size),
                        (mx + size, my + size, mx - size, my + size),
                        (mx - size, my + size, mx - size, my - size),
                    ])
                    self.status_message = f"Добавлено препятствие в точке ({mx}, {my})"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    self.mode = "MANUAL" if self.mode == "TRAIN" else "TRAIN"
                    self.manual_car = Car(self.spawn_x, self.spawn_y, self.spawn_angle, is_ai=False)
                elif event.key == pygame.K_s:
                    best = max(self.population, key=lambda c: c.calculate_fitness(self.target_rect))
                    parked = sum(1 for c in self.population if c.parked)
                    if self.storage.save_progress(self.generation, best.fitness, best.brain.weights, parked):
                        self.status_message = f"Прогресс сохранен в {self.storage.filepath}!"
                elif event.key == pygame.K_l:
                    self._load_saved_state()
                elif event.key == pygame.K_c:
                    self.obstacles = list(self.base_obstacles)
                    self.status_message = "Пользовательские препятствия очищены."
                elif event.key == pygame.K_r:
                    self.storage.reset_progress()
                    self.generation = 1
                    self.best_fitness_ever = 0.0
                    self.population = [Car(self.spawn_x, self.spawn_y, self.spawn_angle) for _ in range(POPULATION_SIZE)]
                    self.status_message = "Полный сброс обучения и удаление файла сохранения."

        if self.mode == "MANUAL" and self.manual_car.alive:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                self.manual_car.speed += 0.1
            if keys[pygame.K_s]:
                self.manual_car.speed -= 0.1
            if keys[pygame.K_a]:
                self.manual_car.angle -= 3.5
            if keys[pygame.K_d]:
                self.manual_car.angle += 3.5
            self.manual_car.speed = max(-2.0, min(4.0, self.manual_car.speed))
            self.manual_car.speed *= 0.95

    def update(self):
        if self.mode == "TRAIN":
            self.timer += 1
            all_done = True
            for car in self.population:
                if car.alive and not car.parked:
                    car.update(self.obstacles, self.target_rect)
                    all_done = False

            if all_done or self.timer >= MAX_GENERATION_FRAMES:
                self.next_generation()
        else:
            self.manual_car.update(self.obstacles, self.target_rect)

    def _draw_car(self, car: Car):
        for i, ray_angle in enumerate(RAY_ANGLES):
            rad = math.radians(car.angle + ray_angle)
            dist = car.sensor_readings[i] * RAY_LENGTH
            ex = car.x + math.cos(rad) * dist
            ey = car.y + math.sin(rad) * dist
            pygame.draw.line(self.screen, (100, 116, 139), (car.x, car.y), (ex, ey), 1)
            dot_color = (239, 68, 68) if car.sensor_readings[i] < 0.35 else (34, 197, 94)
            pygame.draw.circle(self.screen, dot_color, (int(ex), int(ey)), 3)

        corners = car.get_corners()
        pygame.draw.polygon(self.screen, car.color, corners)
        pygame.draw.polygon(self.screen, COLOR_TEXT, corners, 2)

        rad = math.radians(car.angle)
        fx = car.x + math.cos(rad) * (CAR_HEIGHT / 2)
        fy = car.y + math.sin(rad) * (CAR_HEIGHT / 2)
        pygame.draw.circle(self.screen, COLOR_TEXT, (int(fx), int(fy)), 4)

    def draw(self):
        self.screen.fill(COLOR_BG)

        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(self.screen, COLOR_GRID, (x, 65), (x, SCREEN_HEIGHT))
        for y in range(65, SCREEN_HEIGHT, 40):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (SCREEN_WIDTH, y))

        pygame.draw.rect(self.screen, COLOR_PARKING, self.target_rect)
        pygame.draw.rect(self.screen, COLOR_PARKING_BORDER, self.target_rect, 3)
        self.screen.blit(self.font.render("ПАРКОВКА", True, COLOR_TEXT), (self.target_rect.x + 20, self.target_rect.y + 40))

        for obs in self.obstacles:
            pygame.draw.line(self.screen, COLOR_WALL, (obs[0], obs[1]), (obs[2], obs[3]), 4)

        if self.mode == "TRAIN":
            for car in self.population:
                if car.alive or car.parked:
                    self._draw_car(car)
        else:
            self._draw_car(self.manual_car)

        pygame.draw.rect(self.screen, (30, 41, 59), (0, 0, SCREEN_WIDTH, 60))
        self.screen.blit(self.font_title.render("SmartPark AI", True, COLOR_TEXT), (20, 17))
        controls_info = "[M] Режим  |  [S] Сохранить JSON  |  [L] Загрузить  |  [ЛКМ] Препятствие  |  [C] Очистить  |  [R] Сброс"
        self.screen.blit(self.font.render(controls_info, True, (147, 197, 253)), (220, 20))

        if self.mode == "TRAIN":
            alive = sum(1 for c in self.population if c.alive and not c.parked)
            parked = sum(1 for c in self.population if c.parked)
            stats = f"Режим: ИИ (TRAIN)  |  Поколение: {self.generation}  |  Живых: {alive}/{POPULATION_SIZE}  |  Припарковано: {parked}  |  Рекорд: {self.best_fitness_ever:.1f}"
        else:
            state = "ПРИПАРКОВАНО!" if self.manual_car.parked else ("АВАРИЯ!" if not self.manual_car.alive else "В движении (WASD)")
            stats = f"Режим: РУЧНОЙ (MANUAL)  |  Статус: {state}"

        pygame.draw.rect(self.screen, (30, 41, 59), (20, SCREEN_HEIGHT - 45, SCREEN_WIDTH - 40, 35), border_radius=6)
        self.screen.blit(self.font.render(stats, True, COLOR_TEXT), (35, SCREEN_HEIGHT - 37))
        self.screen.blit(self.font.render(self.status_message, True, (74, 222, 128)), (820, SCREEN_HEIGHT - 37))

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)