#! /usr/bin/env python3

import argparse
import sys
import tqdm

from wine_reviews.scrape import WineReviewScraper

interesting_data_from_reviews = """
    date_published: <link href="https://www.winemag.com/wp-json/" rel="https://api.w.org/"/><meta content="2021-11-17T00:00:00+00:00" property="article:published_time"/>

    <meta content="Wine Reviews" name="article:section"/><script type="application/ld+json">{
        "@context": "https://schema.org",
        "@type": "Product",
        "image": "https://www.winemag.com/wp-content/assets/reviews/label-images/wine/wine/385231_05BE_BOY21.JPG",
        "name": "Fess Parker 2019 Sanford &amp; Benedict 1971 Single Vineyard Collection Pinot Noir (Sta. Rita Hills)",
        "category": "Red",
        "review": {
            "@type": "Review",
            "name": "Fess Parker 2019 Sanford &amp; Benedict 1971 Single Vineyard Collection Pinot Noir (Sta. Rita Hills)",
            "reviewRating": {
                "@type": "Rating",
                "bestRating": 100,
                "ratingValue": "95"
            },
            "author": {
                "@type": "Person",
                "name": "Matt Kettmann"
            },
            "datePublished": "1970-01-01T00:00:00+00:00",
            "reviewBody": "Hailing from the iconic vineyard's oldest vines, this excellent bottling begins with lightly poached currant and cranberry aromas, enhanced by peppery herbs and subtle oak spice. The tense, restrained and complex palate balances an elegant, fresh raspberry-paste flavor against tarragon and thyme.",
            "publisher": {
                "@type": "Organization",
                "name": "Wine Enthusiast",
                "address": "200 Summit Lake Drive Valhalla, NY 10595",
                "logo": {
                    "@type": "imageObject",
                    "url": "https://www.winemag.com/wp-content/themes/TrellisFoundation-child/assets/img/we_logo_mag_black_600x113.png",
                    "width": 319,
                    "height": 60
                }
            },
            "isAccessibleForFree": "False",
            "hasPart": {
                "@type": "WebPageElement",
                "isAccessibleForFree": "False",
                "cssSelector": ".bg-gated"
            }
        }
    }</script>

    ################################ Primary Info

    <ul class="primary-info">
    <li class="row">
    <div class="info-label medium-7 columns">
    <span>rating</span>
    </div>
    <div class="info medium-9 columns rating">
    <span><span>95</span></span>
    </div>
    </li>
    <li class="row">
    <div class="info-label medium-7 columns">
    <span>Price</span>
    </div>
    <div class="info medium-9 columns">
    <span><span>$70,<a class="buy-now__link" data-partner="label" href="http://www.fessparker.com" target="_blank">Buy Now</a></span></span>
    </div>
    </li>
    <li class="row">
    <div class="info-label medium-7 columns">
    <span>Designation</span>
    </div>
    <div class="info medium-9 columns">
    <span><span>Sanford &amp; Benedict 1971 Single Vineyard Collection</span></span>
    </div>
    </li>
    <li class="row">
    <div class="info-label medium-7 columns">
    <span>Variety</span>
    </div>
    <div class="info medium-9 columns">
    <span><a href="https://www.winemag.com/varietals/pinot-noir/">Pinot Noir</a></span>
    </div>
    </li>
    <li class="row">
    <div class="info-label medium-7 columns">
    <span>Appellation</span>
    </div>
    <div class="info medium-9 columns">
    <span><a href="https://www.winemag.com/?s=Sta.%20Rita%20Hills">Sta. Rita Hills</a>, <a href="https://www.winemag.com/region/central-coast/">Central Coast</a>, <a href="https://www.winemag.com/region/california/">California</a>, <a href="https://www.winemag.com/region/us/">US</a></span>
    </div>
    </li>
    <li class="row">
    <div class="info-label medium-7 columns">
    <span>Winery</span>
    </div>
    <div class="info medium-9 columns">
    <span><span><a href="https://www.winemag.com/?s=Fess%20Parker">Fess Parker</a></span></span>
    </div>
    </li>
    </ul>


    ################################# Secondary Info
    <ul class="secondary-info">
    <li class="row">
    <div class="info-label small-7 columns">
    <span>Alcohol</span>
    </div>
    <div class="info small-9 columns">
    <span><span>14.1%</span></span>
    </div>
    </li>
    <li class="row">
    <div class="info-label small-7 columns">
    <span>Bottle Size</span>
    </div>
    <div class="info small-9 columns">
    <span><span>750 ml</span></span>
    </div>
    </li>
    <li class="row">
    <div class="info-label small-7 columns">
    <span>Category</span>
    </div>
    <div class="info small-9 columns">
    <span><span>Red</span></span>
    </div>
    </li>
    <li class="row">
    <div class="info-label small-7 columns">
    <span>Date Published</span>
    </div>
    <div class="info small-9 columns">
    <span><span>12/31/2021</span></span>
    </div>
    </li>
    <li class="row">
    <div class="info-label small-7 columns">
    <span>User Avg Rating</span>
    </div>
    <div class="info small-9 columns">
    <span><

"""

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

    for page_num in range(args.pages_start, args.pages_end + 1):
        scraper = WineReviewScraper(page_num)
