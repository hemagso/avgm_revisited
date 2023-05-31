"""
This script scrapes Metacritic index page for game reviews, building a list of URLs
for each individual game and platform.
"""

import csv
import re
from datetime import date, datetime
from time import sleep
from typing import Callable, TypeVar

import requests
from bs4 import BeautifulSoup, Tag


def get_list_url() -> str:
    """Returns the index URL for Metacritic games reviews

    Returns:
        str: The URL
    """
    return "http://www.metacritic.com/browse/games/score/metascore/all/all/filtered"


T1 = TypeVar("T1")
T2 = TypeVar("T2")


def safe_cast(
    v: T1, to_type: Callable[[T1], T2], default: T2 | None = None
) -> T2 | None:
    """Cast a value of type T1 into type T2, returning a default value in case of failure.

    Args:
        v (T1): Value of type T1 that we wish to cast into T2.
        to_type (Callable[[T1], T2]): Callable that receive a value of type T1 and
            returns a value of type T2. This callable must throw either a ValueError or
            a TypeError if the cast is not possible.
        default (T2 | None, optional): Default value to use in case of casting failure.
            Defaults to None.

    Returns:
        T2 | None: Cast value.
    """
    try:
        return to_type(v)
    except (ValueError, TypeError):
        return default


def get_games_page(page: int) -> str:
    """Retrieves a game list page from Metacritic.

    Args:
        page (int): The page number of the list to retrieve.

    Raises:
        ConnectionError: Raised in case the request to Metacritic fails.

    Returns:
        str: String containing the HTML of the page.
    """
    url = get_list_url()
    r = requests.get(
        url, params={"page": page}, headers={"User-Agent": "Metascraper 1.0"}
    )
    if r.status_code != 200:
        raise ConnectionError(r.status_code)
    return r.text


def parse_game_title(row: Tag) -> tuple[str, str]:
    title_dom = row.find("a", attrs={"class": "title"})
    title = title_dom.text
    title = re.sub("\s+", " ", title).strip()
    url = title_dom["href"]
    return title, url


def parse_game_score(row: Tag) -> tuple[int, float]:
    # Getting Metascore
    metascore_dom = row.find("div", attrs={"class": "clamp-metascore"}).find(
        "div", attrs={"class": "metascore_w"}
    )
    metascore = safe_cast(metascore_dom.text, int)
    # Getting Userscore
    userscore_dom = row.find("div", attrs={"class": "clamp-userscore"}).find(
        "div", attrs={"class": "metascore_w"}
    )
    userscore = safe_cast(userscore_dom.text, float)
    return metascore, userscore


def parse_game_publish_date_platform(row: Tag) -> tuple[date, str]:
    details_dom = row.find("div", attrs={"class": "clamp-details"})
    platform_dom = details_dom.find("div", attrs={"class": "platform"}).find(
        "span", attrs={"class": "data"}
    )
    platform = platform_dom.text

    platform = re.sub("\s+", " ", platform).strip()
    publish_date_dom = details_dom.find("span", recursive=False)

    publish_date = publish_date_dom.text
    publish_date = re.sub("\s+", " ", publish_date).strip()
    publish_date = datetime.strptime(publish_date, "%B %d, %Y").date()

    return publish_date, platform


def parse_product_row(row: Tag) -> tuple[str, str, int, float, date, str]:
    title, url = parse_game_title(row)
    metascore, userscore = parse_game_score(row)
    publish_date, platform = parse_game_publish_date_platform(row)
    return title, url, metascore, userscore, publish_date, platform


def main():
    with open("data/game_index.csv", "a") as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\n")
        for page in range(0, 202):
            print("Page ", page)
            html = get_games_page(page)
            soup = BeautifulSoup(html, "html5lib")
            games = soup.find_all("td", attrs={"class": "clamp-summary-wrap"})
            scraped_games = [(page,) + parse_product_row(row) for row in games]
            for row in scraped_games:
                writer.writerow(row)
            sleep(10)


if __name__ == "__main__":
    main()
