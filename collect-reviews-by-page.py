#! /usr/bin/env python3

import argparse
import os
import sys
import time

import pandas

from sqlalchemy import create_engine

from wine_reviews.scrape_tools import WineReviewScraper
from wine_reviews.data_models import wine_reviews_base, WineReviews

script_directory_path = os.path.dirname(os.path.abspath(__file__))
default_sqlite_path = f"{script_directory_path}/wine-reviews.db"

last_page_number_crawled = 200

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

    parser.add_argument(
        "--wait-time", type=int, required=False, default=1,
        help="Time to politely wait between page scrapes"
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

    for page_num in range(args.pages_start, args.pages_end + 1):
        print(f"Scraping page number {page_num}")
        scraped_data = (
            WineReviewScraper(page_num, 5)
            .parse_review_pages()
        )

        # sometimes a scraped page has no entries
        if not scraped_data.empty:
            (
                scraped_data
                .to_sql(
                    WineReviews.__tablename__,
                    con=engine,
                    if_exists='append',
                    index=False
                )
            )
        print(f"Sleeping for {args.wait_time} secs before next scrape")
        time.sleep(args.wait_time)

    # load table and drop duplicates for convenience checking if running from ipython
    table = pandas.read_sql_table(WineReviews.__tablename__, con=engine)
    data = table.drop_duplicates('sha512_hash')
    
