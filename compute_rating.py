import math
import os
import sys
from datetime import date
from game_base import GameBase
from rating_output import RatingOutput
from whr import Base, Evaluate

input_xml = os.path.join(sys.path[0], 'data',
                         'renjunet_v10_%s.rif' % sys.argv[1])
additional_input = os.path.join(sys.path[0], 'data', 'additional_input.txt')
save_json = os.path.join(sys.path[0], 'data',
                         'game_base_%s.json' % sys.argv[1])
unrated_rules = os.path.join(sys.path[0], 'data', 'unrated_rules')
rated_tournaments = os.path.join(sys.path[0], 'data', 'rated_tournaments')
unrated_tournaments = os.path.join(sys.path[0], 'data', 'unrated_tournaments')
female = os.path.join(sys.path[0], 'data', 'female')
native_name = os.path.join(sys.path[0], 'data', 'native_name')

cur_date = (int(sys.argv[1][:4]), int(sys.argv[1][4:6]), int(sys.argv[1][6:8]))

base = GameBase(cur_date=cur_date)

if not os.path.exists(save_json):
    base.read_xml(input_xml,
                  unrated_rules=unrated_rules,
                  rated_tournaments=rated_tournaments,
                  unrated_tournaments=unrated_tournaments)
    base.read_additional_input(additional_input)
    #base.read_female(female)
    #base.read_native_name(native_name)
    train_games = base.gen_games()
    w2 = 12.9
    virtual_games = 2
    config = {'w2': w2, 'virtual_games': virtual_games}
    whr_base = Base(config=config)
    whr_base.create_games(train_games)
    whr_base.iterate(100)
    ratings = whr_base.get_ordered_ratings()
    base.set_ratings(ratings)
    base.save(save_json)
else:
    base.load(save_json)

output = RatingOutput(base, bias=1900.0)

output.gen_ratings()
cur_year = base.date.year
if base.date.month == 12 and base.date.day == 31:
    cur_year += 1
for country_id in output.country_set:
    output.gen_ratings(country_id=country_id)
for year in range(cur_year - 1, 1988, -1):
    day = (date(year, 12, 31) - date(1970, 1, 1)).days
    output.gen_ratings(day=day)
    for country_id in output.country_set:
        output.gen_ratings(day=day, country_id=country_id)
output.gen_ratings(active_level=2)
for country_id in output.country_set:
    output.gen_ratings(country_id=country_id, active_level=2)
for year in range(cur_year - 1, 1988, -1):
    day = (date(year, 12, 31) - date(1970, 1, 1)).days
    output.gen_ratings(day=day, active_level=2)
    for country_id in output.country_set:
        output.gen_ratings(day=day, country_id=country_id, active_level=2)
output.gen_ratings(active_level=0)
for country_id in output.country_set:
    output.gen_ratings(country_id=country_id, active_level=0)
for year in range(cur_year - 1, 1988, -1):
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
output.gen_sitemap('https://rating.renju.net/')
output.gen_ljratings()
