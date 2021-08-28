from datetime import date, timedelta
import json
from xml.etree import ElementTree

# replace date.today


class GameBase():
    def __init__(self, cur_date=None):
        if not cur_date:
            self.date = date.today()
        else:
            self.date = date(cur_date[0], cur_date[1], cur_date[2])
        self.countries = {}
        self.cities = {}
        self.rules = {}
        self.players = {}
        self.tournaments = {}
        self.games = {}
        self.ratings = {}
        self.games_for_tournaments_cache = None
        self.history_for_players_cache = None

    def read_xml(self,
                 input_file,
                 rated_tournaments=None,
                 unrated_tournaments=None,
                 unrated_rules=None,
                 city_names=None,
                 tournament_names=None,
                 player_names=None):
        fin = open(input_file, encoding='utf-8', errors='replace')
        str_xml = fin.read()
        fin.close()
        etree = ElementTree.fromstring(str_xml)
        countries = etree.find('countries')
        cities = etree.find('cities')
        rules = etree.find('rules')
        players = etree.find('players')
        tournaments = etree.find('tournaments')
        games = etree.find('games')

        for country in countries:
            id_ = country.attrib['id']
            name = country.attrib['name']
            abbr = country.attrib['abbr']
            self.countries[id_] = {'name': name, 'abbr': abbr}

        city_name_map = {}
        if city_names:
            fin = open(city_names, 'r')
            for line in fin:
                id_, name = line.strip().split('\t')
                city_name_map[id_] = name
            fin.close()
        for city in cities:
            id_ = city.attrib['id']
            country = city.attrib['country']
            name = city.attrib['name']
            if id_ in city_name_map.keys():
                name = city_name_map[id_]
            self.cities[id_] = {'country': country, 'name': name}

        unrated_rule_list = set()
        if unrated_rules:
            fin = open(unrated_rules, 'r')
            for line in fin:
                rule = line.strip()
                unrated_rule_list.add(rule)
            fin.close()
        for rule in rules:
            id_ = rule.attrib['id']
            name = rule.attrib['name']
            if not id_ in unrated_rule_list:
                self.rules[id_] = {'name': name}

        player_name_map = {}
        if player_names:
            fin = open(player_names, 'r')
            for line in fin:
                id_, name, surname = line.strip().split('\t')
                player_name_map[id_] = (name, surname)
            fin.close()
        for player in players:
            id_ = player.attrib['id']
            name = player.attrib['name']
            surname = player.attrib['surname']
            if id_ in player_name_map.keys():
                name, surname = player_name_map[id_]
            country = player.attrib['country']
            city = player.attrib['city']
            self.players[id_] = {
                'name': name,
                'surname': surname,
                'country': country,
                'city': city,
                'female': False,
                'native_name': ''
            }

        unrated_tournament_list = set()
        if unrated_tournaments:
            fin = open(unrated_tournaments, 'r')
            for line in fin:
                tournament = line.strip()
                unrated_tournament_list.add(tournament)
            fin.close()
        rated_tournament_list = set()
        if rated_tournaments:
            fin = open(rated_tournaments, 'r')
            for line in fin:
                tournament = line.strip()
                rated_tournament_list.add(tournament)
            fin.close()
        tournaments_name_map = {}
        if tournament_names:
            fin = open(tournament_names, 'r')
            for line in fin:
                id_, name = line.strip().split('\t')
                tournaments_name_map[id_] = name
            fin.close()
        for tournament in tournaments:
            id_ = tournament.attrib['id']
            name = tournament.attrib['name']
            if id_ in tournaments_name_map.keys():
                name = tournaments_name_map[id_]
            country = tournament.attrib['country']
            city = tournament.attrib['city']
            start = tournament.attrib['start']
            if not start:
                continue
            end = tournament.attrib['end']
            if not end:
                continue
            if start == '0000-00-00' and end == '0000-00-00':
                year = int(tournament.attrib['year'])
                month = int(tournament.attrib['month'])
                start = '%04d-%02d-%02d' % (year, month, 1)
                if month < 12:
                    end = '%04d-%02d-%02d' % (year, month,
                                              (date(year, month + 1, 1) -
                                               timedelta(1)).day)
                else:
                    end = '%04d-%02d-%02d' % (year, month,
                                              (date(year + 1, 1, 1) -
                                               timedelta(1)).day)
            elif start == '0000-00-00':
                start = end
            elif end == '0000-00-00':
                end = start
            if start > end:
                start = end
            start = list(map(int, start.split('-')))
            if start[0] == 0:
                continue
            if start[2] == 0:
                start[2] = 1
            if date(start[0], start[1], start[2]) <= self.date:
                start = '%04d-%02d-%02d' % (start[0], start[1], start[2])
            else:
                continue
            end = list(map(int, end.split('-')))
            if end[0] == 0:
                continue
            if end[2] == 0:
                end[2] = 1
            if date(end[0], end[1], end[2]) <= self.date:
                end = '%04d-%02d-%02d' % (end[0], end[1], end[2])
            else:
                continue
            rule = tournament.attrib['rule']
            rated = bool(int(tournament.attrib['rated']))
            if rule in unrated_rule_list:
                rated = False
            if id_ in unrated_tournament_list:
                rated = False
            if id_ in rated_tournament_list:
                rated = True
            if rated:
                self.tournaments[id_] = {
                    'name': name,
                    'country': country,
                    'city': city,
                    'start': start,
                    'end': end,
                    'rule': rule
                }

        for game in games:
            id_ = game.attrib['id']
            tournament = game.attrib['tournament']
            if not tournament in self.tournaments.keys():
                continue
            round_ = game.attrib.get('round', '')
            rule = game.attrib['rule']
            black = game.attrib['black']
            white = game.attrib['white']
            if black == white:
                continue
            result = game.attrib['bresult']
            if not result:
                continue
            result = float(result)
            if result == 1.:
                result = 'B'
            elif result == 0.5:
                result = 'D'
            elif result == 0.:
                result = 'W'
            self.games[id_] = {
                'tournament': tournament,
                'round': round_,
                'rule': rule,
                'black': black,
                'white': white,
                'result': result
            }

    def read_additional_input(self, input_file):
        fin = open(input_file, 'r')
        for line in fin:
            line = line.strip()
            if not line:
                continue
            type_, content = line.split('\t', 1)
            if type_ == 'country':
                id_, name, abbr = content.split('\t')
                self.countries[id_] = {'name': name, 'abbr': abbr}
            elif type_ == 'city':
                id_, country, name = content.split('\t')
                self.cities[id_] = {'country': country, 'name': name}
            elif type_ == 'rule':
                id_, name = content.split('\t')
                self.rules[id_] = {'name': name}
            elif type_ == 'player':
                id_, name, surname, country, city = content.split('\t')
                self.players[id_] = {
                    'name': name,
                    'surname': surname,
                    'country': country,
                    'city': city,
                    'female': False,
                    'native_name': ''
                }
            elif type_ == 'tournament':
                id_, name, country, city, start, end, rule = content.split(
                    '\t')
                start = list(map(int, start.split('-')))
                if date(start[0], start[1], start[2]) <= self.date:
                    start = '%04d-%02d-%02d' % (start[0], start[1], start[2])
                else:
                    continue
                end = list(map(int, end.split('-')))
                if date(end[0], end[1], end[2]) <= self.date:
                    end = '%04d-%02d-%02d' % (end[0], end[1], end[2])
                else:
                    continue
                self.tournaments[id_] = {
                    'name': name,
                    'country': country,
                    'city': city,
                    'start': start,
                    'end': end,
                    'rule': rule
                }
            elif type_ == 'game':
                id_, tournament, round_, rule, black, white, result = content.split(
                    '\t')
                if black == white:
                    continue
                self.games[id_] = {
                    'tournament': tournament,
                    'round': round_,
                    'rule': rule,
                    'black': black,
                    'white': white,
                    'result': result
                }
        fin.close()

    def read_female(self, female):
        female_players = set()
        female_tournaments = {}
        fin = open(female, 'r')
        for line in fin:
            line = line.strip()
            if not line:
                continue
            type_, content = line.split('\t', 1)
            if type_ == 'player':
                id_ = content
                female_players.add(id_)
            elif type_ == 'tournament':
                id_, rounds = content.split('\t')
                if rounds == '*':
                    rounds = None
                else:
                    rounds = rounds.split(',')
                female_tournaments[id_] = rounds
        fin.close()
        for player_id in female_players:
            self.players[player_id]['female'] = True
        for game in self.games.values():
            tournament_id = game['tournament']
            if tournament_id in female_tournaments.keys():
                rounds = female_tournaments[tournament_id]
                if rounds is None:
                    is_female = True
                else:
                    is_female = False
                    for round_ in rounds:
                        if game['round'].upper().startswith(round_):
                            is_female = True
                if is_female:
                    self.players[game['black']]['female'] = True
                    self.players[game['white']]['female'] = True

    def read_native_name(self, native_name):
        fin = open(native_name, 'r', encoding='utf-8')
        for line in fin:
            line = line.strip()
            if not line:
                continue
            player_id, native_name = line.split('\t')
            if native_name == '*':
                continue
            self.players[player_id]['native_name'] = native_name
        fin.close()

    def save(self, save_file):
        date_ = (self.date.year, self.date.month, self.date.day)
        save_objects = {
            'date': date_,
            'countries': self.countries,
            'cities': self.cities,
            'rules': self.rules,
            'players': self.players,
            'tournaments': self.tournaments,
            'games': self.games,
            'ratings': self.ratings
        }
        fout = open(save_file, 'w')
        json.dump(save_objects, fout, indent=4)
        fout.close()

    def load(self, load_file):
        fin = open(load_file, 'r')
        load_objects = json.load(fin)
        fin.close()
        date_ = load_objects['date']
        self.date = date(date_[0], date_[1], date_[2])
        self.countries = load_objects['countries']
        self.cities = load_objects['cities']
        self.rules = load_objects['rules']
        self.players = load_objects['players']
        self.tournaments = load_objects['tournaments']
        self.games = load_objects['games']
        self.ratings = load_objects['ratings']

    def date_to_day(self, date_):
        if type(date_) == str:
            date_ = list(map(int, date_.split('-')))
        elif type(date_) == date:
            date_ = (date_.year, date_.month, date_.day)
        return (date(date_[0], date_[1], date_[2]) - date(1970, 1, 1)).days

    def gen_games(self):
        games = []
        for game in self.games.values():
            black = game['black']
            white = game['white']
            winner = game['result']
            tournament = game['tournament']
            tournament = self.tournaments[tournament]
            day = self.date_to_day(tournament['end'])
            games.append((black, white, winner, day))
        games.sort(key=lambda g: g[3])
        return games

    def gen_games_evaluate_split(self, train_count, evaluate_count):
        if train_count <= 0 or evaluate_count <= 0:
            return None
        train_games = []
        evaluate_games = []
        gcount = 0
        for game in self.gen_games():
            black, white, winner, day = game
            if gcount % (train_count + evaluate_count) < train_count:
                train_games.append((black, white, winner, day))
            else:
                evaluate_games.append((black, white, winner, day))
            gcount += 1
        train_games.sort(key=lambda g: g[3])
        evaluate_games.sort(key=lambda g: g[3])
        return [train_games, evaluate_games]

    def set_ratings(self, ratings):
        for id_, rating in ratings:
            self.ratings[id_] = rating

    def get_player_rating_on_day(self, player, day):
        ratings = self.ratings[player]
        min_day, min_rating = None, None
        max_day, max_rating = None, None
        if not player in self.ratings.keys():
            return 0.
        ratings = self.ratings[player]
        for i in range(len(ratings)):
            if ratings[i][0] <= day:
                if (not min_day) or (ratings[i][0] >= min_day):
                    min_day = ratings[i][0]
                    min_rating = ratings[i][1]
            if ratings[i][0] >= day:
                if (not max_day) or (ratings[i][0] <= max_day):
                    max_day = ratings[i][0]
                    max_rating = ratings[i][1]
        if not min_day:
            ret = None
        elif not max_day:
            ret = min_rating
        elif max_day <= min_day:
            ret = max_rating
        else:
            ret = ((max_day - day) * min_rating +
                   (day - min_day) * max_rating) * 1.0 / (max_day - min_day)
        return ret

    def get_ratings_on_day(self, day):
        ret = {}
        for player in self.ratings.keys():
            player_rating = self.get_player_rating_on_day(player, day)
            if player_rating:
                ret[player] = player_rating
        return ret

    def get_ratings_latest(self):
        return self.get_ratings_on_day(self.date_to_day(self.date))

    def get_game_count_within_n_years_on_day(self, year, day):
        cur_date = date(1970, 1, 1) + timedelta(day)
        cur_date = (cur_date.year, cur_date.month, cur_date.day)
        game_count = {}
        for game in self.games.values():
            black = game['black']
            white = game['white']
            game_count.setdefault(black, 0)
            game_count.setdefault(white, 0)
            tournament = game['tournament']
            tournament_date = self.tournaments[tournament]['end']
            tournament_date = tuple(map(int, tournament_date.split('-')))
            if tournament_date <= cur_date:
                if cur_date[0] - tournament_date[0] < year or (
                        cur_date[0] - tournament_date[0] == year and
                    (cur_date[1], cur_date[2]) <
                    (tournament_date[1], tournament_date[2])):
                    game_count[black] += 1
                    game_count[white] += 1
        return game_count

    def get_game_count_within_n_years_latest(self, year):
        return self.get_game_count_within_n_years_on_day(
            year, self.date_to_day(self.date))

    def get_game_count_so_far_on_day(self, day):
        return self.get_game_count_within_n_years_on_day(3000, day)

    def get_game_count_so_far_latest(self):
        return self.get_game_count_so_far_on_day(self.date_to_day(self.date))

    def round_to_key(self, s):
        ret = []
        for c in s:
            if c >= '0' and c <= '9':
                if (not ret) or ret[-1][0] == 1:
                    ret.append((0, int(c), 1))
                else:
                    ret[-1] = (0, ret[-1][1] * 10 + int(c), ret[-1][2] + 1)
            else:
                ret.append((1, c))
        return ret

    def get_games_for_tournaments(self):
        if self.games_for_tournaments_cache != None:
            return self.games_for_tournaments_cache
        ret = {}
        for game_id, game in self.games.items():
            tournament = game['tournament']
            ret.setdefault(tournament, [])
            ret[tournament].append(game_id)
        for game_list in ret.values():
            game_list.sort(
                key=lambda gid: self.round_to_key(self.games[gid]['round']))
        self.games_for_tournaments_cache = ret
        return ret

    def get_history_for_players(self):
        if self.history_for_players_cache != None:
            return self.history_for_players_cache
        ret = {}
        for game_id, game in self.games.items():
            black = game['black']
            white = game['white']
            tournament = game['tournament']
            for player in (black, white):
                ret.setdefault(player, {})
                ret[player].setdefault(tournament, [])
                ret[player][tournament].append(game_id)
        for player, tournaments in ret.items():
            tournaments = sorted(tournaments.items(),
                                 key=lambda t: (self.tournaments[t[0]][
                                     'end'], self.tournaments[t[0]]['start']))
            ret[player] = tournaments
            for tournament_id, game_list in tournaments:
                game_list.sort(key=lambda gid: self.round_to_key(self.games[
                    gid]['round']))
        self.history_for_players_cache = ret
        return ret
