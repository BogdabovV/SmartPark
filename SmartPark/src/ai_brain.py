#иишно
import math
import random
from src.config import MUTATION_RATE


class SimpleBrain:

    def __init__(self, input_dim: int = 6, output_dim: int = 2, weights: list | None = None):
        self.input_dim = input_dim
        self.output_dim = output_dim

        if weights is not None and len(weights) == input_dim:
            self.weights = [row[:] for row in weights]
        else:
            self.weights = [
                [random.uniform(-1.0, 1.0) for _ in range(output_dim)]
                for _ in range(input_dim)
            ]

    def predict(self, inputs: list[float]) -> list[float]:
        if len(inputs) != self.input_dim:
            raise ValueError(f"Ожидалось {self.input_dim} входов, получено {len(inputs)}")

        outputs = [0.0] * self.output_dim
        for j in range(self.output_dim):
            total = sum(inputs[i] * self.weights[i][j] for i in range(self.input_dim))
            outputs[j] = math.tanh(total)
        return outputs

    def mutate(self, rate: float = MUTATION_RATE) -> "SimpleBrain":
        new_weights = []
        for i in range(self.input_dim):
            row = []
            for j in range(self.output_dim):
                w = self.weights[i][j]
                if random.random() < rate:
                    w += random.gauss(0, 0.4)
                    w = max(-2.0, min(2.0, w))
                row.append(w)
            new_weights.append(row)
        return SimpleBrain(self.input_dim, self.output_dim, new_weights)