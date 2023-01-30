import csv
import os
import re
from datetime import datetime
from time import sleep

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag


def get_number_pages(page: Tag) -> int:
    if last_page_dom := page.find("li", attrs={"class": "page last_page"}):
        last_page_dom = last_page_dom.find("a")
        return int(last_page_dom.text)
    return 1


def get_game_page(url: str, page_no: int) -> Tag:
    """get_games_page
    Retrieve the game list html document from metacritic.
    :param page: Desired page on the metacritic game list.
    :return: String containing the html document.
    """

    r = requests.get(
        url, params={"page": page_no}, headers={"User-Agent": "Metascraper 1.0"}
    )
    if r.status_code != 200:
        raise ValueError(r.status_code)
    return BeautifulSoup(r.text, "html.parser")


def get_review_text(review_dom: Tag) -> str:
    review_body_dom = review_dom.find("div", attrs={"class": "review_body"})
    if blurb_expanded_dom := review_body_dom.find(
        "span", attrs={"class": "blurb blurb_expanded"}
    ):
        return blurb_expanded_dom.text
    else:
        return review_body_dom.text


def get_review_score(review_dom: Tag) -> int:
    return int(review_dom.find("div", attrs={"class": "review_grade"}).text)


def get_reviewer_and_date(review_dom: Tag) -> tuple[str, str]:
    review_critic_dom = review_dom.find("div", attrs={"class": "review_critic"})
    reviewer = re.sub(
        "(\s|\n)+", "", review_critic_dom.find("div", attrs={"class": "name"}).text
    )
    date = datetime.strptime(
        review_critic_dom.find("div", attrs={"class": "date"}).text, "%b %d, %Y"
    )
    return reviewer, date.strftime("%Y-%m-%d")


def parse_review(review_dom: Tag) -> tuple[str, str, int, str]:
    text = get_review_text(review_dom)
    text = re.sub("(\s|\n)+", " ", text).strip()
    score = get_review_score(review_dom)
    reviewer, date = get_reviewer_and_date(review_dom)
    return reviewer, date, score, text


def get_game_reviews_page(page: Tag):
    reviews_doms = page.find("ol", attrs={"class": "reviews user_reviews"}).find_all(
        "li",
        attrs={
            "class": [
                "review user_review",
                "review user_review first_review",
                "review user_review last_review",
            ]
        },
    )
    return [parse_review(review_dom) for review_dom in reviews_doms]


def get_game_reviews(game: str):
    try:
        out_file = game.replace("/", "_")
        if os.path.exists(f"data/raw/games/{out_file}.csv"):
            print(f"Skipping {game}: Already Exists")
            return
        url = f"https://www.metacritic.com{game}/user-reviews"
        first_page = get_game_page(url, 0)
        number_pages = get_number_pages(first_page)
        reviews = []
        for page_no in range(0, number_pages):
            print(game, page_no)
            page = get_game_page(url, page_no)
            reviews += get_game_reviews_page(page)
            sleep(0.5)
        with open(f"data/raw/games/{out_file}.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerows(reviews)
        sleep(1)
    except Exception as e:
        print(f"Skipping {game}: Exception")
        print(e)


def main():
    with open("data/raw/game_index.csv", "r") as file:
        reader = csv.reader(file, delimiter=";")
        for _, _, url, _, _, _, _ in reader:
            get_game_reviews(url)


if __name__ == "__main__":
    main()
