#! /usr/bin/env python
'''This scrapes every PR History page on the-elite.net, and concatenates all PR times into one table.'''

import csv, itertools, requests, time, tqdm, yaml
import pdb # pylint: disable = unused-import
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime

LAST_CALL = time.time()
CALL_INTERVAL = 15.0 # Minimum time between requests (seconds)

class Player:
    def __init__(self, real_name, alias, game):
        self.real_name = real_name
        self.alias = alias
        self.game = game

        self.times = []

        self.hex_code = None
        self.times = {}
        self.player_url = "https://rankings.the-elite.net/~" + alias.replace(" ", "+")
        self.points = {}

    def __str__(self):
        return self.real_name + " / " + self.alias

    def __repr__(self):
        return self.real_name + " / " + self.alias

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
        return self.name + ": stages = " + [repr(stage) for stage in self.stages]

    def load_players(self, session):
        '''This creates the set of Players by visiting the All Players page and parsing the table.'''
        table = request_soup(session, self.players_url).find("table")
        pdb.set_trace()
        rows = [[cell.text.replace("\n", "") for cell in row.find_all("td")] for row in table.find_all("tr")[1:]]
        self.players.extend([Player(row[1], row[0], self) for row in rows])

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
        self.time = time

        self.player.times[self.stage.game].add(self)
        self.stage.times.add(self)
        self.points = 0

    def __str__(self):
        return str(self.player) + ": " + str(self.stage) + " " + self.time

    def __repr__(self):
        return str(self.player) + ": " + str(self.stage) + " " + self.time

    def calculate_points(self):
        pass


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
    time.sleep(max(CALL_INTERVAL - (time.time() - LAST_CALL), 0))
    LAST_CALL = time.time()


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
        game_yaml = [game for game in yaml.load(infile)["games"] if game["name"] == game_name][0]
        return Game(game_name, game_yaml["times_url_suffix"], game_yaml["players_page"], game_yaml["levels"], game_yaml["difficulties"])


def main():
    '''Execute top-level functionality'''
    session = requests.Session()

    goldeneye = set_up_game("games.yaml", "GoldenEye")
    perfect_dark = set_up_game("games.yaml", "Perfect Dark")

    for game in [goldeneye, perfect_dark]:
        game.load_players(session)
        for player in tqdm(game.players, desc = "Downloading times for " + game.name + " players"):
            player.load_times(session)
        game.write_times()

if __name__ == "__main__":
    main()
