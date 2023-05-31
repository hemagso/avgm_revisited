import csv
import os
import re
from datetime import datetime
from time import sleep

import requests
from bs4 import BeautifulSoup, Tag


def get_number_pages(page: Tag) -> int:
    match last_page_dom := page.find("li", attrs={"class": "page last_page"}):
        case Tag():
            match last_page_anchor := last_page_dom.find("a"):
                case Tag():
                    return int(last_page_anchor.text)
                case _:
                    raise ValueError("Last page anchor not found in Tag")
        case None:
            return 1
        case _:
            raise ValueError("Last page anchor not found in Tag")


def get_game_page(url: str, page_no: int) -> Tag:
    r = requests.get(
        url, params={"page": page_no}, headers={"User-Agent": "Metascraper 1.0"}
    )
    if r.status_code != 200:
        raise ValueError(r.status_code)
    dom = BeautifulSoup(r.text.replace("<br>", "\n").replace("<br/>", "\n"), "html5lib")
    return dom


def get_review_text(review_dom: Tag) -> str:
    match review_body_dom := review_dom.find("div", attrs={"class": "review_body"}):
        case Tag():
            match blurb_expanded_dom := review_body_dom.find(
                "span", attrs={"class": "blurb blurb_expanded"}
            ):
                case Tag():
                    return blurb_expanded_dom.text
                case None:
                    return review_body_dom.text
                case _:
                    raise ValueError("Review text not found in Tag")
        case _:
            raise ValueError("Review body not found in Tag")


def get_review_score(review_dom: Tag) -> int:
    match review_grade_dom := review_dom.find("div", attrs={"class": "review_grade"}):
        case Tag():
            return int(review_grade_dom.text)
        case _:
            raise ValueError("Review grade not found in Tag")


def get_reviewer_and_date(review_dom: Tag) -> tuple[str, str]:
    match critic_dom := review_dom.find("div", attrs={"class": "review_critic"}):
        case Tag():
            match critic_name_dom := critic_dom.find("div", attrs={"class": "name"}):
                case Tag():
                    reviewer = re.sub("(\s|\n)+", "", critic_name_dom.text)
                case _:
                    raise ValueError("Critic name not found in Tag")
            match date_dom := critic_dom.find("div", attrs={"class": "date"}):
                case Tag():
                    review_date = datetime.strptime(date_dom.text, "%b %d, %Y")
                case _:
                    raise ValueError("Review date not found in Tag")
        case _:
            raise ValueError("Review critic not found in Tag")
    return reviewer, review_date.strftime("%Y-%m-%d")


def parse_review(review_dom: Tag) -> tuple[str, str, int, str]:
    text = get_review_text(review_dom)
    text = re.sub("(\s|\n)+", " ", text).strip()
    score = get_review_score(review_dom)
    reviewer, date = get_reviewer_and_date(review_dom)
    return reviewer, date, score, text


def get_game_reviews_page(page: Tag):
    match list_dom := page.find("ol", attrs={"class": "reviews user_reviews"}):
        case Tag():
            ans = []
            reviews_doms = list_dom.find_all(
                "li",
                attrs={
                    "class": [
                        "review user_review",
                        "review user_review first_review",
                        "review user_review last_review",
                    ]
                },
            )
            for item in reviews_doms:
                match item:
                    case Tag():
                        ans.append(parse_review(item))
                    case _:
                        raise ValueError("Review item not found in Tag")
            return ans
        case None:
            return []
        case _:
            raise ValueError("Review list not found in Tag")


def get_game_reviews(game: str):
    try:
        out_file = game.replace("/", "_")
        if os.path.exists(f"data/raw/games/{out_file}.csv"):
            return
        url = f"https://www.metacritic.com{game}/user-reviews"
        first_page = get_game_page(url, 0)
        number_pages = get_number_pages(first_page)
        reviews = []
        for page_no in range(0, number_pages):
            print(game, page_no)
            page = get_game_page(url, page_no)
            reviews += get_game_reviews_page(page)
            sleep(0.25)
        with open(f"data/raw/games/{out_file}.csv", "w") as file:
            writer = csv.writer(file)
            print(f"Writing {len(reviews)} reviews")
            writer.writerows(reviews)
        sleep(0.25)
    except Exception as e:
        print(f"Skipping {url}: Exception")
        print(e)


def main():
    with open("data/game_index.csv", "r") as file:
        reader = csv.reader(file, delimiter=";")
        for _, _, url, _, _, _, _ in reader:
            get_game_reviews(url)


if __name__ == "__main__":
    main()
