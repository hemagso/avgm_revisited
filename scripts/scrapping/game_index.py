import csv
import re
from datetime import datetime
from time import sleep

import requests
from bs4 import BeautifulSoup


def get_list_url():
    return "http://www.metacritic.com/browse/games/score/metascore/all/all/filtered"


def safe_cast(v, to_type, default=None):
    """safe_cast
    Exception safe casting function
    :param v: Value to be cast
    :param to_type: Type to be cast into
    :param default: Default value in case of failure
    :return: Casted value, or default value in failure
    """
    try:
        return to_type(v)
    except (ValueError, TypeError):
        return default


def get_games_page(page):
    """get_games_page
    Retrieve the game list html document from metacritic.
    :param page: Desired page on the metacritic game list.
    :return: String containing the html document.
    """
    url = get_list_url()
    r = requests.get(
        url, params={"page": page}, headers={"User-Agent": "Metascraper 1.0"}
    )
    if r.status_code != 200:
        raise ValueError(r.status_code)
    return r.text


def parse_game_title(row):
    """parse_game_title
    Retrieve the game title and metacritic URL page from the product_row DOM element
    :param row: product_row BeautifulSoup DOM element.
    :return: (title [string], url [string]) tuple.
    """
    title_dom = row.find("a", attrs={"class": "title"})
    title = title_dom.text
    title = re.sub("\s+", " ", title).strip()
    url = title_dom["href"]
    return title, url


def parse_game_score(row):
    """parse_game_score
    Retrieve the game metascore and userscore from the product_row DOM element
    :param row: product_row BeautifulSoup DOM element
    :return: (metascore [integer], userscore [float]) tuple.
    """
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


def parse_game_publish_date_platform(row):
    """parse_game_publish_date
    Retrieve the game publish date from the product_row DOM element
    :param row: product_row BeautifulSoup DOM element
    :return: Publish Date [datetime.date]
    """
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


def parse_product_row(row):
    """parse_product_row
    Retrieve Name, URL, Scores and Publish Date from game's the product_row DOM element
    :param row: product_row BeautifulSoup DOM element
    :return: (title [String], url [String], metascore [Integer], userscore [Float], publish_date [datetime.Date] tuple)
    """
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
            soup = BeautifulSoup(html, "html.parser")
            games = soup.find_all("td", attrs={"class": "clamp-summary-wrap"})
            scraped_games = [(page,) + parse_product_row(row) for row in games]
            for row in scraped_games:
                writer.writerow(row)
            sleep(10)


if __name__ == "__main__":
    main()
