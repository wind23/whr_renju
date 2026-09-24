import gc
import math
import os
import sys
from datetime import date
from game_base import GameBase
from rating_config import RATINGS, domain
from rating_output import RatingOutput
from whr import Base, Evaluate

input_xml = os.path.join(sys.path[0], "data", "renjunet_v10_%s.rif" % sys.argv[1])
rating = sys.argv[2]
save_json = os.path.join(
    sys.path[0], "data", "game_base_%s_%s.json" % (sys.argv[1], rating)
)
rated_tournaments = os.path.join(sys.path[0], "data", "rated_tournaments")
unrated_tournaments = os.path.join(sys.path[0], "data", "unrated_tournaments")
female = os.path.join(sys.path[0], "data", "female")
native_name = os.path.join(sys.path[0], "data", "native_name")

cur_date = (int(sys.argv[1][:4]), int(sys.argv[1][4:6]), int(sys.argv[1][6:8]))
start_year = RATINGS[rating]["start_year"]

base = GameBase(rating, cur_date=cur_date)

base.read_xml(
    input_xml,
    rated_tournaments=rated_tournaments,
    unrated_tournaments=unrated_tournaments,
)
train_games = base.gen_games()
w2 = RATINGS[rating]["w2"]
virtual_games = 2
base.set_w2(w2)
config = {"w2": w2, "virtual_games": virtual_games}
whr_base = Base(config=config)
whr_base.create_games(train_games)
whr_base.iterate_until_converge(verbose=False)
ratings = whr_base.get_ordered_ratings()
base.set_ratings(ratings)
base.save(save_json)

# The output stage does not need the WHR graph and the training games anymore;
# release them early so they do not stay in memory during the whole generation.
del whr_base
del train_games
gc.collect()

output = RatingOutput(base, bias=1900.0)

# print(output.compute_active_threshold())

output.gen_ratings()
cur_year = base.date.year
if base.date.month == 12 and base.date.day == 31:
    cur_year += 1
for country_id in output.country_set:
    output.gen_ratings(country_id=country_id)
for year in range(cur_year - 1, start_year - 1, -1):
    day = (date(year, 12, 31) - date(1970, 1, 1)).days
    output.gen_ratings(day=day)
    for country_id in output.country_set:
        output.gen_ratings(day=day, country_id=country_id)
output.gen_ratings(active_level=2)
for country_id in output.country_set:
    output.gen_ratings(country_id=country_id, active_level=2)
for year in range(cur_year - 1, start_year - 1, -1):
    day = (date(year, 12, 31) - date(1970, 1, 1)).days
    output.gen_ratings(day=day, active_level=2)
    for country_id in output.country_set:
        output.gen_ratings(day=day, country_id=country_id, active_level=2)
output.gen_ratings(active_level=0)
for country_id in output.country_set:
    output.gen_ratings(country_id=country_id, active_level=0)
for year in range(cur_year - 1, start_year - 1, -1):
    day = (date(year, 12, 31) - date(1970, 1, 1)).days
    output.gen_ratings(day=day, active_level=0)
    for country_id in output.country_set:
        output.gen_ratings(day=day, country_id=country_id, active_level=0)
output.gen_player()
output.gen_players()
output.gen_players_json()
output.gen_tournaments()
output.gen_tournament()
output.gen_top_ratings()
output.gen_top_ratings(female=True)
output.gen_sitemap()
# GitHub Pages serves the site on the custom domain declared in this file
cname = os.path.join(RATINGS[rating]["html_path"], "CNAME")
with open(cname, "w", newline="\n") as fout:
    fout.write(domain(rating))
if rating == "renju":
    output.gen_ljratings()
