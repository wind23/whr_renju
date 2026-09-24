import math
import os
import sys
from game_base import GameBase
from rating_config import RATINGS
from whr import Base, Evaluate

# Optional argument is a rating key (see rating_config.py), renju by default
rating = sys.argv[1] if len(sys.argv) > 1 else "renju"

input_xml = os.path.join(sys.path[0], "data", "renjunet_v10_20240330.rif")
save_json = os.path.join(sys.path[0], "data", "game_base_evaluate.json")

base = GameBase(rating)
base.read_xml(input_xml)
base.save(save_json)

train_games, evaluate_games = base.gen_games_evaluate_split(9, 1)

w2 = RATINGS[rating]["w2"]
virtual_games = 2
config = {"w2": w2, "virtual_games": virtual_games}
whr_base = Base(config=config)
whr_base.create_games(train_games)
whr_base.iterate_until_converge(verbose=False)
ev = Evaluate(whr_base)
log_likelihood = ev.evaluate_ave_log_likelihood_games(evaluate_games)
print("w2: %.2f, Likelihood: %.10f" % (w2, math.exp(log_likelihood)))
