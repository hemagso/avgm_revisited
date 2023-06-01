from abc import ABC, abstractmethod

import torch
import torch.nn as nn
import tqdm
from torch.utils.data import DataLoader

from ..protocols import MetricFactory, TorchCriterion, TorchOptimizer


class Model(nn.Module, ABC):
    def __init__(
        self, metrics: list[MetricFactory] | None = None, print_every: int = 25
    ):
        super().__init__()
        self.criterion: TorchCriterion
        self.optimizer: TorchOptimizer
        if metrics is None:
            metrics = []
        self.metrics = {
            "train": [metric() for metric in metrics],
            "eval": [metric() for metric in metrics],
        }
        self.print_every = print_every

    def fit(self, train_data: DataLoader, valid_data: DataLoader | None, n_epochs: int):
        for epoch in range(n_epochs):
            self.train()
            self.run_epoch(train_data, epoch)
            if valid_data:
                self.eval()
                self.run_epoch(valid_data, epoch)

    def update_metrics(self, y_hat: torch.Tensor, y: torch.Tensor):
        set = "train" if self.training else "eval"
        for metric in self.metrics[set]:
            metric.update(y_hat, y)

    def run_epoch(self, data: DataLoader, epoch: int):
        total_loss: float = 0
        total_batch = len(data)
        with tqdm.tqdm(total=total_batch) as pbar:
            set = "train" if self.training else "eval"
            pbar.set_description(f"{set}: Epoch {epoch+1}")
            for idx, (x, y, lengths) in enumerate(data):
                self.optimizer.zero_grad()
                y_hat = self.forward(x, lengths)
                loss = self.criterion(y_hat, y)
                total_loss += loss.item()
                self.update_metrics(y_hat, y)
                if self.training:
                    loss.backward()
                    self.optimizer.step()
                if idx % self.print_every == 0:
                    pbar.update(self.print_every)
                    pbar.set_postfix(
                        loss=loss.item(),
                        **{metric.get_name(): metric for metric in self.metrics[set]},
                    )

    @abstractmethod
    def forward(self, tokens: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        ...
