import abc
import hashlib
import json
import re
import time

from typing import Any, Tuple, Dict, Optional, List

import pandas
import requests

from bs4 import BeautifulSoup
from tqdm import tqdm

from wine_reviews import crawl_delay_config


tqdm.pandas()

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

# really just a 4 digit number finder
year_finder = re.compile(r"\d{4}")

flags = {
    1: "Number of year-like values in title > 1, i.e. multiple possible vintages, taking first one",
    2: "Number of year-like values in title = 0, i.e. no vintage found",
    3: "No designation found in primary information",
    4: "Duplicate keys found when parsing"
}


class WineReviewScraper(object):
    def __init__(
        self,
        page_number: int,
        wait_between_requests: float = 0
    ) -> None:
        self.page_number = page_number
        self.wait_between_requests = wait_between_requests

    @property
    def download_link(self) -> str:
        return (
            "https://www.winemag.com/?s=&drink_type=wine&page={page}&"
            "sort_by=pub_date_web&sort_dir=desc&search_type=reviews"
        ).format(page=self.page_number)

    def download_reviews_page(self) -> requests.models.Response:
        with requests.Session() as sesh:
            return sesh.get(self.download_link, headers=HEADERS)

    def parse_all_review_cards(self) -> pandas.DataFrame:
        response = self.download_reviews_page()
        response_soup = BeautifulSoup(response.content, 'html.parser')
        review_cards = response_soup.find_all("li", {"class": "review-item"})

        review_cards_data = []
        for card in review_cards:
            observation = {
                obj: card.find(*card_objects[obj]).get_text() for obj in card_objects
            }
            observation['link'] = card.find("a", {'class': 'review-listing'})['href']
            observation['page_number'] = self.page_number
            review_cards_data.append(observation)

        return pandas.DataFrame(review_cards_data)
    
    def parse_review_pages(self) -> pandas.DataFrame:
        review_cards = self.parse_all_review_cards()

        # No cards parsed, return empty... scrape script takes care of this
        # Removes divide by zero warning from tqdm and pandas
        if review_cards.empty:
            return pandas.DataFrame([])

        wine_review_pages = review_cards.progress_apply(
            lambda card: WineReviewPage(card), axis=1
        )
        return pandas.DataFrame(
            [x._get_properties_and_values() for x in wine_review_pages]
        )


