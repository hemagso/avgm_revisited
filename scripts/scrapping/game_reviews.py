import csv
import re
from datetime import datetime
from time import sleep

import requests
from bs4 import BeautifulSoup


def get_number_pages(page) -> int:
    last_page_dom = page.find("li", attrs={"class": "page last_page"}).find("a")
    return int(last_page_dom.text)


def get_game_page(url, page):
    """get_games_page
    Retrieve the game list html document from metacritic.
    :param page: Desired page on the metacritic game list.
    :return: String containing the html document.
    """

    r = requests.get(
        url, params={"page": page}, headers={"User-Agent": "Metascraper 1.0"}
    )
    if r.status_code != 200:
        raise ValueError(r.status_code)
    return r.text


def main():
    html = get_game_page(
        "https://www.metacritic.com/game/nintendo-64/the-legend-of-zelda-ocarina-of-time/user-reviews",
        0,
    )
    soup = BeautifulSoup(html, "html.parser")
    print(get_number_pages(soup))


if __name__ == "__main__":
    main()
