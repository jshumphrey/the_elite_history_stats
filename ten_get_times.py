#! /usr/bin/env python
'''This scrapes every PR History page on the-elite.net,
and concatenates all PR times into one table.'''

import csv, datetime, requests, sqlite3, time, tqdm
import pdb # pylint: disable = unused-import
from bs4 import BeautifulSoup
from tqdm import tqdm
from ten_classes import *

LAST_CALL = time.time()
CALL_INTERVAL = 15.0 # Minimum time between requests (seconds)

PLAYERS_PAGE_URL = "https://rankings.the-elite.net/players"
GAMES = {
    "GoldenEye": {
        "levels": [
            "Dam",
            "Facility",
            "Runway",
            "Surface 1",
            "Bunker 1",
            "Silo",
            "Frigate",
            "Surface 2",
            "Bunker 2",
            "Statue",
            "Archives",
            "Streets",
            "Depot",
            "Train",
            "Jungle",
            "Control",
            "Caverns",
            "Cradle",
            "Aztec",
            "Egypt"
        ],
        "difficulties": ["Agent", "Secret Agent", "00 Agent"],
        "times_url_suffix": "/goldeneye/history"
    },
    "Perfect Dark": {
        "levels": [
            "dataDyne Central - Defection",
            "dataDyne Research - Investigation",
            "dataDyne Central - Extraction",
            "Carrington Villa - Hostage One",
            "Chicago - Stealth",
            "G5 Building - Reconnaissance",
            "Area 51 - Infiltration",
            "Area 51 - Rescue",
            "Area 51 - Escape",
            "Air Base - Espionage",
            "Air Force One - Antiterrorism",
            "Crash Site - Confrontation",
            "Pelagic II - Exploration",
            "Deep Sea - Nullify Threat",
            "Carrington Institute - Defense",
            "Attack Ship - Covert Assault",
            "Skedar Ruins - Battle Shrine",
            "Mr. Blonde's Revenge",
            "Maian SOS",
            "WAR!",
            "The Duel"
        ],
        "difficulties": ["Agent", "Special Agent", "Perfect Agent"],
        "times_url_suffix": "/perfect-dark/history"
    }
}

def request_soup(session, url):
    '''Wraps the process of getting soup from a URL.'''
    soup = None
    while not soup:
        try:
            bucket_sleep()
            soup = BeautifulSoup(session.get(url).content, features = "lxml")
        except (ConnectionError, TimeoutError) as e:    
            pass
    
    return soup

def bucket_sleep():
    '''Rate-limits requests, according to CALL_INTERVAL.'''
    global LAST_CALL
    time.sleep(max(CALL_INTERVAL - (time.time() - LAST_CALL), 0))
    LAST_CALL = time.time()

def load_stages():
    '''Sets up the Stages from the GAMES dict.'''
    return {Stage(level, difficulty, game) for game, game_dict in GAMES.items() for level in game_dict["levels"] for difficulty in game_dict["difficulties"]}

def te_date_to_iso(te_date):
    '''Converts the date format used on times pages to YYYY-MM-DD.'''
    return datetime.strptime(te_date, "%d %b %Y").strftime("%Y-%m-%d")

def get_stage(stages, level, difficulty):
    '''This returns the Stage with th specified level name and difficulty.'''
    output = [stage for stage in stages if stage.level_name == level and stage.difficulty == difficulty]
    if not output:
        raise ValueError("Could not find stage \"" + level + " " + difficulty + "\"!")
    return output[0]

def get_players(session):
    '''This creates the set of Players by visiting the All Players page and parsing the table.'''
    table = request_soup(session, PLAYERS_PAGE_URL).find("table")
    rows = [[cell.text.replace("\n", "") for cell in row.find_all("td")] for row in table.find_all("tr")[1:]]
    return {Player(row[1], row[0], bool(row[2]), bool(row[3])) for row in rows}

def get_hex_code(soup):
    '''This extracts the hex code from a player's PR history page.'''
    try:
        return soup.find("h1").get("style")[6:]
    except TypeError:
        return "#000000"

def get_times(session, players, stages):
    '''This sweeps through every player's PR history page
    and creates a set of all PR times posted on the site.'''
    times = set()
    for player in tqdm(players, desc = "Fetching times"):
        for game, game_dict in GAMES.items():
            if player.has_times(game):
                soup = request_soup(session, player.player_url + game_dict["times_url_suffix"])
                player.hex_code = get_hex_code(soup)
                try:
                    rows = [[cell.text.replace("\n", "") for cell in row.find_all("td")] for row in soup.find("table").find_all("tr")[1:]]
                except AttributeError:
                    continue

                for row in rows:
                    if all([row[0] != "Unknown", row[3] != "N/A"]):
                        times.add(Time(
                            player,
                            get_stage(stages, row[1], row[2]),
                            te_date_to_iso(row[0]),
                            row[4],
                            row[3]
                        ))

    return times

def write_times(times):
    '''This writes all the times out to a CSV.'''
    with open("times.csv", "w") as outfile:
        writer = csv.writer(outfile, delimiter = ",", quotechar = '"')
        writer.writerow(["Player Name", "Player Alias", "Hex Code", "Date", "Game", "Level", "Difficulty", "Time", "System"])
        for each_time in sorted(times, key = lambda x: x.date):
            writer.writerow([
                each_time.player.real_name,
                each_time.player.alias,
                each_time.player.hex_code,
                each_time.date,
                each_time.stage.game,
                each_time.stage.level_name,
                each_time.stage.difficulty,
                each_time.time,
                each_time.system
            ])

def main():
    '''Execute top-level functionality'''
    session = requests.Session()
    stages = load_stages()
    players = get_players(session)
    times = get_times(session, players, stages)
    write_times(times)

main()
