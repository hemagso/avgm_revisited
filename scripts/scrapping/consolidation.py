import csv
import os
from typing import Generator, NamedTuple

import pyarrow as pa
import pyarrow.csv as pc
import pyarrow.parquet as pq
from pyarrow import dataset as ds


class Game(NamedTuple):
    name: str
    platform: str


class GameIndexItem(NamedTuple):
    game: Game
    file: str


def get_index() -> Generator[GameIndexItem, None, None]:
    with open("data/game_index.csv", "r") as file:
        reader = csv.reader(file, delimiter=";")
        for _, game_name, url, _, _, _, platform in reader:
            game_file = url.replace("/", "_")
            yield GameIndexItem(Game(game_name, platform), game_file + ".csv")


def main():
    partitioning = ds.partitioning(
        schema=pa.schema(
            [pa.field("game", pa.string()), pa.field("platform", pa.string())]
        )
    )
    tables = []
    for (game_name, platform), file in get_index():
        try:
            table = pc.read_csv(
                os.path.join("data/raw/games", file),
                read_options=pc.ReadOptions(
                    column_names=["user", "date", "score", "text"]
                ),
                convert_options=pc.ConvertOptions(
                    column_types={
                        "user": pa.string(),
                        "date": pa.date32(),
                        "score": pa.int8(),
                        "text": pa.string(),
                    }
                ),
            )
            table = table.append_column("game", pa.array([game_name] * len(table)))
            table = table.append_column("platform", pa.array([platform] * len(table)))

            pq.write_to_dataset(
                table, root_path="data/raw/parquet", partitioning=partitioning
            )
            tables.append(table)

        except FileNotFoundError as e:
            print(f"Skipping {game_name} ({platform}): File Not Found")
        except pa.ArrowInvalid as e:
            print(f"Skipping {game_name} ({platform}): Empty File")

    combined_table = pa.concat_tables(tables)
    pq.write_table(combined_table, "data/raw/reviews.parquet")


if __name__ == "__main__":
    main()
