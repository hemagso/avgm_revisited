from __future__ import annotations

import torch

from .protocols import MetricFactory


def Accuracy() -> MetricFactory:
    return lambda: AccuracyThressholdInstance(0)


def AccuracyThresshold(thresshold: int) -> MetricFactory:
    return lambda: AccuracyThressholdInstance(thresshold)


class AccuracyThressholdInstance:
    def __init__(self, thresshold: int):
        self.thresshold: int = thresshold
        self.correct: int = 0
        self.total: int = 0
        self.history: list[float] = []

    def update(self, y_hat: torch.Tensor, y: torch.Tensor) -> None:
        self.correct += int(
            ((y_hat.argmax(dim=1) - y).abs() <= self.thresshold).sum().item()
        )
        self.total += len(y)

    def reset(self) -> None:
        self.history.append(self.get_current())
        self.correct = 0
        self.total = 0

    def get_current(self) -> float:
        return self.correct / self.total

    def get_history(self) -> list[float]:
        return self.history

    def __repr__(self) -> str:
        return f"{self.get_current():.2%}"

    def get_name(self) -> str:
        return f"Acc{self.thresshold}"
