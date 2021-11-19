#! /usr/bin/env python3

import argparse
import sys

import pandas

from wine_reviews.scrape import WineReviewScraper

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

    args = parser.parse_args()

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
        scraper = WineReviewScraper(page_num)
        data.append(scraper.parse_review_page())
