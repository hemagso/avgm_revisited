from typing import Iterable

import polars as pl
from tokenizers import (
    Tokenizer,
    decoders,
    models,
    normalizers,
    pre_tokenizers,
    trainers,
)


def create_tokenizer(
    data: Iterable[str],
    vocab_size: int,
    /,
    unk_token: str = "<unk>",
    pad_token: str = "<pad>",
    subword_prefix: str = "##",
):
    tokenizer = Tokenizer(models.WordPiece(unk_token=unk_token))
    tokenizer.add_special_tokens([unk_token, pad_token])
    tokenizer.normalizer = normalizers.BertNormalizer(
        clean_text=True, handle_chinese_chars=True, strip_accents=True, lowercase=True
    )

    tokenizer.pre_tokenizer = pre_tokenizers.BertPreTokenizer()
    tokenizer.decoder = decoders.WordPiece(prefix=subword_prefix)

    trainer = trainers.WordPieceTrainer(
        vocab_size=vocab_size,
        min_frequency=2,
        limit_alphabet=1000,
        special_tokens=[unk_token, pad_token],
        show_progress=True,
        continuing_subword_prefix=subword_prefix,
    )

    tokenizer.train_from_iterator(data, trainer=trainer)
    return tokenizer


def main():
    print("Reading reviews")
    df_en = pl.read_parquet(
        "./data/processed/reviews.parquet", columns=("text", "language", "set")
    ).filter(pl.col("language") == "en")
    data = df_en.filter(pl.col("set") == "train")["text"].to_list()
    print("Creating tokenizer")
    tokenizer = create_tokenizer(data, 30000)

    print("Encoding reviews")
    df_en = df_en.with_columns(
        pl.col("text").apply(lambda x: tokenizer.encode(x).ids).alias("token_ids")
    )


if __name__ == "__main__":
    main()
