"""Definition of every rating: which games it uses, where it is published.

The rating key is used as the compute_rating.py command line argument and as
the suffix of the game_base json file name.

All ratings come from the same renjunet database and are told apart by
(rule_category, blitz):
    rule_category: "1" = renju, "2" = gomoku
    blitz:         True takes only blitz tournaments, False only ordinary ones
                   (the two are disjoint)

Other fields:
    start_year / women_start_year: earliest year of the history pages and charts
    w2: daily variance parameter of WHR, tuned with evaluate.py on this rating
    url: site address, used for the cross links, the sitemap and the CNAME file
    repo: GitHub repository to push the generated site to
    html_path: directory the pages of this rating are generated into
"""

RATINGS = {
    "renju": {
        "name": "Renju",
        "rule_category": "1",
        "blitz": False,
        "html_path": "html_renju",
        "url": "https://rating.renju.net/",
        "repo": "renjurating",
        "ua_ga": "UA-119927498-1",
        "w2": 19.3,
        "start_year": 1989,
        "women_start_year": 1997,
    },
    "gomoku": {
        "name": "Gomoku",
        "rule_category": "2",
        "blitz": False,
        "html_path": "html_gomoku",
        "url": "https://gomokurating.renju.net/",
        "repo": "gomokurating",
        "ua_ga": "UA-173435487-1",
        "w2": 10.7,
        "start_year": 2004,
        "women_start_year": 2006,
    },
    "blitz": {
        "name": "Blitz Gomoku",
        "rule_category": "2",
        "blitz": True,
        "html_path": "html_gomokublitz",
        "url": "https://gomokublitzrating.renju.net/",
        "repo": "gomokublitzrating",
        "ua_ga": "UA-173435487-1",
        "w2": 10.7,
        "start_year": 2004,
        "women_start_year": 2006,
    },
}


def get(rating):
    return RATINGS[rating]


def rating_of(rule_category, blitz):
    """Look up the rating key from (rule category, blitz), for old json files."""
    for key, config in RATINGS.items():
        if config["rule_category"] == rule_category and config["blitz"] == blitz:
            return key
    raise KeyError("no rating for rule_category=%s, blitz=%s" % (rule_category, blitz))


def other_ratings(rating):
    """The other ratings, in RATINGS order, as (display name, url) pairs."""
    return [(config["name"], config["url"]) for key, config in RATINGS.items() if key != rating]


def domain(rating):
    """Bare host of the site, as written into the GitHub Pages CNAME file."""
    return RATINGS[rating]["url"].split("//", 1)[1].strip("/")
