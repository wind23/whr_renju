import os
import sys
import json
from datetime import date, timedelta, datetime, timezone
from yattag import Doc, indent
from xml.etree import ElementTree
from xml.dom import minidom


class RatingOutput:

    def __init__(self, base, bias=1600.):
        self.base = base
        self.bias = bias
        self.top_players = {}
        self.top_players_women = {}
        self.rank = {}
        self.topN = {}
        self.topN_women = {}
        self.country_set = set()
        self.gy1_cache = {}
        self.gy2_cache = {}
        self.gy5_cache = {}
        self.gcount_cache = None
        self.save_path = sys.path[0]
        self.rating_path = 'index.html'
        self.rating_gy1_path = 'rating_gy1.html'
        self.rating_all_path = 'rating_all.html'
        self.rating_date_path = 'rating_%04d%02d%02d.html'
        self.rating_gy1_date_path = 'rating_gy1_%04d%02d%02d.html'
        self.rating_all_date_path = 'rating_all_%04d%02d%02d.html'
        self.rating_country_path = 'rating_c%s.html'
        self.rating_gy1_country_path = 'rating_gy1_c%s.html'
        self.rating_all_country_path = 'rating_all_c%s.html'
        self.rating_country_date_path = 'rating_c%s_%04d%02d%02d.html'
        self.rating_gy1_country_date_path = 'rating_gy1_c%s_%04d%02d%02d.html'
        self.rating_all_country_date_path = 'rating_all_c%s_%04d%02d%02d.html'
        self.flag_path = 'flag/%s.svg'
        self.game_path = 'https://www.renju.net/game/%s/'
        self.player_path = 'player_%s.html'
        self.players_path = 'players.html'
        self.players_json_path = 'players.json'
        self.tournament_path = 'tournament_%s.html'
        self.tournaments_path = 'tournaments.html'
        self.top_rating_path = 'top.html'
        self.top_rating_women_path = 'top_women.html'
        self.ljrating_path = 'ljrating.html'
        self.sitemap_path = 'sitemap.xml'
        self.gomoku_path = 'https://gomokurating.wind23.com/'
        self.ljinfo_name = 'ljinfo.csv'
        self.ljcountry_name = 'ljcountry.csv'
        self.ljcity_name = 'ljcity.csv'
        self.pages = []

        ratings = self.base.get_ratings_latest()
        if self.gcount_cache == None:
            gcounts = self.base.get_game_count_so_far_latest()
            self.gcount_cache = gcounts
        else:
            gcounts = self.gcount_cache
        for player, rating in ratings.items():
            gcount = gcounts[player]
            is_established = (gcount >= 10)
            cur_country_id = self.base.players[player]['country']
            self.country_set.add(cur_country_id)

        self.n_games = len(self.base.games)
        self.n_players = len(
            {game['black'] for game in self.base.games.values()} |
            {game['white'] for game in self.base.games.values()})

    def flag(self, doc, country, klass='flag'):
        return
        doc.stag('img', src=self.flag_path % country, klass=klass, alt=country)

    def gen_ratings(self, active_level=1, day=None, country_id=None):
        if day == None:
            ratings = self.base.get_ratings_latest()
            gy1s = self.gy1_cache.get(None, None)
            if gy1s == None:
                gy1s = self.base.get_game_count_within_n_years_latest(1)
                self.gy1_cache[None] = gy1s
            gy2s = self.gy2_cache.get(None, None)
            if gy2s == None:
                gy2s = self.base.get_game_count_within_n_years_latest(2)
                self.gy2_cache[None] = gy2s
            gy5s = self.gy5_cache.get(None, None)
            if gy5s == None:
                gy5s = self.base.get_game_count_within_n_years_latest(5)
                self.gy5_cache[None] = gy5s
        else:
            ratings = self.base.get_ratings_on_day(day)
            gy1s = self.gy1_cache.get(day, None)
            if gy1s == None:
                gy1s = self.base.get_game_count_within_n_years_on_day(1, day)
                self.gy1_cache[day] = gy1s
            gy2s = self.gy2_cache.get(day, None)
            if gy2s == None:
                gy2s = self.base.get_game_count_within_n_years_on_day(2, day)
                self.gy2_cache[day] = gy2s
            gy5s = self.gy5_cache.get(day, None)
            if gy5s == None:
                gy5s = self.base.get_game_count_within_n_years_on_day(5, day)
                self.gy5_cache[day] = gy5s
        if self.gcount_cache == None:
            gcounts = self.base.get_game_count_so_far_latest()
            self.gcount_cache = gcounts
        else:
            gcounts = self.gcount_cache
        ratings = sorted(ratings.items(), key=lambda x: x[1][0], reverse=True)
        outputs = []
        cur_rank = 0
        cur_rank_women = 0
        gy1_rank = 0
        gy1_rank_women = 0
        top_rating = None
        top_rating_women = None
        for player, rating in ratings:
            rating, uncertainty = rating
            cur_country_id = self.base.players[player]['country']
            country = self.base.countries[cur_country_id]['abbr']
            country_name = self.base.countries[cur_country_id]['name']
            if country_id is not None:
                if cur_country_id != country_id:
                    continue
            name = self.base.players[player]['name']
            surname = self.base.players[player]['surname']
            native_name = self.base.players[player]['native_name']
            female = self.base.players[player]['female']
            gy1 = gy1s[player]
            gy2 = gy2s[player]
            gy5 = gy5s[player]
            gcount = gcounts[player]
            is_established = (gcount >= 10)
            if active_level == 1:
                is_active = (gy5 > 0)
            elif active_level == 2:
                is_active = (gy1 >= 10)
            elif active_level == 0:
                is_active = True
            if day is None:
                women_start = True
            else:
                women_start = (date(1970, 1, 1) + timedelta(day)).year >= 1997
            if (is_established and is_active) or (not active_level > 0):
                cur_rank += 1
                if women_start and female:
                    cur_rank_women += 1
                if gy1 > 0:
                    gy1_rank += 1
                    if women_start and female:
                        gy1_rank_women += 1
                rank = '%d' % cur_rank
                if country_id is None and active_level == 1:
                    if day == None:
                        self.rank[player] = rank
                    if cur_rank == 1:
                        top_rating = rating
                    if women_start and female and cur_rank_women == 1:
                        top_rating_women = rating
                    if cur_rank <= 12 and top_rating - rating <= 165:
                        self.top_players.setdefault(player, rating)
                        if rating > self.top_players[player]:
                            self.top_players[player] = rating
                    if women_start and female and cur_rank_women <= 12 and top_rating_women - rating <= 165:
                        self.top_players_women.setdefault(player, rating)
                        if rating > self.top_players_women[player]:
                            self.top_players_women[player] = rating
                    if gy1 > 0 and gy1_rank <= 5 and day != None:
                        cur_date = date(1970, 1, 1) + timedelta(day)
                        cur_date = '%04d' % cur_date.year
                        self.topN.setdefault(cur_date, [])
                        self.topN[cur_date].append(player)
                    if women_start and female and gy1 > 0 and gy1_rank_women <= 5 and day != None:
                        cur_date = date(1970, 1, 1) + timedelta(day)
                        cur_date = '%04d' % cur_date.year
                        self.topN_women.setdefault(cur_date, [])
                        self.topN_women[cur_date].append(player)
            else:
                rank = ''
            if ((not active_level > 0) or (is_active and is_established)):
                outputs.append((player, rank, country, country_name, surname,
                                name, native_name, rating + self.bias,
                                uncertainty, gy1, gy2, gy5, female))

        if day == None:
            if active_level == 1:
                if country_id is None:
                    title = 'Whole History Rating (WHR) of Active Renju Players'
                    dst = self.rating_path
                else:
                    title = 'Whole History Rating (WHR) of Active Renju Players in %s' % (
                        self.base.countries[country_id]['name'])
                    dst = self.rating_country_path % country_id
            elif active_level == 2:
                if country_id is None:
                    title = 'Whole History Rating (WHR) of Active Renju Players (Gy1≥10)'
                    dst = self.rating_gy1_path
                else:
                    title = 'Whole History Rating (WHR) of Active Renju Players in %s (Gy1≥10)' % (
                        self.base.countries[country_id]['name'])
                    dst = self.rating_gy1_country_path % country_id
            elif active_level == 0:
                if country_id is None:
                    title = 'Whole History Rating (WHR) of All Renju Players'
                    dst = self.rating_all_path
                else:
                    title = 'Whole History Rating (WHR) of All Renju Players in %s' % (
                        self.base.countries[country_id]['name'])
                    dst = self.rating_all_country_path % country_id
        elif day != None:
            date_ = date(1970, 1, 1) + timedelta(day)
            if active_level == 1:
                if country_id is None:
                    title = 'Whole History Rating (WHR) of Active Renju Players (%04d-%02d-%02d)' % (
                        date_.year, date_.month, date_.day)
                    dst = self.rating_date_path % (date_.year, date_.month,
                                                   date_.day)
                else:
                    title = 'Whole History Rating (WHR) of Active Renju Players in %s (%04d-%02d-%02d)' % (
                        self.base.countries[country_id]['name'], date_.year,
                        date_.month, date_.day)
                    dst = self.rating_country_date_path % (
                        country_id, date_.year, date_.month, date_.day)
            elif active_level == 2:
                if country_id is None:
                    title = 'Whole History Rating (WHR) of Active Renju Players (%04d-%02d-%02d) (Gy1≥10)' % (
                        date_.year, date_.month, date_.day)
                    dst = self.rating_gy1_date_path % (date_.year, date_.month,
                                                       date_.day)
                else:
                    title = 'Whole History Rating (WHR) of Active Renju Players in %s (%04d-%02d-%02d) (Gy1≥10)' % (
                        self.base.countries[country_id]['name'], date_.year,
                        date_.month, date_.day)
                    dst = self.rating_gy1_country_date_path % (
                        country_id, date_.year, date_.month, date_.day)
            elif active_level == 0:
                if country_id is None:
                    title = 'Whole History Rating (WHR) of All Renju Players (%04d-%02d-%02d)' % (
                        date_.year, date_.month, date_.day)
                    dst = self.rating_all_date_path % (date_.year, date_.month,
                                                       date_.day)
                else:
                    title = 'Whole History Rating (WHR) of All Renju Players in %s (%04d-%02d-%02d)' % (
                        self.base.countries[country_id]['name'], date_.year,
                        date_.month, date_.day)
                    dst = self.rating_all_country_date_path % (
                        country_id, date_.year, date_.month, date_.day)

        doc, tag, text, line = Doc().ttl()
        line('h1', title)
        doc.asis(
            f'<p><b>Last update:</b> { self.base.date.strftime("%Y-%m-%d") }, <b>Players:</b> { self.n_players }, <b>Games:</b> { self.n_games }</p>'
        )
        doc.asis(
            '<p><b>Note:</b> This rating is calculated based on the <a href="https://www.remi-coulom.fr/WHR/">WHR algorithm</a> by Rémi Coulom, a similar approach as the <a href="https://www.goratings.org/en/">Go Ratings</a>. The core algorithm is based on the <a href="https://github.com/wind23/whr_renju">open-source code</a> on Github. The Elo version of the renju rating can be found <a href="http://renjuoffline.com/renju-rating/">here</a>.  Just for observing the variation of renju player ratings in a different view!</p>'
        )
        with tag('p'):
            doc.asis('<b>History ratings: </b>')
            with tag(
                    'select',
                    onchange=
                    "this.options[this.selectedIndex].value && (window.location = this.options[this.selectedIndex].value);"
            ):
                if day == None:
                    if active_level == 1:
                        if country_id is None:
                            line('option',
                                 'Current',
                                 value=self.rating_path,
                                 selected='selected')
                        else:
                            line('option',
                                 'Current',
                                 value=self.rating_country_path % country_id,
                                 selected='selected')
                    elif active_level == 2:
                        if country_id is None:
                            line('option',
                                 'Current',
                                 value=self.rating_gy1_path,
                                 selected='selected')
                        else:
                            line('option',
                                 'Current',
                                 value=self.rating_gy1_country_path %
                                 country_id,
                                 selected='selected')
                    elif active_level == 0:
                        if country_id is None:
                            line('option',
                                 'Current',
                                 value=self.rating_all_path,
                                 selected='selected')
                        else:
                            line('option',
                                 'Current',
                                 value=self.rating_all_country_path %
                                 country_id,
                                 selected='selected')
                else:
                    if active_level == 1:
                        if country_id is None:
                            line('option', 'Current', value=self.rating_path)
                        else:
                            line('option',
                                 'Current',
                                 value=self.rating_country_path % country_id)
                    elif active_level == 2:
                        if country_id is None:
                            line('option',
                                 'Current',
                                 value=self.rating_gy1_path)
                        else:
                            line('option',
                                 'Current',
                                 value=self.rating_gy1_country_path %
                                 country_id)
                    elif active_level == 0:
                        if country_id is None:
                            line('option',
                                 'Current',
                                 value=self.rating_all_path)
                        else:
                            line('option',
                                 'Current',
                                 value=self.rating_all_country_path %
                                 country_id)
                    cur_year = (date(1970, 1, 1) + timedelta(day)).year
                for year in range(self.base.date.year - 1, 1988, -1):
                    if day != None and cur_year == year:
                        if active_level == 1:
                            if country_id is None:
                                line('option',
                                     '%04d' % year,
                                     value=self.rating_date_path %
                                     (year, 12, 31),
                                     selected='selected')
                            else:
                                line('option',
                                     '%04d' % year,
                                     value=self.rating_country_date_path %
                                     (country_id, year, 12, 31),
                                     selected='selected')
                        elif active_level == 2:
                            if country_id is None:
                                line('option',
                                     '%04d' % year,
                                     value=self.rating_gy1_date_path %
                                     (year, 12, 31),
                                     selected='selected')
                            else:
                                line('option',
                                     '%04d' % year,
                                     value=self.rating_gy1_country_date_path %
                                     (country_id, year, 12, 31),
                                     selected='selected')
                        elif active_level == 0:
                            if country_id is None:
                                line('option',
                                     '%04d' % year,
                                     value=self.rating_all_date_path %
                                     (year, 12, 31),
                                     selected='selected')
                            else:
                                line('option',
                                     '%04d' % year,
                                     value=self.rating_all_country_date_path %
                                     (country_id, year, 12, 31),
                                     selected='selected')
                    else:
                        if active_level == 1:
                            if country_id is None:
                                line('option',
                                     '%04d' % year,
                                     value=self.rating_date_path %
                                     (year, 12, 31))
                            else:
                                line('option',
                                     '%04d' % year,
                                     value=self.rating_country_date_path %
                                     (country_id, year, 12, 31))
                        elif active_level == 2:
                            if country_id is None:
                                line('option',
                                     '%04d' % year,
                                     value=self.rating_gy1_date_path %
                                     (year, 12, 31))
                            else:
                                line('option',
                                     '%04d' % year,
                                     value=self.rating_gy1_country_date_path %
                                     (country_id, year, 12, 31))
                        elif active_level == 0:
                            if country_id is None:
                                line('option',
                                     '%04d' % year,
                                     value=self.rating_all_date_path %
                                     (year, 12, 31))
                            else:
                                line('option',
                                     '%04d' % year,
                                     value=self.rating_all_country_date_path %
                                     (country_id, year, 12, 31))
            doc.asis('&nbsp;&nbsp;&nbsp;&nbsp;<b>Country/Region: </b>')
            with tag(
                    'select',
                    onchange=
                    "this.options[this.selectedIndex].value && (window.location = this.options[this.selectedIndex].value);"
            ):
                if country_id == None:
                    if active_level == 1:
                        if day is None:
                            line('option',
                                 'All',
                                 value=self.rating_path,
                                 selected='selected')
                        else:
                            cur_year = (date(1970, 1, 1) + timedelta(day)).year
                            line('option',
                                 'All',
                                 value=self.rating_date_path %
                                 (cur_year, 12, 31),
                                 selected='selected')
                    elif active_level == 2:
                        if day is None:
                            line('option',
                                 'All',
                                 value=self.rating_gy1_path,
                                 selected='selected')
                        else:
                            cur_year = (date(1970, 1, 1) + timedelta(day)).year
                            line('option',
                                 'All',
                                 value=self.rating_gy1_date_path %
                                 (cur_year, 12, 31),
                                 selected='selected')
                    elif active_level == 0:
                        if day is None:
                            line('option',
                                 'All',
                                 value=self.rating_all_path,
                                 selected='selected')
                        else:
                            cur_year = (date(1970, 1, 1) + timedelta(day)).year
                            line('option',
                                 'All',
                                 value=self.rating_all_date_path %
                                 (cur_year, 12, 31),
                                 selected='selected')
                else:
                    if active_level == 1:
                        if day is None:
                            line('option', 'All', value=self.rating_path)
                        else:
                            cur_year = (date(1970, 1, 1) + timedelta(day)).year
                            line('option',
                                 'All',
                                 value=self.rating_date_path %
                                 (cur_year, 12, 31))
                    elif active_level == 2:
                        if day is None:
                            line('option', 'All', value=self.rating_gy1_path)
                        else:
                            cur_year = (date(1970, 1, 1) + timedelta(day)).year
                            line('option',
                                 'All',
                                 value=self.rating_gy1_date_path %
                                 (cur_year, 12, 31))
                    elif active_level == 0:
                        if day is None:
                            line('option', 'All', value=self.rating_all_path)
                        else:
                            cur_year = (date(1970, 1, 1) + timedelta(day)).year
                            line('option',
                                 'All',
                                 value=self.rating_all_date_path %
                                 (cur_year, 12, 31))
                sorted_country_list = sorted(
                    self.country_set,
                    key=lambda x: self.base.countries[x]['name'])
                for list_country_id in sorted_country_list:
                    if country_id != None and country_id == list_country_id:
                        if active_level == 1:
                            if day is None:
                                line('option',
                                     self.base.countries[list_country_id]
                                     ['name'],
                                     value=self.rating_country_path %
                                     list_country_id,
                                     selected='selected')
                            else:
                                cur_year = (date(1970, 1, 1) +
                                            timedelta(day)).year
                                line('option',
                                     self.base.countries[list_country_id]
                                     ['name'],
                                     value=self.rating_country_date_path %
                                     (list_country_id, cur_year, 12, 31),
                                     selected='selected')
                        elif active_level == 2:
                            if day is None:
                                line('option',
                                     self.base.countries[list_country_id]
                                     ['name'],
                                     value=self.rating_gy1_country_path %
                                     list_country_id,
                                     selected='selected')
                            else:
                                cur_year = (date(1970, 1, 1) +
                                            timedelta(day)).year
                                line('option',
                                     self.base.countries[list_country_id]
                                     ['name'],
                                     value=self.rating_gy1_country_date_path %
                                     (list_country_id, cur_year, 12, 31),
                                     selected='selected')
                        elif active_level == 0:
                            if day is None:
                                line('option',
                                     self.base.countries[list_country_id]
                                     ['name'],
                                     value=self.rating_all_country_path %
                                     list_country_id,
                                     selected='selected')
                            else:
                                cur_year = (date(1970, 1, 1) +
                                            timedelta(day)).year
                                line('option',
                                     self.base.countries[list_country_id]
                                     ['name'],
                                     value=self.rating_all_country_date_path %
                                     (list_country_id, cur_year, 12, 31),
                                     selected='selected')
                    else:
                        if active_level == 1:
                            if day is None:
                                line('option',
                                     self.base.countries[list_country_id]
                                     ['name'],
                                     value=self.rating_country_path %
                                     list_country_id)
                            else:
                                cur_year = (date(1970, 1, 1) +
                                            timedelta(day)).year
                                line('option',
                                     self.base.countries[list_country_id]
                                     ['name'],
                                     value=self.rating_country_date_path %
                                     (list_country_id, cur_year, 12, 31))
                        elif active_level == 2:
                            if day is None:
                                line('option',
                                     self.base.countries[list_country_id]
                                     ['name'],
                                     value=self.rating_gy1_country_path %
                                     list_country_id)
                            else:
                                cur_year = (date(1970, 1, 1) +
                                            timedelta(day)).year
                                line('option',
                                     self.base.countries[list_country_id]
                                     ['name'],
                                     value=self.rating_gy1_country_date_path %
                                     (list_country_id, cur_year, 12, 31))
                        elif active_level == 0:
                            if day is None:
                                line('option',
                                     self.base.countries[list_country_id]
                                     ['name'],
                                     value=self.rating_all_country_path %
                                     list_country_id)
                            else:
                                cur_year = (date(1970, 1, 1) +
                                            timedelta(day)).year
                                line('option',
                                     self.base.countries[list_country_id]
                                     ['name'],
                                     value=self.rating_all_country_date_path %
                                     (list_country_id, cur_year, 12, 31))
            doc.asis('&nbsp;&nbsp;&nbsp;&nbsp;<b>Active/All players: </b>')
            with tag(
                    'select',
                    onchange=
                    "this.options[this.selectedIndex].value && (window.location = this.options[this.selectedIndex].value);"
            ):
                if country_id is None:
                    if day is None:
                        if active_level == 1:
                            line('option',
                                 'Active',
                                 value=self.rating_path,
                                 selected='selected')
                            line('option', 'Gy1≥10', value=self.rating_gy1_path)
                            line('option', 'All', value=self.rating_all_path)
                        elif active_level == 2:
                            line('option', 'Active', value=self.rating_path)
                            line('option',
                                 'Gy1≥10',
                                 value=self.rating_gy1_path,
                                 selected='selected')
                            line('option', 'All', value=self.rating_all_path)
                        elif active_level == 0:
                            line('option', 'Active', value=self.rating_path)
                            line('option', 'Gy1≥10', value=self.rating_gy1_path)
                            line('option',
                                 'All',
                                 value=self.rating_all_path,
                                 selected='selected')
                    else:
                        if active_level == 1:
                            line('option',
                                 'Active',
                                 value=self.rating_date_path %
                                 (cur_year, 12, 31),
                                 selected='selected')
                            line('option',
                                 'Gy1≥10',
                                 value=self.rating_gy1_date_path %
                                 (cur_year, 12, 31))
                            line('option',
                                 'All',
                                 value=self.rating_all_date_path %
                                 (cur_year, 12, 31))
                        elif active_level == 2:
                            line('option',
                                 'Active',
                                 value=self.rating_date_path %
                                 (cur_year, 12, 31))
                            line('option',
                                 'Gy1≥10',
                                 value=self.rating_gy1_date_path %
                                 (cur_year, 12, 31),
                                 selected='selected')
                            line('option',
                                 'All',
                                 value=self.rating_all_date_path %
                                 (cur_year, 12, 31))
                        elif active_level == 0:
                            line('option',
                                 'Active',
                                 value=self.rating_date_path %
                                 (cur_year, 12, 31))
                            line('option',
                                 'Gy1≥10',
                                 value=self.rating_gy1_date_path %
                                 (cur_year, 12, 31))
                            line('option',
                                 'All',
                                 value=self.rating_all_date_path %
                                 (cur_year, 12, 31),
                                 selected='selected')
                else:
                    if day is None:
                        if active_level == 1:
                            line('option',
                                 'Active',
                                 value=self.rating_country_path % country_id,
                                 selected='selected')
                            line('option',
                                 'Gy1≥10',
                                 value=self.rating_gy1_country_path %
                                 country_id)
                            line('option',
                                 'All',
                                 value=self.rating_all_country_path %
                                 country_id)
                        elif active_level == 2:
                            line('option',
                                 'Active',
                                 value=self.rating_country_path % country_id)
                            line('option',
                                 'Gy1≥10',
                                 value=self.rating_gy1_country_path %
                                 country_id,
                                 selected='selected')
                            line('option',
                                 'All',
                                 value=self.rating_all_country_path %
                                 country_id)
                        elif active_level == 0:
                            line('option',
                                 'Active',
                                 value=self.rating_country_path % country_id)
                            line('option',
                                 'Gy1≥10',
                                 value=self.rating_gy1_country_path %
                                 country_id)
                            line('option',
                                 'All',
                                 value=self.rating_all_country_path %
                                 country_id,
                                 selected='selected')
                    else:
                        if active_level == 1:
                            line('option',
                                 'Active',
                                 value=self.rating_country_date_path %
                                 (country_id, cur_year, 12, 31),
                                 selected='selected')
                            line('option',
                                 'Gy1≥10',
                                 value=self.rating_gy1_country_date_path %
                                 (country_id, cur_year, 12, 31))
                            line('option',
                                 'All',
                                 value=self.rating_all_country_date_path %
                                 (country_id, cur_year, 12, 31))
                        elif active_level == 2:
                            line('option',
                                 'Active',
                                 value=self.rating_country_date_path %
                                 (country_id, cur_year, 12, 31))
                            line('option',
                                 'Gy1≥10',
                                 value=self.rating_gy1_country_date_path %
                                 (country_id, cur_year, 12, 31),
                                 selected='selected')
                            line('option',
                                 'All',
                                 value=self.rating_all_country_date_path %
                                 (country_id, cur_year, 12, 31))
                        elif active_level == 0:
                            line('option',
                                 'Active',
                                 value=self.rating_country_date_path %
                                 (country_id, cur_year, 12, 31))
                            line('option',
                                 'Gy1≥10',
                                 value=self.rating_gy1_country_date_path %
                                 (country_id, cur_year, 12, 31))
                            line('option',
                                 'All',
                                 value=self.rating_all_country_date_path %
                                 (country_id, cur_year, 12, 31),
                                 selected='selected')
        with tag('table'):
            with tag('tbody'):
                with tag('tr'):
                    for entry in ('Rank', 'Player', 'Rating', '±', 'Gy1', 'Gy2',
                                  'Gy5', 'Country/Region'):
                        line('th', entry)
                for player, rank, country, country_name, surname, name, native_name, rating, uncertainty, gy1, gy2, gy5, female in outputs:
                    with tag('tr'):
                        line('td', rank, klass='num')
                        with tag('td'):
                            self.flag(doc, country)
                            text(' ')
                            if not female:
                                line('a',
                                     '%s %s' % (surname, name),
                                     href=self.player_path % player,
                                     title=native_name)
                            else:
                                line('a',
                                     '%s %s' % (surname, name),
                                     href=self.player_path % player,
                                     klass='female',
                                     title=native_name)
                        line('td', '%d' % round(rating), klass='num')
                        line('td', '%d' % round(uncertainty), klass='graynum')
                        line('td', gy1, klass='num')
                        line('td', gy2, klass='num')
                        line('td', gy5, klass='num')
                        line('td', country_name)

        weight = 1.0
        if day is not None:
            weight -= 0.2
        if country_id is not None:
            weight -= 0.3
        self.gen_html(dst, title, doc.getvalue(), weight)

    def gen_ljratings(self):
        ratings = self.base.get_ratings_latest()
        gy5s = self.gy5_cache.get(None, None)
        if gy5s == None:
            gy5s = self.base.get_game_count_within_n_years_latest(5)
            self.gy5_cache[None] = gy5s

        if self.gcount_cache == None:
            gcounts = self.base.get_game_count_so_far_latest()
            self.gcount_cache = gcounts
        else:
            gcounts = self.gcount_cache

        ratings = sorted(ratings.items(), key=lambda x: x[1][0], reverse=True)
        outputs = []
        ljinfo_outputs = []
        cur_rank = 0

        ljinfo = {}
        ljinfo_name = os.path.join(self.save_path, 'data', self.ljinfo_name)
        if os.path.exists(ljinfo_name):
            with open(ljinfo_name, 'r', encoding='utf-8') as fin:
                for line in fin:
                    if line:
                        player, name, native_name, country, city, is_active, rating = line.strip(
                        ).split('\t')
                        ljinfo[player] = native_name

        ljcountry_dict = {}
        ljcountry_name = os.path.join(self.save_path, 'data',
                                      self.ljcountry_name)
        if os.path.exists(ljcountry_name):
            with open(ljcountry_name, 'r', encoding='utf-8') as fin:
                for line in fin:
                    if line:
                        country_id, country, ljcountry = line.strip(
                            '\r\n').split('\t')
                        ljcountry_dict[country_id] = ljcountry

        ljcity_dict = {}
        ljcity_name = os.path.join(self.save_path, 'data', self.ljcity_name)
        if os.path.exists(ljcity_name):
            with open(ljcity_name, 'r', encoding='utf-8') as fin:
                for line in fin:
                    if line:
                        city_id, city, ljcity = line.strip('\r\n').split('\t')
                        ljcity_dict[city_id] = ljcity

        for player, rating in ratings:
            rating, uncertainty = rating
            cur_country_id = self.base.players[player]['country']
            country_code = self.base.countries[cur_country_id]['abbr']
            country = self.base.countries[cur_country_id]['name']
            cur_city_id = self.base.players[player]['city']
            city = self.base.cities[cur_city_id]['name']
            name = self.base.players[player]['name']
            surname = self.base.players[player]['surname']
            native_name = self.base.players[player]['native_name']
            gy5 = gy5s[player]
            gcount = gcounts[player]
            is_established = (gcount >= 10)
            is_active = (gy5 > 0)
            if is_established and is_active:
                cur_rank += 1
                rank = '%d' % cur_rank
            else:
                rank = ''
            cur_ljinfo = ljinfo.get(player, None)
            if cur_ljinfo is not None:
                ljnative_name = cur_ljinfo
                if ljnative_name != '*':
                    native_name = ljnative_name
            if cur_country_id in ljcountry_dict.keys():
                country = ljcountry_dict[cur_country_id]
            if cur_city_id in ljcity_dict.keys():
                city = ljcity_dict[cur_city_id]
            if city == '?':
                city = ''
            if is_active and is_established:
                outputs.append((player, rank, country_code, country, city,
                                surname, name, native_name, rating + self.bias))
            ljinfo_outputs.append(
                (player, rank, country_code, country, city, surname, name,
                 native_name, rating + self.bias, (is_active and
                                                   is_established)))

        with open(ljinfo_name, 'w', encoding='utf-8') as fout:
            for player, rank, country_code, country, city, surname, name, native_name, rating, is_active in ljinfo_outputs:
                if not native_name:
                    native_name = '*'
                if not country:
                    country = '*'
                if not city:
                    city = '*'
                if is_active:
                    is_active = '+'
                else:
                    is_active = '-'
                fout.write(
                    f'{player}\t{surname} {name}\t{native_name}\t{country}\t{city}\t{is_active}\t{round(rating)}\n'
                )

        title = 'LJRenju Rating'
        dst = self.ljrating_path

        doc, tag, text, line = Doc().ttl()
        doc.asis('<!DOCTYPE html>')
        with tag('html', xmlns="http://www.w3.org/1999/xhtml"):
            with tag('head'):
                doc.stag('meta', charset='utf-8')
                doc.stag('meta', ('http-equiv', "content-type"),
                         ('content', "text/html; charset=utf-8"))
                doc.stag('meta',
                         name="viewport",
                         content=
                         "width=device-width, initial-scale=1, maximum-scale=1")
                doc.asis('''    <!--[if lt IE 9]>
    <script src="//html5shiv.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->''')
                doc.stag(
                    'meta',
                    name="keywords",
                    content="Renju, Renju rating, whole-history rating, WHR")
                doc.stag('meta',
                         name="description",
                         content="Whole-history rating of Renju players")
                doc.stag('meta', name="author", content="Tianyi Hao")
                doc.stag('meta',
                         name="copyright",
                         content="%d Renju Rating" % self.base.date.year)
                line('title', '%s - Renju Rating' % title)
                with tag('script'):
                    doc.asis('''
        if (window.location.protocol != "file:") {
            var _hmt = _hmt || [];
            (function() {
            var hm = document.createElement("script");
            hm.src = "https://hm.baidu.com/hm.js?cb525b0b0c34b96320b743cdf90a90c3";
            var s = document.getElementsByTagName("script")[0];
            s.parentNode.insertBefore(hm, s);
            })();
        }
    ''')
                with tag('script'):
                    doc.asis('''
        if (window.location.protocol != "file:") {
            (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
            (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
            m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
            })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
            ga('create', 'UA-119927498-1', 'auto');
            ga('send', 'pageview');
        }
    ''')
                doc.stag('link',
                         href="css/ljrenju.css",
                         rel="stylesheet",
                         type="text/css")
            with tag('body'):
                with tag('div', align='center'):
                    doc.asis(
                        f'<p><b>最近更新：</b> { self.base.date.strftime("%Y-%m-%d") }</p>'
                    )

                    with tag('table', align='center', klass='tabRat2'):
                        with tag('tr'):
                            for entry in ('序号', '编号', '姓名', '国家(地区)', '城市',
                                          '等级分'):
                                line('th', entry)
                        for player, rank, country_code, country, city, surname, name, native_name, rating in outputs:
                            with tag('tr'):
                                if rank == '1':
                                    line('th',
                                         rank,
                                         align='center',
                                         klass='mdlGod')
                                elif rank in [str(i) for i in range(2, 4)]:
                                    line('th', rank, align='center')
                                elif rank in [str(i) for i in range(4, 11)]:
                                    line('th',
                                         rank,
                                         align='center',
                                         bgcolor='#CCFFCC')
                                elif rank in [str(i) for i in range(11, 21)]:
                                    line('td',
                                         rank,
                                         align='center',
                                         bgcolor='#CCFFCC')
                                else:
                                    line('td', rank, align='center')
                                if country_code == 'CHN':
                                    klass = 'bgChn'
                                elif country_code == 'TPE':
                                    klass = 'bgTpe'
                                elif country_code == 'HKG':
                                    klass = 'bgHok'
                                elif country_code == 'MAC':
                                    klass = 'bgMac'
                                else:
                                    klass = None
                                if not klass:
                                    line('td', player, align='center')
                                    if native_name:
                                        line(
                                            'td', '%s %s (%s)' %
                                            (surname, name, native_name))
                                    else:
                                        line('td', '%s %s' % (surname, name))
                                    line('td', country)
                                    line('td', city)
                                    line('td',
                                         '%d' % round(rating),
                                         align='center')
                                else:
                                    line('td',
                                         player,
                                         align='center',
                                         klass=klass)
                                    if native_name:
                                        line('td',
                                             '%s %s (%s)' %
                                             (surname, name, native_name),
                                             klass=klass)
                                    else:
                                        line('td',
                                             '%s %s' % (surname, name),
                                             klass=klass)
                                    line('td', country, klass=klass)
                                    line('td', city, klass=klass)
                                    line('td',
                                         '%d' % round(rating),
                                         align='center',
                                         klass=klass)

        fout = open(os.path.join(self.save_path, 'html', dst),
                    'w',
                    encoding='utf-8')
        fout.write(indent(doc.getvalue()))
        fout.close()

    def gen_players(self):
        players = sorted(self.base.players.items(),
                         key=lambda x: self.base.round_to_key(x[0]))
        ratings = self.base.ratings
        histories = self.base.get_history_for_players()
        outputs = []
        for player_id, player in players:
            if not player_id in ratings.keys():
                continue
            surname = player['surname']
            name = player['name']
            native_name = player['native_name']
            female = player['female']
            country = self.base.countries[player['country']]['abbr']
            country_name = self.base.countries[player['country']]['name']
            city = self.base.cities[player['city']]['name']
            rating = ratings[player_id][-1][1] + self.bias
            history = histories[player_id]
            gcount = 0
            for tournament_id, games in history:
                gcount += len(games)
            outputs.append([
                player_id, surname, name, native_name, country, country_name,
                rating, gcount, city, female
            ])
        doc, tag, text, line = Doc().ttl()
        with tag('table'):
            with tag('tbody'):
                with tag('tr'):
                    line('th', 'ID')
                    line('th', 'Player')
                    line('th', 'Rating')
                    line('th', 'Games')
                    line('th', 'Place')
                for player_id, surname, name, native_name, country, country_name, rating, gcount, city, female in outputs:
                    with tag('tr'):
                        line('td', player_id, klass='num')
                        with tag('td'):
                            self.flag(doc, country)
                            text(' ')
                            if not female:
                                line('a',
                                     '%s %s' % (surname, name),
                                     href=self.player_path % player_id,
                                     title=native_name)
                            else:
                                line('a',
                                     '%s %s' % (surname, name),
                                     href=self.player_path % player_id,
                                     klass='female',
                                     title=native_name)
                        line('td', '%d' % round(rating), klass='num')
                        line('td', '%d' % gcount, klass='num')
                        line('td', city + ', ' + country_name)
        title = 'List of Players'
        dst = self.players_path

        weight = 0.9
        self.gen_html(dst, title, doc.getvalue(), weight)

    def gen_players_json(self):
        ratings = self.base.get_ratings_latest()
        gy5s = self.gy5_cache.get(None, None)
        if gy5s == None:
            gy5s = self.base.get_game_count_within_n_years_latest(5)
            self.gy5_cache[None] = gy5s

        if self.gcount_cache == None:
            gcounts = self.base.get_game_count_so_far_latest()
            self.gcount_cache = gcounts
        else:
            gcounts = self.gcount_cache

        ratings = sorted(ratings.items(), key=lambda x: x[1][0], reverse=True)
        outputs = []
        cur_rank = 0

        for player, rating in ratings:
            rating, uncertainty = rating
            gy5 = gy5s[player]
            gcount = gcounts[player]
            is_established = (gcount >= 10)
            is_active = (gy5 > 0)
            if is_established and is_active:
                cur_rank += 1
                rank = cur_rank
            else:
                rank = 0

            outputs.append(
                [int(player), rank, rating + self.bias,
                 int(is_established)])
        outputs.sort(key=lambda x: int(x[0]))

        dst = self.players_json_path
        with open(os.path.join(self.save_path, 'html', dst),
                  'w',
                  encoding='utf-8') as fout:
            json.dump(outputs, fout)

    def gen_player(self):
        ratings = self.base.ratings
        historys = self.base.get_history_for_players()
        gy1s = self.base.get_game_count_within_n_years_latest(1)
        gy2s = self.base.get_game_count_within_n_years_latest(2)
        gy5s = self.base.get_game_count_within_n_years_latest(5)
        for player_id, ratings_player in ratings.items():
            player = self.base.players[player_id]
            surname = player['surname']
            name = player['name']
            native_name = player['native_name']
            country = self.base.countries[player['country']]['name']
            country_abbr = self.base.countries[player['country']]['abbr']
            city = self.base.cities[player['city']]['name']
            cur_rating = ratings_player[-1][1] + self.bias
            cur_rank = self.rank.get(player_id, '-')
            first_game = date(1970, 1, 1) + timedelta(ratings[player_id][0][0])
            last_game = date(1970, 1, 1) + timedelta(ratings[player_id][-1][0])
            top_rating_date, top_rating, _ = max(ratings_player,
                                                 key=lambda x: x[1])
            top_rating_date = date(1970, 1, 1) + timedelta(top_rating_date)
            top_rating += self.bias
            win = 0
            draw = 0
            loss = 0
            gy1 = gy1s[player_id]
            gy2 = gy2s[player_id]
            gy5 = gy5s[player_id]
            history = historys[player_id]
            rating = ratings[player_id]
            rating_chart = ''.join(
                map(
                    lambda r: '{x: %d, y: %f}, ' %
                    (r[0] * 86400000, r[1] + self.bias), rating))
            tournament_outputs = []
            for tournament_id, games in reversed(history):
                tournament = self.base.tournaments[tournament_id]
                tournament_name = tournament['name']
                tournament_end = tournament['end']
                tournament_end_day = self.base.date_to_day(tournament_end)
                rating_in_tournament = next(
                    filter(lambda x: x[0] == tournament_end_day,
                           rating))[1] + self.bias
                game_outputs = []
                for game_id in games:
                    game = self.base.games[game_id]
                    black = game['black']
                    white = game['white']
                    result = game['result']
                    round_ = game['round']
                    if player_id == black:
                        color = 'Black'
                        if result == 'B':
                            result = 1
                            win += 1
                        elif result == 'W':
                            result = 0
                            loss += 1
                        else:
                            result = 0.5
                            draw += 1
                        opponent_id = white
                    else:
                        color = 'White'
                        if result == 'W':
                            result = 1
                            win += 1
                        elif result == 'B':
                            result = 0
                            loss += 1
                        else:
                            result = 0.5
                            draw += 1
                        opponent_id = black
                    opponent = self.base.players[opponent_id]
                    opponent_surname = opponent['surname']
                    opponent_name = opponent['name']
                    opponent_native_name = opponent['native_name']
                    opponent_female = opponent['female']
                    opponent_country = self.base.countries[
                        opponent['country']]['abbr']
                    opponent_rating = next(
                        filter(lambda x: x[0] == tournament_end_day,
                               ratings[opponent_id]))[1] + self.bias
                    if game_id.startswith('G'):
                        output_game_id = None
                    else:
                        output_game_id = game_id
                    game_outputs.append([
                        round_, color, opponent_id, opponent_surname,
                        opponent_name, opponent_native_name, opponent_country,
                        opponent_rating, opponent_female, result, output_game_id
                    ])
                tournament_outputs.append([
                    tournament_id, tournament_name, tournament_end,
                    rating_in_tournament, game_outputs
                ])
            doc, tag, text, line = Doc().ttl()
            doc.asis(
                '<link href="css/nv.d3.css" rel="stylesheet" type="text/css">')
            with tag('h1'):
                self.flag(doc, country_abbr, klass='flag_large')
                if not native_name:
                    doc.text(' %s %s' % (surname, name))
                else:
                    doc.text(' %s %s (%s)' % (surname, name, native_name))
            with tag('p'):
                doc.asis('<b>Place:</b> %s, %s' % (city, country))
            with tag('p'):
                doc.asis('<b>Rating:</b> %.2f, <b>Rank:</b> %s' %
                         (round(cur_rating, 2), cur_rank))
            with tag('p'):
                doc.asis(
                    '<b>First game:</b> %04d-%02d-%02d, <b>Last game:</b> %04d-%02d-%02d'
                    % (first_game.year, first_game.month, first_game.day,
                       last_game.year, last_game.month, last_game.day))
            with tag('p'):
                doc.asis('<b>Top rating:</b> %.2f (%04d-%02d-%02d)' %
                         (round(top_rating, 2), top_rating_date.year,
                          top_rating_date.month, top_rating_date.day))
            with tag('p'):
                doc.asis(
                    '<b>Games:</b> %d, <b>Wins:</b> %d, <b>Draws:</b> %d, <b>Losses:</b> %d'
                    % (win + draw + loss, win, draw, loss))
            with tag('p'):
                doc.asis('<b>Gy1:</b> %d, <b>Gy2:</b> %d, <b>Gy5:</b> %d' %
                         (gy1, gy2, gy5))
            doc.asis('''<div id="chart1"></div>''')

            with tag('table'):
                with tag('tbody'):
                    for tournament_id, tournament_name, tournament_end, rating_in_tournament, game_outputs in tournament_outputs:
                        with tag('tr'):
                            with tag('th', colspan='5'):
                                line('a',
                                     tournament_name,
                                     href=self.tournament_path % tournament_id)
                        with tag('tr'):
                            line('th', 'Date', klass='second')
                            line('td', tournament_end, colspan='2', klass='num')
                            line('th', 'Rating', klass='second')
                            line('td',
                                 '%.2f' % round(rating_in_tournament, 2),
                                 klass='num')
                        with tag('tr'):
                            line('th', 'Round')
                            line('th', 'Color')
                            line('th', 'Result')
                            line('th', 'Opponent', colspan='2')
                        for round_, color, opponent_id, opponent_surname, opponent_name, opponent_native_name, opponent_country, opponent_rating, opponent_female, result, output_game_id in game_outputs:
                            with tag('tr'):
                                line('td', round_, klass='num')
                                line('td', color)
                                if output_game_id is None:
                                    if result == 1:
                                        line('td', 'Win', klass='win')
                                    elif result == 0:
                                        line('td', 'Loss', klass='loss')
                                    else:
                                        line('td', 'Draw', klass='draw')
                                else:
                                    if result == 1:
                                        with tag('td', klass='win'):
                                            line('a',
                                                 'Win',
                                                 href=self.game_path %
                                                 output_game_id)
                                    elif result == 0:
                                        with tag('td', klass='loss'):
                                            line('a',
                                                 'Loss',
                                                 href=self.game_path %
                                                 output_game_id)
                                    else:
                                        with tag('td', klass='draw'):
                                            line('a',
                                                 'Draw',
                                                 href=self.game_path %
                                                 output_game_id)
                                with tag('td'):
                                    self.flag(doc, opponent_country)
                                    text(' ')
                                    if not opponent_female:
                                        line('a',
                                             '%s %s' %
                                             (opponent_surname, opponent_name),
                                             href=self.player_path %
                                             opponent_id,
                                             title=opponent_native_name)
                                    else:
                                        line('a',
                                             '%s %s' %
                                             (opponent_surname, opponent_name),
                                             href=self.player_path %
                                             opponent_id,
                                             klass='female',
                                             title=opponent_native_name)
                                line('td',
                                     '%.2f' % round(opponent_rating, 2),
                                     klass='num')

            doc.asis('''<script src="js/d3.min.js" charset="utf-8"></script>
<script src="js/nv.d3.js"></script>            
<script>
    var chart;
    var data;

    nv.addGraph(function() {
        data = Data();
        var y_min = 1.e+9, y_max = -1.e+9;
        for(var i = 0; i < data[0].values.length; i ++) {
            var cur_y = data[0].values[i].y;
            y_min = Math.min(y_min, cur_y);
            y_max = Math.max(y_max, cur_y);
        }
        var y_d = 200. - (y_max - y_min);
        if(y_d > 0.) {
            y_max += y_d / 2.
            y_min -= y_d / 2.
        }

        chart = nv.models.lineChart()
            .options({
                duration: 300,
                useInteractiveGuideline: true
            })
        ;

        chart.xAxis
            .axisLabel("Date")
            .tickFormat(function(d) {
          return d3.time.format('%%Y-%%m-%%d')(new Date(d))
		});

		chart.xScale(d3.time.scale());

        chart.yAxis
            .axisLabel('Rating')
            .tickFormat(d3.format(',.2f'))
        ;

        chart.forceY([y_min, y_max]);
		
		chart.showYAxis(true).showXAxis(true).showLegend(false).margin({top:20, left: 100, right:100});

        d3.select('#chart1').append('svg')
            .datum(data)
            .call(chart);

        nv.utils.windowResize(chart.update);

        return chart;
    });

    function Data() {
        var rating = [%s];
            ;

        return [
            {
                values: rating,
                color: "#ff7f0e",
            }
        ];
    }

</script>''' % rating_chart)

            title = '%s %s, %s' % (surname, name, country)
            dst = self.player_path % player_id

            weight = 0.3
            self.gen_html(dst, title, doc.getvalue(), weight)

    def gen_tournaments(self):
        tournaments = sorted(
            self.base.tournaments.items(),
            key=lambda x:
            (x[1]['end'], x[1]['start'], self.base.round_to_key(x[0])),
            reverse=True)
        games_for_tournaments = self.base.get_games_for_tournaments()
        outputs = []
        for tournament_id, tournament in tournaments:
            if not tournament_id in games_for_tournaments.keys():
                continue
            name = tournament['name']
            country = self.base.countries[tournament['country']]['abbr']
            country_name = self.base.countries[tournament['country']]['name']
            city = self.base.cities[tournament['city']]['name']
            ngames = len(games_for_tournaments[tournament_id])
            start = tournament['start']
            end = tournament['end']
            outputs.append([
                tournament_id, name, country, country_name, city, ngames, start,
                end
            ])
        doc, tag, text, line = Doc().ttl()
        with tag('table'):
            with tag('tbody'):
                with tag('tr'):
                    line('th', 'Place')
                    line('th', 'Tournament')
                    line('th', 'Games')
                    line('th', 'Start')
                    line('th', 'End')
                for tournament_id, name, country, country_name, city, ngames, start, end in outputs:
                    with tag('tr'):
                        with tag('td'):
                            self.flag(doc, country)
                            text(' %s, %s' % (city, country_name))
                        with tag('td'):
                            line('a',
                                 name,
                                 href=self.tournament_path % tournament_id)
                        line('td', '%d' % ngames, klass='num')
                        line('td', start, klass='num')
                        line('td', end, klass='num')
        title = 'List of Tournaments'
        dst = self.tournaments_path

        weight = 0.9
        self.gen_html(dst, title, doc.getvalue(), weight)

    def gen_tournament(self):
        games_for_tournaments = self.base.get_games_for_tournaments()
        for tournament_id, tournament in self.base.tournaments.items():
            if not tournament_id in games_for_tournaments.keys():
                continue
            name = tournament['name']
            country = self.base.countries[tournament['country']]['name']
            city = self.base.cities[tournament['city']]['name']
            start = tournament['start']
            end = tournament['end']
            end_day = self.base.date_to_day(end)
            rule = self.base.rules[tournament['rule']]['name']
            ngames = len(games_for_tournaments[tournament_id])
            round_outputs = {}
            for game_id in games_for_tournaments[tournament_id]:
                game = self.base.games[game_id]
                round_ = game['round']
                black = game['black']
                white = game['white']
                result = game['result']
                if result == 'B':
                    result = '1 : 0'
                elif result == 'W':
                    result = '0 : 1'
                else:
                    result = '0.5 : 0.5'
                black_player = self.base.players[black]
                black_surname = black_player['surname']
                black_name = black_player['name']
                black_native_name = black_player['native_name']
                black_female = black_player['female']
                black_country = self.base.countries[
                    black_player['country']]['abbr']
                black_rating = next(
                    filter(lambda x: x[0] == end_day,
                           self.base.ratings[black]))[1] + self.bias
                white_player = self.base.players[white]
                white_surname = white_player['surname']
                white_name = white_player['name']
                white_native_name = white_player['native_name']
                white_female = white_player['female']
                white_country = self.base.countries[
                    white_player['country']]['abbr']
                white_rating = next(
                    filter(lambda x: x[0] == end_day,
                           self.base.ratings[white]))[1] + self.bias
                round_outputs.setdefault(round_, [])
                if game_id.startswith('G'):
                    output_game_id = None
                else:
                    output_game_id = game_id
                round_outputs[round_].append([
                    black, black_surname, black_name, black_native_name,
                    black_country, black_rating, black_female, white,
                    white_surname, white_name, white_native_name, white_country,
                    white_rating, white_female, result, output_game_id
                ])
            round_outputs = sorted(round_outputs.items(),
                                   key=lambda x: self.base.round_to_key(x[0]))
            for round_, game_outputs in round_outputs:
                game_outputs.sort(key=lambda g:
                                  (max(g[5], g[12]), min(g[5], g[12])),
                                  reverse=True)
            doc, tag, text, line = Doc().ttl()
            line('h1', name)
            with tag('p'):
                doc.asis('<b>Place:</b> %s, %s' % (city, country))
            with tag('p'):
                doc.asis('<b>Start:</b> %s, <b>End:</b> %s' % (start, end))
            with tag('p'):
                doc.asis('<b>Rule:</b> %s, <b>Games:</b> %d' % (rule, ngames))
            with tag('table'):
                with tag('tbody'):
                    for round_, game_outputs in round_outputs:
                        with tag('tr'):
                            line('th', 'Round %s' % round_, colspan='5')
                        with tag('tr'):
                            line('th', 'Black', colspan='2', klass='second')
                            line('th', 'Result', klass='second')
                            line('th', 'White', colspan='2', klass='second')
                        for black, black_surname, black_name, black_native_name, black_country, black_rating, black_female, white, white_surname, white_name, white_native_name, white_country, white_rating, white_female, result, output_game_id in game_outputs:
                            with tag('tr'):
                                with tag('td'):
                                    self.flag(doc, black_country)
                                    text(' ')
                                    if not black_female:
                                        line('a',
                                             '%s %s' %
                                             (black_surname, black_name),
                                             href=self.player_path % black,
                                             title=black_native_name)
                                    else:
                                        line('a',
                                             '%s %s' %
                                             (black_surname, black_name),
                                             href=self.player_path % black,
                                             klass='female',
                                             title=black_native_name)
                                line('td',
                                     '%.2f' % round(black_rating, 2),
                                     klass='num')
                                if output_game_id is None:
                                    line('td', result, klass='cnum')
                                else:
                                    with tag('td', klass='cnum'):
                                        line('a',
                                             result,
                                             href=self.game_path %
                                             output_game_id)
                                line('td',
                                     '%.2f' % round(white_rating, 2),
                                     klass='num')
                                with tag('td', klass='right'):
                                    if not white_female:
                                        line('a',
                                             '%s %s' %
                                             (white_surname, white_name),
                                             href=self.player_path % white,
                                             title=white_native_name)
                                    else:
                                        line('a',
                                             '%s %s' %
                                             (white_surname, white_name),
                                             href=self.player_path % white,
                                             klass='female',
                                             title=white_native_name)
                                    text(' ')
                                    self.flag(doc, white_country)
            title = name
            dst = self.tournament_path % tournament_id

            weight = 0.4
            self.gen_html(dst, title, doc.getvalue(), weight)

    def gen_top_ratings(self, female=False):
        if not female:
            top_players = sorted(self.top_players.keys(),
                                 key=lambda p: self.top_players[p],
                                 reverse=True)
        else:
            top_players = sorted(self.top_players_women.keys(),
                                 key=lambda p: self.top_players_women[p],
                                 reverse=True)
        charts = []
        players = []
        colors = [
            'FF4500', '0000FF', '006400', 'DA70D6', '7CFC00', '00BFFF',
            '800000', '9400D3', '008080', 'FF1493', '00008B', '708090',
            'FF00FF', '7FFFD4', 'FA8072', 'B8860B', '4169E1', 'FFD700',
            'DC143C', '2F4F4F', 'BDB76B', '00FF7F', '32CD32', '8B008B',
            '8B4513', '9370DB', 'FF0000', 'FF8C00', '483D8B', '20B2AA',
            '00FFFF', '00FF00', '228B22', '4B0082', 'CD5C5C', 'C71585',
            '6495ED', '808000', '66CDAA', '556B2F', '1E90FF', 'FF6347',
            '4682B4', '9ACD32', 'B22222', 'FF69B4', '9932CC', 'CD853F',
            '2E8B57', '0000CD', 'DB7093', '6A5ACD', '3CB371', 'DAA520',
            '191970', 'D2691E', '6B8E23', 'BA55D3', 'F4A460', '40E0D0',
            '5F9EA0', 'A0522D', 'ADFF2F', '00CED1', '7B68EE', 'FF7F50',
            '008000', 'E9967A', '8A2BE2', 'FFA500', 'FFA07A', 'A52A2A',
            'F08080', '48D1CC', '008B8B', '800080', '00FA9A', '778899',
            '8B0000', '000080', '7FFF00'
        ]
        player_count = 0
        for player in top_players:
            rating = self.base.ratings[player]
            if not female:
                start_year = 1989
            else:
                start_year = 1997
            str_chart = ''.join(
                map(
                    lambda r: '{x: %d, y: %f}, ' %
                    (r[0] * 86400000, r[1] + self.bias),
                    filter(
                        lambda r: r[0] >= int(
                            datetime(start_year, 1, 1, tzinfo=timezone.utc).
                            timestamp()) // 86400, rating)))
            str_chart = 'var rating_%s = [%s];' % (player, str_chart)
            charts.append(str_chart)
            player_surname = self.base.players[player]['surname']
            player_name = self.base.players[player]['name']
            str_player = '{ values: rating_%s, key: "%s %s", color: "#%s", },' % (
                player, player_surname, player_name, colors[player_count])
            players.append(str_player)
            player_count += 1
        if not female:
            topN = sorted(self.topN.items(), key=lambda x: x[0])
        else:
            topN = sorted(self.topN_women.items(), key=lambda x: x[0])
        outputs = []
        for date_, player_ids in topN:
            date_outputs = []
            for player_id in player_ids:
                player = self.base.players[player_id]
                surname = player['surname']
                name = player['name']
                native_name = player['native_name']
                female = player['female']
                country = self.base.countries[player['country']]['abbr']
                date_outputs.append(
                    [player_id, country, surname, name, native_name, female])
            outputs.append([date_, date_outputs])
        doc, tag, text, line = Doc().ttl()
        doc.asis('<link href="css/nv.d3.css" rel="stylesheet" type="text/css">')
        if not female:
            line('h1', 'History Ratings of Top Renju Players')
        else:
            line('h1', 'History Ratings of Top Women Renju Players')
        doc.asis('''<div id="chart1"></div>''')

        with tag('table'):
            with tag('tbody'):
                with tag('tr'):
                    line('th', 'Year')
                    line('th', '1st')
                    line('th', '2nd')
                    line('th', '3rd')
                    line('th', '4th')
                    line('th', '5th')
                for date_, date_outputs in outputs:
                    with tag('tr'):
                        line('td', date_, klass='num')
                        for player_id, country, surname, name, native_name, female in date_outputs:
                            with tag('td'):
                                self.flag(doc, country)
                                text(' ')
                                if not female:
                                    line('a',
                                         '%s %s' % (surname, name),
                                         href=self.player_path % player_id,
                                         title=native_name)
                                else:
                                    line('a',
                                         '%s %s' % (surname, name),
                                         href=self.player_path % player_id,
                                         klass='female',
                                         title=native_name)
        with tag('p'):
            doc.asis(
                '<b>Note:</b> This table only contains players with <b>Gy1</b>&gt;0.'
            )

        doc.asis('''<script src="js/d3.min.js" charset="utf-8"></script>
<script src="js/nv.d3.js"></script>
<script>
    var chart;
    var data;

    nv.addGraph(function() {
        data = Data();

        chart = nv.models.lineChart()
            .options({
                duration: 300,
                useInteractiveGuideline: true
            })
        ;

        chart.xAxis
            .axisLabel("Date")
            .tickFormat(function(d) {
          return d3.time.format('%%Y-%%m-%%d')(new Date(d))
		});

		chart.xScale(d3.time.scale());

        chart.yAxis
            .axisLabel('Rating')
            .tickFormat(d3.format(',.2f'))
        ;
		
		chart.showYAxis(true).showXAxis(true).showLegend(true).margin({top:20, left: 100, right:100});

        d3.select('#chart1').append('svg')
            .datum(data)
            .call(chart);

        nv.utils.windowResize(chart.update);

        return chart;
    });

    function Data() {
        %s

        return [
            %s
        ];
    }

</script>''' % ('\n        '.join(charts), '\n            '.join(players)))

        if not female:
            title = 'History Ratings of Top Renju Players'
            dst = self.top_rating_path
        else:
            title = 'History Ratings of Top Women Renju Players'
            dst = self.top_rating_women_path

        weight = 0.9
        self.gen_html(dst, title, doc.getvalue(), weight)

    def gen_html(self, dst, title, content, weight, head_script=None):
        doc, tag, text, line = Doc().ttl()
        doc.asis('<!DOCTYPE html>')
        with tag('html', xmlns="http://www.w3.org/1999/xhtml"):
            with tag('head'):
                doc.stag('meta', charset='utf-8')
                doc.stag('meta', ('http-equiv', "content-type"),
                         ('content', "text/html; charset=utf-8"))
                doc.stag('meta',
                         name="viewport",
                         content=
                         "width=device-width, initial-scale=1, maximum-scale=1")
                doc.asis('''    <!--[if lt IE 9]>
    <script src="//html5shiv.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->''')
                doc.stag(
                    'meta',
                    name="keywords",
                    content="Renju, Renju rating, whole-history rating, WHR")
                doc.stag('meta',
                         name="description",
                         content="Whole-history rating of Renju players")
                doc.stag('meta', name="author", content="Tianyi Hao")
                doc.stag('meta',
                         name="copyright",
                         content="%d Renju Rating" % self.base.date.year)
                line('title', '%s - Renju Rating' % title)
                if head_script:
                    doc.asis(head_script)
                with tag('script'):
                    doc.asis('''
        if (window.location.protocol != "file:") {
            var _hmt = _hmt || [];
            (function() {
            var hm = document.createElement("script");
            hm.src = "https://hm.baidu.com/hm.js?cb525b0b0c34b96320b743cdf90a90c3";
            var s = document.getElementsByTagName("script")[0]; 
            s.parentNode.insertBefore(hm, s);
            })();
        }
    ''')
                with tag('script'):
                    doc.asis('''
        if (window.location.protocol != "file:") {
            (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
            (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
            m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
            })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
            ga('create', 'UA-119927498-1', 'auto');
            ga('send', 'pageview');
        }
    ''')
                doc.stag('link',
                         href="css/default.css",
                         rel="stylesheet",
                         type="text/css")
            with tag('body'):
                with tag('div', id='outer'):
                    line('div', '', id="header")
                    with tag('div', id='menu'):
                        with tag('ul'):
                            for page_title, page_href, is_first in [
                                ('Home page', self.rating_path, True),
                                ('Players', self.players_path, False),
                                ('Tournaments', self.tournaments_path, False),
                                ('History of Top players', self.top_rating_path,
                                 False),
                                ('History of Top Women',
                                 self.top_rating_women_path, False),
                                ('Gomoku', self.gomoku_path, False)
                            ]:
                                if is_first:
                                    with tag('li', klass="first"):
                                        line('a', page_title, href=page_href)
                                else:
                                    with tag('li'):
                                        line('a', page_title, href=page_href)
                    with tag('div', id='content'):
                        with tag('div', id='primaryContentContainer'):
                            with tag('div', id='primaryContent'):
                                doc.asis(content)
                        doc.stag('div', klass='clear')
                    with tag('div', id='footer'):
                        with tag('p'):
                            doc.asis(
                                'Theme based on <a href="http://templated.co/genericblue">GenericBlue</a> designed by <a href="http://templated.co" rel="nofollow">TEMPLATED</a>.'
                            )

        fout = open(os.path.join(self.save_path, 'html', dst),
                    'w',
                    encoding='utf-8')
        fout.write(indent(doc.getvalue()))
        fout.close()
        self.pages.append((dst, weight))

    def gen_sitemap(self, prefix):
        pages = sorted(self.pages, key=lambda p: (-p[1], p[0]))
        timestr = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
        dom = minidom.Document()
        root = dom.createElement('urlset')
        dom.appendChild(root)
        root.setAttribute("xmlns",
                          "http://www.sitemaps.org/schemas/sitemap/0.9")
        for dst, weight in pages:
            url = dom.createElement('url')
            root.appendChild(url)
            loc = dom.createElement('loc')
            url.appendChild(loc)
            loc_text = dom.createTextNode(prefix + dst)
            loc.appendChild(loc_text)
            lastmod = dom.createElement('lastmod')
            url.appendChild(lastmod)
            lastmod_text = dom.createTextNode(timestr)
            lastmod.appendChild(lastmod_text)
            changefreq = dom.createElement('changefreq')
            url.appendChild(changefreq)
            changefreq_text = dom.createTextNode('daily')
            changefreq.appendChild(changefreq_text)
            priority = dom.createElement('priority')
            url.appendChild(priority)
            priority_text = dom.createTextNode('%.1f' % weight)
            priority.appendChild(priority_text)
        xml_str = dom.toprettyxml(indent="\t", encoding='utf-8')
        fout = open(os.path.join(self.save_path, 'html', self.sitemap_path),
                    'w',
                    encoding='utf-8')
        fout.write(xml_str.decode('utf-8'))
        fout.close()
