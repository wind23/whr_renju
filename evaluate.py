import math
import os
import sys
from game_base import GameBase
from whr import Base, Evaluate

input_xml = os.path.join(sys.path[0], 'data', 'renjunet_v10_20191120.rif')
save_json = os.path.join(sys.path[0], 'data', 'game_base_evaluate.json')
unrated_rules = os.path.join(sys.path[0], 'data', 'unrated_rules')

base = GameBase()
base.read_xml(input_xml, unrated_rules=unrated_rules)
base.save(save_json)

train_games, evaluate_games = base.gen_games_evaluate_split(9, 1)
print(train_games)

w2 = 12.9
virtual_games = 2
config = {'w2': w2, 'virtual_games': virtual_games}
whr_base = Base(config=config)
whr_base.create_games(train_games)
whr_base.iterate(100)
ev = Evaluate(whr_base)
log_likelihood = ev.evaluate_ave_log_likelihood_games(evaluate_games)
print("w2: %.2f, Likelihood: %.10f" % (w2, math.exp(log_likelihood)))
