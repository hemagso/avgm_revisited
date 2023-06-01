from __future__ import annotations

from typing import Callable, Protocol

import torch


class TorchCriterion(Protocol):
    def __call__(self, y_hat: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        ...


class TorchOptimizer(Protocol):
    def zero_grad(self) -> None:
        ...

    def step(self) -> None:
        ...


class Metric(Protocol):
    def update(self, y_hat: torch.Tensor, y: torch.Tensor) -> None:
        ...

    def reset(self) -> None:
        ...

    def get_current(self) -> float:
        ...

    def get_history(self) -> list[float]:
        ...

    def get_name(self) -> str:
        ...


MetricFactory = Callable[[], Metric]
