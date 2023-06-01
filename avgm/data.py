import polars as pl
import torch
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset

DataBatch = tuple[torch.Tensor, torch.Tensor, torch.Tensor]


class ReviewDataset(Dataset):
    def __init__(self, df: pl.DataFrame, padding_index: int, device: str = "cuda"):
        self.df = df
        self.padding_index = padding_index
        self.device = device

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return (
            self.df["token_ids"][idx].to_list(),
            self.df["score"][idx],
            self.df["n_tokens"][idx],
        )

    def get_loader(self, batch_size: int = 128, shuffle: bool = True) -> DataLoader:
        def collate(batch: list[DataBatch]) -> DataBatch:
            sorted_batch = sorted(batch, key=lambda x: len(x[0]), reverse=True)
            tokens, scores, lengths = zip(*sorted_batch)
            tokens_padded = pad_sequence(
                [
                    torch.tensor(token, dtype=torch.int64, device=self.device)
                    for token in tokens
                ],
                batch_first=True,
                padding_value=self.padding_index,
            )
            return (
                tokens_padded,
                torch.tensor(scores, dtype=torch.int64, device=self.device),
                torch.tensor(lengths, dtype=torch.int64, device="cpu"),
            )

        return DataLoader(
            self, batch_size=batch_size, collate_fn=collate, shuffle=shuffle
        )
