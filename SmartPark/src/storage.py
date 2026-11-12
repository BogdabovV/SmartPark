
import json
import os
from src.config import DATA_FILE_PATH


class ProgressStorage:
    def __init__(self, filepath=DATA_FILE_PATH):
        self.filepath = filepath
        self._ensure_directory()

    def _ensure_directory(self):
        directory = os.path.dirname(self.filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def save_progress(self, generation: int, best_fitness: float, best_weights: list, total_parked: int) -> bool:
        data = {
            "generation": generation,
            "best_fitness": round(best_fitness, 2),
            "total_parked_record": total_parked,
            "weights": best_weights
        }
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"[Ошибка сохранения]: {e}")
            return False

    def load_progress(self) -> dict | None:
        if not os.path.exists(self.filepath):
            return None
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "weights" in data and "generation" in data:
                return data
            return None
        except (json.JSONDecodeError, IOError) as e:
            print(f"[Ошибка загрузки данных]: {e}")
            return None

    def reset_progress(self) -> bool:
        if os.path.exists(self.filepath):
            try:
                os.remove(self.filepath)
                return True
            except OSError as e:
                print(f"[Ошибка удаления файла]: {e}")
                return False
        return True