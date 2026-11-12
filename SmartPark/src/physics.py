
import math
import pygame
from src.config import (
    CAR_WIDTH, CAR_HEIGHT, MAX_SPEED, REVERSE_MAX_SPEED,
    ACCELERATION, STEER_SPEED, NUM_RAYS, RAY_LENGTH, RAY_ANGLES,
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_CAR_AI, COLOR_CAR_MANUAL
)
from src.ai_brain import SimpleBrain


def line_intersection(line1: tuple, line2: tuple) -> tuple[float, float] | None:
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2

    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if denom == 0:
        return None

    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom

    if 0.0 <= ua <= 1.0 and 0.0 <= ub <= 1.0:
        return (x1 + ua * (x2 - x1), y1 + ua * (y2 - y1))
    return None


class Car:

    def __init__(self, x: float, y: float, angle: float = 0, is_ai: bool = True, brain: SimpleBrain | None = None):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 0.0
        self.is_ai = is_ai
        self.brain = brain if brain else SimpleBrain(input_dim=6, output_dim=2)

        self.alive = True
        self.parked = False
        self.fitness = 0.0
        self.sensor_readings = [1.0] * NUM_RAYS
        self.color = COLOR_CAR_AI if is_ai else COLOR_CAR_MANUAL

    def get_corners(self) -> list[tuple[float, float]]:
        rad = math.radians(self.angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        hw, hh = CAR_WIDTH / 2, CAR_HEIGHT / 2

        offsets = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        return [
            (self.x + ox * cos_a - oy * sin_a, self.y + ox * sin_a + oy * cos_a)
            for ox, oy in offsets
        ]

    def get_bounding_lines(self) -> list[tuple]:
        c = self.get_corners()
        return [
            (c[0][0], c[0][1], c[1][0], c[1][1]),
            (c[1][0], c[1][1], c[2][0], c[2][1]),
            (c[2][0], c[2][1], c[3][0], c[3][1]),
            (c[3][0], c[3][1], c[0][0], c[0][1])
        ]

    def update_sensors(self, obstacle_lines: list[tuple]):
        self.sensor_readings = [1.0] * NUM_RAYS
        for i, ray_angle in enumerate(RAY_ANGLES):
            rad = math.radians(self.angle + ray_angle)
            rx = self.x + math.cos(rad) * RAY_LENGTH
            ry = self.y + math.sin(rad) * RAY_LENGTH
            ray_line = (self.x, self.y, rx, ry)

            min_dist = 1.0
            for line in obstacle_lines:
                pt = line_intersection(ray_line, line)
                if pt:
                    dist = math.hypot(pt[0] - self.x, pt[1] - self.y) / RAY_LENGTH
                    if dist < min_dist:
                        min_dist = dist
            self.sensor_readings[i] = min_dist

    def update(self, obstacle_lines: list[tuple], target_rect: pygame.Rect):
        if not self.alive or self.parked:
            return

        if self.is_ai:
            dx_target = (target_rect.centerx - self.x) / SCREEN_WIDTH
            inputs = self.sensor_readings + [dx_target]
            steering, throttle = self.brain.predict(inputs)

            self.angle += steering * STEER_SPEED
            self.speed += throttle * ACCELERATION
            self.speed = max(REVERSE_MAX_SPEED, min(MAX_SPEED, self.speed))
            self.speed *= 0.95

        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed

        self.update_sensors(obstacle_lines)

        # Проверка столкновения
        for c_line in self.get_bounding_lines():
            for obs in obstacle_lines:
                if line_intersection(c_line, obs):
                    self.alive = False
                    self.speed = 0
                    return

        # Проверка заезда в парковочный карман
        car_rect = pygame.Rect(self.x - CAR_WIDTH / 2, self.y - CAR_HEIGHT / 2, CAR_WIDTH, CAR_HEIGHT)
        if target_rect.contains(car_rect) and abs(self.speed) < 0.35:
            self.parked = True
            self.speed = 0

    def calculate_fitness(self, target_rect: pygame.Rect) -> float:
        dist = math.hypot(target_rect.centerx - self.x, target_rect.centery - self.y)
        max_dist = math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT)
        fitness = (1.0 - (dist / max_dist)) * 100.0

        if self.parked:
            fitness += 300.0
        elif not self.alive:
            fitness -= 40.0

        self.fitness = max(0.1, fitness)
        return self.fitness