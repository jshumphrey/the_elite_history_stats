#! /usr/bin/env python
"""This scrapes every PR History page on the-elite.net, retrieves all historical PR times, and analyzes them."""

import itertools, re, requests, sys, time, yaml
import pdb # pylint: disable = unused-import
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime

LAST_CALL = None
if "--debug" in sys.argv:
    CALL_INTERVAL = 1 # Minimum time between requests (seconds)
else:
    CALL_INTERVAL = 10 # Minimum time between requests (seconds)


def request_soup(session, url):
    """Wraps the process of getting soup from a URL."""
    soup = None
    while not soup:
        try:
            bucket_sleep()
            soup = BeautifulSoup(session.get(url).content, features = "lxml")
        except (ConnectionError, TimeoutError) as _:
            pass

    return soup


def bucket_sleep():
    """Rate-limits requests, according to CALL_INTERVAL."""
    global LAST_CALL
    current_time = time.time()
    if LAST_CALL:
        time.sleep(max(CALL_INTERVAL - (current_time - LAST_CALL), 0))
    LAST_CALL = current_time


class Game:
    def __init__(self, name, config_filename):
        with open(config_filename, "r") as infile:
            game_dict = yaml.load(infile, Loader = yaml.SafeLoader)[name]

        self.name = name
        self.times_url_suffix = game_dict["times_url_suffix"]
        self.players_url = game_dict["players_url"]
        self.stages = {Stage(level, difficulty, self) for level, difficulty in itertools.product(game_dict["levels"], game_dict["difficulties"])}

        self.players = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Game: name = {!r}, times_url_suffix = {!r}, players_url = {!r}, stages = {!s}, players = {!s}".format(
            self.name, self.times_url_suffix, self.players_url, self.stages, self.players
        )

    def download_players(self, session):
        """This creates the game's Players by visiting the All Players page and parsing the table."""
        players_soup = request_soup(session, self.players_url)

        css_url = "https://rankings.the-elite.net" + players_soup.find(href = re.compile("\/css\/users.*css")).get("href")
        css_dict = parse_hex_code_css(request_soup(session, css_url))

        rows = [row.find_all("td") for row in players_soup.find("table").find_all("tr")[1:]]
        self.players.extend([Player(
            row[1].text.replace("\n", ""),
            row[0].text.replace("\n", ""),
            css_dict[row[0].find("a").get("class")[1]],
            self
        ) for row in rows])

    def download_times(self, session):
        """This wraps the process of downloading all times for every player for this game."""
        for player in tqdm(self.players[:10] if "--debug" in sys.argv else self.players, desc = "Downloading times for " + self.name + " players"):
            player.download_times(session)

    def export_players_and_times(self, filename):
        """This writes all the times out to a CSV."""
        with open(filename, "w") as outfile:
            yaml.dump([player.dict_repr() for player in self.players], outfile)

    def import_players_and_times(self, filename):
        """This creates the games Players (with their Times) by loading them from a YAML file."""
        with open(filename, "r") as infile:
            for player_yaml in yaml.load(infile, Loader = yaml.SafeLoader):
                player = Player(player_yaml["real_name"], player_yaml["alias"], player_yaml["hex_code"], self)
                player.import_times(player_yaml["times"])
                self.players.append(player)

    def find_stage(self, level_name, difficulty_name):
        """This returns the Stage for this game with the provided level and difficulty names."""
        try:
            return [stage for stage in self.stages if stage.level.name == level_name and stage.difficulty.name == difficulty_name][0]
        except IndexError:
            raise LookupError("Stage " + level_name + " " + difficulty_name + " not found!")


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

    def dict_repr(self):
        """This creates a dictionary representation of this Player, enabling it to be written out to a YAML file."""
        return {
            "real_name": self.real_name,
            "alias": self.alias,
            "hex_code": self.hex_code,
            "times": [t.dict_repr() for t in self.times]
        }

    def recalculate_points(self):
        """This recalculates the Player's points value by summing up the points for each of the Player's Times."""
        self.points = sum([time.points for time in self.times])

    def download_times(self, session):
        """This queries the-elite.net to load the Player's times with all of their times."""
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

    def import_times(self, times_list):
        """This loads the Player's times from a list of time dicts, provided by the exported YAML file."""
        self.times.extend([Time(
            self,
            self.game.find_stage(time_yaml["level"], time_yaml["difficulty"]),
            time_yaml["date"],
            time_yaml["system"],
            time_yaml["time_string"]
        ) for time_yaml in times_list])


class Time:
    def __init__(self, player, stage, date, system, time_string):
        self.player = player
        self.stage = stage
        self.date = date
        self.system = system
        self.time_string = time_string

        self.points = 0

    def __str__(self):
        return str(self.stage) + " " + self.time_string

    def __repr__(self):
        return "Time: player = {!s}, stage = {!s}, date = {!s}, system = {!r}, time_string = {!r}".format(
            self.player, self.stage, self.date, self.system, self.time_string
        )

    def dict_repr(self):
        """This creates a dictionary representation of this Time, enabling it to be written out to a YAML file."""
        return {
            "level": self.stage.level.name,
            "difficulty": self.stage.difficulty.name,
            "date": self.date,
            "system": self.system,
            "time_string": self.time_string
        }

    def calculate_points(self):
        """This calculates the current point value of this time, given all times for this game."""



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

    def get_times(self):
        """This returns a list of all times for this Stage across all Players for this Stage's Game."""
        return itertools.chain([[t for t in player.times if t.stage == self] for player in self.game.players])


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


def te_date_to_iso(te_date):
    """Converts the date format used on times pages to YYYY-MM-DD."""
    return datetime.strptime(te_date, "%d %b %Y").strftime("%Y-%m-%d")


def parse_hex_code_css(css_soup):
    """This parses the CSS soup from the-elite.net to create a dictionary mapping user IDs to hex codes."""
    css_entries = re.split(r",?a\.", css_soup.get_text())

    css_dict = {}
    for entry in [entry for entry in css_entries if entry]:
        entry_match = re.fullmatch(r"(u\d+)\{color:(\#[\da-fA-F]+)\}", entry)
        if not entry_match:
            css_dict[entry] = "#000000"
        else:
            css_dict[entry_match[1]] = entry_match[2]

    return css_dict


def main():
    """Execute top-level functionality."""

    goldeneye = Game("GoldenEye", "games.yaml")
    perfect_dark = Game("Perfect Dark", "games.yaml")

    for game in [goldeneye, perfect_dark]:
        if "--download" in sys.argv: # If the "download" option is specified, query the-elite.net for all our information.
            session = requests.Session()
            game.download_players(session) # Download all the players for this game.
            game.download_times(session) # Download all the times for each player.
            game.export_players_and_times(game.name.lower().replace(" ", "_") + "_times.yaml") # Write all times to an output YAML file so that we don't have to download everything each time we run.

        else: # The "download" option was not specified; load the players and times from the game's YAML file.
            game.import_players_and_times(game.name.lower().replace(" ", "_") + "_times.yaml")
            pdb.set_trace()
            foo

if __name__ == "__main__":
    main()