class WineReviewPage(object):
    def __init__(self, card: pandas.Series, crawl_delay: int = crawl_delay_config) -> None:
        self.card = card
        self.crawl_delay = crawl_delay
        self.flags: List[int] = []

        # initialize scraped data from page, add link
        self.scraped_info: Dict[str, str] = {}
        # add info from card to scraped data
        self.scraped_info['link'] = self.card.link
        self.scraped_info['page_number'] = self.card.page_number
        self.scraped_info['title'] = self.card.title

        time.sleep(self.crawl_delay)
        with requests.Session() as sesh:
            self.response = sesh.get(self.link, headers=HEADERS)

        self.content = BeautifulSoup(self.response.content, 'html.parser')

        # use sha hash to check for duplicate entries
        self.scraped_info['sha512_hash'] = hashlib.sha512(
            str(self.content).encode(self.response.encoding)
        )

        # add info scraped from wine review page
        self._get_primary_info()
        self._get_secondary_info()
        # call after, just in case there is weird stuff in this dictionary already
        self._get_json_post_metadata()
        self._get_date_published()
        self._get_vintage_from_card_title()


    def get_value_from_parsed_info(self, key) -> Optional[str]:
        try:
            return self.scraped_info[key]
        except KeyError:
            return None

    @property
    def page_number(self) -> Optional[str]:
        return self.get_value_from_parsed_info('page_number')

    @property
    def sha512_hash(self) -> Optional[str]:
        return self.get_value_from_parsed_info('sha512_hash').digest()

    @property
    def link(self) -> Optional[str]:
        return self.get_value_from_parsed_info('link')

    @property
    def title(self) -> Optional[str]:
        return self.get_value_from_parsed_info('title')

    @property
    def date_published(self) -> Optional[str]:
        return self.get_value_from_parsed_info('date_published')
    
    # change this to content being extracted to scraped info
    @property
    def vintage(self) -> Optional[int]:
        try:
            return int(self.get_value_from_parsed_info('vintage'))
        except (TypeError, ValueError):
            return None

    @property
    def rating(self) -> Optional[int]:
        try:
            return int(self.get_value_from_parsed_info('rating'))
        except ValueError:
            return None

    @property
    def price(self) -> Optional[float]:
        try:
            return float(
                self.get_value_from_parsed_info('Price').split(",")[0][1:]
            )
        except ValueError:
            return None

    @property
    def designation(self) -> Optional[str]:
        try:
            return self.get_value_from_parsed_info('Designation')
        except KeyError:
            self.flags.append(3)
            return None

    @property
    def variety(self) -> Optional[str]:
        return self.get_value_from_parsed_info('Variety')

    @property
    def appellation(self) -> Optional[str]:
        return self.get_value_from_parsed_info('Appellation')

    @property
    def winery(self) -> Optional[str]:
        return self.get_value_from_parsed_info('Winery')

    @property
    def alcohol(self) -> Optional[float]:
        # don't include percent sign
        try:
            return float(self.get_value_from_parsed_info('Alcohol')[:-1])
        except ValueError:
            return None

    @property
    def bottle_size(self) -> Optional[int]:
        try:
            value, units = self.get_value_from_parsed_info('Bottle Size').split(" ")
            
            if units == 'L':
                return float(value) * 1000
            else:
                return float(value)

        except ValueError:
            return None

    @property
    def category(self) -> Optional[str]:
        return self.get_value_from_parsed_info('Category')

    @property
    def author_name(self) -> Optional[str]:
        return self.get_value_from_parsed_info('review.author.name')

    @property
    def review_body(self) -> Optional[str]:
        return self.get_value_from_parsed_info('review.reviewBody')

    @property
    def price_per_milliliter(self) -> Optional[float]:
        if self.price is None or self.bottle_size is None:
            return None
        return self.price / self.bottle_size

    def _get_primary_info(self) -> None:
        primary_info = self.content.findAll('ul', {'class':'primary-info'})[0]
        rows = primary_info.findAll('li', {'class': 'row'})
        for r in rows:
            self.scraped_info[r.find('div', {'class': 'info-label'}).find('span').text] = \
                r.find('div', {'class': 'info'}).find('span').text

    def _get_secondary_info(self) -> None:
        secondary_info = self.content.findAll('ul', {'class':'secondary-info'})[0]
        rows = secondary_info.findAll('li', {'class': 'row'})
        for r in rows:
            potential_key = r.find('div', {'class': 'info-label'}).find('span').text
            if potential_key in self.scraped_info:
                self.flags.append(4)
            self.scraped_info[potential_key] = r.find('div', {'class': 'info'}).find('span').text

    def _get_json_post_metadata(self) -> None:
        unwieldy_json = json.loads(
            self
            .content
            .find(
                'meta',
                {
                    'content': 'Wine Reviews',
                    'name': 'article:section'
                }
            )
            .find_next_sibling('script')
            .contents[0]
        )

        wieldy_json = (
            pandas
            .json_normalize(unwieldy_json)
            .iloc[0]
            .to_dict()
        )

        for k, v in wieldy_json.items():
            if k in self.scraped_info:
                self.flags.append(4)
            self.scraped_info[k] = v

    def _get_date_published(self) -> None:
        self.scraped_info['date_published'] = (
            self
            .content
            .find('meta', {'property':'article:published_time'})
            .attrs['content']
        )

    def _get_vintage_from_card_title(self) -> None:
        yearlike_in_title = year_finder.findall(self.card.title)
        if len(yearlike_in_title) > 0:
            if len(yearlike_in_title) > 1:
                # seems like the first year in the title is usually the vintage
                self.flags.append(1)                
        else:
            self.flags.append(2)
            self.scraped_info['vintage'] = None
            return

        self.scraped_info['vintage'] = int(yearlike_in_title[0])

    @classmethod
    def _get_all_properties(cls) -> List[str]:
        return sorted([
            k for k, v in vars(cls).items() if isinstance(v, property)
        ])

    def _get_properties_and_values(self) -> Dict[str, Any]:
        return {
            k: getattr(self, k) for k in self._get_all_properties()
        }


class AttributeRetriever(object):

    def __init__(self, name: str, parser_args: Optional[Tuple[str, Dict[str, str]]]):
        self.name = name
        self.args = parser_args

    @abc.abstractmethod
    def retriever(self):
        raise NotImplementedError("Must define the retriever method")
