#! /usr/bin/env python3

import argparse
import os
import sys

import pandas

from sqlalchemy import create_engine

from wine_reviews.scrape import WineReviewScraper
from wine_reviews.data_models import wine_reviews_base, WineReviews

script_directory_path = os.path.dirname(os.path.abspath(__file__))
default_sqlite_path = f"{script_directory_path}/wine-reviews.db"

if __name__ == "__main__":

    desc = """
        This script requests each page from the wine-reviews website defined by
        page_start to page_end. Then it scrapes the pages to get the interesting
        data for modeling
    """

    parser = argparse.ArgumentParser(
        prog='collect-reviews-by-page.py', description=desc
    )

    parser.add_argument(
        '--pages-start', type=int, required=True,
        help="First page to download wine reviews (> 0)"
    )

    parser.add_argument(
        '--pages-end', type=int, required=True,
        help="Last page to download wine reviews (>= --pages-start)"
    )

    parser.add_argument(
        "--sqlite-path", type=str, required=False, default=default_sqlite_path,
        help="Path to sqlite database for wine reviews dumps"
    )

    args = parser.parse_args()

    engine = create_engine(f"sqlite:///{args.sqlite_path}")
    wine_reviews_base.metadata.create_all(engine)

    # do some argument checking
    if args.pages_start > 0:
        if args.pages_end < args.pages_start:
            sys.exit("Page Range ERROR: --pages-end has to be greater than --pages-start!")
    else:
        sys.exit(
            """
                Page Range ERROR: --pages-start has to be greater than 0!\n
            """
        )

    data = pandas.DataFrame()
    for page_num in range(args.pages_start, args.pages_end + 1):
        print(f"Scraping page number {page_num}")
        scraper = WineReviewScraper(page_num, 5)
        data = data.append(scraper.parse_review_pages())
    
    data.to_sql(
        WineReviews.__tablename__, con=engine, if_exists='append', index=False
    )
