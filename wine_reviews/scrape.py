import abc
import glob
import itertools
import os
import re

from typing import Tuple, Dict, Optional
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

# need to change page=1, iterate over pages (get number of pages from this URL, page 1?)
page = 1
BASE_URL = f"https://www.winemag.com/?s=&drink_type=wine&page={page}&sort_by=pub_date_web&sort_dir=desc&search_type=reviews"

HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36"
    )
}


# create data class for each of the things we want to retrieve from the pages
card_objects = {
    "title": ('h3', {'class': 'title'}),
    "appellation": ('span', {'class': 'appellation'}),
    "rating": ('span', {'class': 'rating'}),
    "price": ('span', {'class': 'price'})
}


def parse_review_card(review_item):
    finder = review_item.find
    link = [finder("a", {'class': 'review-listing'})['href']]
    return link + [
        finder(*card_objects[obj]).get_text() for obj in card_objects
    ]

year_finder = re.compile(r"\d{4}")

@dataclass
class WineReview:
    title: str
    rating: int
    price: float
    appellation: str
    link: str


class AttributeRetriever(object):

    def __init__(self, name: str, parser_args: Optional[Tuple[str, Dict[str, str]]]):
        self.name = name
        self.args = parser_args

    @abc.abstractmethod
    def retriever(self):
        raise NotImplementedError("Must define the retriever method")


def load_test_data():
    datapath = os.path.dirname(os.path.abspath(__file__)) + "/data"
    review_cards = []
    for review_page in glob.glob(f"{datapath}/*all_reviews.html"):
        html = BeautifulSoup(
            open(review_page, "r").read(), "html.parser"
        )
        review_cards += html.find_all("li", {"class": "review-item"})

    reviews = []
    for x, y in itertools.product(range(1, 4), range(1,21)):
        reviews.append(
            BeautifulSoup(open(f"{datapath}/page_{x}_review_{y}.html", "r").read(), "html.parser")
        )

    review_cards_parsed = [
        parse_review_card(rv_card) for rv_card in review_cards
    ]

    return list(zip(review_cards_parsed, reviews))


if __name__ == "__main__":
    print("hello, I am wine review parser")
    cards = load_test_data()
