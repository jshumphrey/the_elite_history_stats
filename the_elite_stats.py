#! /usr/bin/env python
'''This scrapes every PR History page on the-elite.net, and concatenates all PR times into one table.'''

import csv, itertools, json, re, requests, time, tqdm, yaml
import pdb # pylint: disable = unused-import
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime

LAST_CALL = None
CALL_INTERVAL = 1 # Minimum time between requests (seconds)


def request_soup(session, url):
    '''Wraps the process of getting soup from a URL.'''
    soup = None
    while not soup:
        try:
            bucket_sleep()
            soup = BeautifulSoup(session.get(url).content, features = "lxml")
        except (ConnectionError, TimeoutError) as _:
            pass

    return soup


def bucket_sleep():
    '''Rate-limits requests, according to CALL_INTERVAL.'''
    global LAST_CALL
    current_time = time.time()
    if LAST_CALL:
        time.sleep(max(CALL_INTERVAL - (current_time - LAST_CALL), 0))
    LAST_CALL = current_time


class Player:
    def __init__(self, real_name, alias, hex_code, game):
        self.real_name = real_name
        self.alias = alias
        self.hex_code = hex_code
        self.game = game

        self.times = []
        self.player_url = "https://rankings.the-elite.net/~" + alias.replace(" ", "+")
        self.points = 0

    def __str__(self):
        return self.real_name + " / " + self.alias

    def __repr__(self):
        return "Player: real_name = {!r}, alias = {!r}, hex_code = {!r}, game = {!s}, points = {!r}".format(
            self.real_name, self.alias, self.hex_code, self.game, self.points
        )

    def recalculate_points(self):
        self.points = sum([time.points for time in self.times])

    def load_times(self, session):
        '''This loads the Player's times with all of their PR times.'''
        soup = request_soup(session, self.player_url + self.game.times_url_suffix)
        try:
            rows = [[cell.text.replace("\n", "") for cell in row.find_all("td")] for row in soup.find("table").find_all("tr")[1:]]
        except AttributeError:
            pass

        self.times.extend([Time(
            self,
            self.game.find_stage(row[1], row[2]),
            te_date_to_iso(row[0]),
            row[4],
            row[3]
        ) for row in rows if row[0] != "Unknown" and row[3] != "N/A"])


class Game:
    def __init__(self, name, times_url_suffix, players_url, levels, difficulties):
        self.name = name
        self.times_url_suffix = times_url_suffix
        self.players_url = players_url
        self.stages = {Stage(level, difficulty, self) for level, difficulty in itertools.product(levels, difficulties)}

        self.players = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Game: name = {!r}, times_url_suffix = {!r}, players_url = {!r}, stages = {!s}, players = {!s}".format(
            self.name, self.times_url_suffix, self.players_url, self.stages, self.players
        )

    def load_players(self, session):
        '''This creates the set of Players by visiting the All Players page and parsing the table.'''
        players_soup = request_soup(session, self.players_url)
        
        css_url = "https://rankings.the-elite.net" + players_soup.find(href = re.compile("\/css\/users.*css")).get("href")
        css_soup = request_soup(session, css_url)
        css_entries = re.split(r",?a\.", css_soup.get_text())
        
        css_dict = {}
        for entry in [entry for entry in css_entries if entry]:
            entry_match = re.fullmatch(r"(u\d+)\{color:(\#[\da-fA-F]+)\}", entry)
            if not entry_match:
                css_dict[entry] = "#000000"
            else:
                css_dict[entry_match[1]] = entry_match[2]
            
        rows = [row.find_all("td") for row in players_soup.find("table").find_all("tr")[1:]]
        self.players.extend([Player(
            row[1].text.replace("\n", ""), 
            row[0].text.replace("\n", ""),
            css_dict[row[0].find("a").get("class")[1]],
            self
        ) for row in rows])

    def find_stage(self, level_name, difficulty_name):
        '''This returns the Stage for this game with the provided level and difficulty names.'''
        try:
            return [stage for stage in self.stages if stage.level.name == level_name and stage.difficulty.name == difficulty_name][0]
        except IndexError:
            raise LookupError("Stage " + level_name + " " + difficulty_name + " not found!")

    def write_times(self):
        '''This writes all the times out to a CSV.'''
        with open("times.csv", "w") as outfile:
            writer = csv.writer(outfile, delimiter = ",", quotechar = '"')
            writer.writerow(["Player Name", "Player Alias", "Hex Code", "Date", "Game", "Level", "Difficulty", "Time", "System"])
            for t in sorted(itertools.chain([player.times for player in self.players]), key = lambda t: t.date):
                writer.writerow([
                    t.player.real_name,
                    t.player.alias,
                    t.player.hex_code,
                    t.date,
                    t.stage.game,
                    t.stage.level_name,
                    t.stage.difficulty,
                    t.time,
                    t.system
                ])


class Stage:
    def __init__(self, level_dict, difficulty_dict, game):
        self.level = Level(level_dict["name"], level_dict["abbreviation"])
        self.difficulty = Difficulty(difficulty_dict["name"])
        self.game = game

        self.times = set()

    def __str__(self):
        return self.level.name + " " + self.difficulty.name

    def __repr__(self):
        return self.level.name + " " + self.difficulty.name


class Level:
    def __init__(self, level_name, abbreviation):
        self.name = level_name
        self.abbreviation = abbreviation

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class Difficulty:
    def __init__(self, difficulty_name):
        self.name = difficulty_name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class Time:
    def __init__(self, player, stage, date, system, time_string):
        self.player = player
        self.stage = stage
        self.date = date
        self.system = system
        self.time = time_string

        #self.player.times[self.stage.game].add(self)
        #self.stage.times.add(self)
        self.points = 0

    def __str__(self):
        return str(self.stage) + " " + self.time

    def __repr__(self):
        return "Time: player = {!s}, stage = {!s}, date = {!s}, system = {!r}, time = {!r}".format(
            self.player, self.stage, self.date, self.system, self.time
        )

    def calculate_points(self):
        pass


def te_date_to_iso(te_date):
    '''Converts the date format used on times pages to YYYY-MM-DD.'''
    return datetime.strptime(te_date, "%d %b %Y").strftime("%Y-%m-%d")


def get_hex_code(soup):
    '''This extracts the hex code from a player's PR history page.'''
    try:
        return soup.find("h1").get("style")[6:]
    except TypeError:
        return "#000000"


def set_up_game(config_filename, game_name):
    with open(config_filename, "r") as infile:
        game_dict = yaml.load(infile, Loader = yaml.SafeLoader)[game_name]
        return Game(game_name, game_dict["times_url_suffix"], game_dict["players_url"], game_dict["levels"], game_dict["difficulties"])


def main():
    '''Execute top-level functionality'''
    session = requests.Session()

    goldeneye = set_up_game("games.yaml", "GoldenEye")
    perfect_dark = set_up_game("games.yaml", "Perfect Dark")

    for game in [goldeneye, perfect_dark]:
        game.load_players(session)
        for player in tqdm(game.players, desc = "Downloading times for " + game.name + " players"):
            player.load_times(session)
            pdb.set_trace()
        game.write_times()

if __name__ == "__main__":
    main()
