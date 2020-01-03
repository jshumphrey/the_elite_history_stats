#! /usr/bin/env python
'''This scrapes every PR History page on the-elite.net,
and concatenates all PR times into one table.'''

import copy, csv, datetime, tqdm
import pdb # pylint: disable = unused-import
from tqdm import tqdm
from ten_classes import *

TIMES_PAGE = {
    "GoldenEye": {
        "Dam": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Facility": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Runway": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Surface 1": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Bunker 1": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Silo": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Frigate": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Surface 2": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Bunker 2": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Statue": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Archives": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Streets": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Depot": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Train": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Jungle": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Control": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Caverns": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Cradle": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Aztec": {"Agent": None, "Secret Agent": None, "00 Agent": None},
        "Egypt": {"Agent": None, "Secret Agent": None, "00 Agent": None}
    },
    "Perfect Dark": {
        "dataDyne Central - Defection": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "dataDyne Research - Investigation": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "dataDyne Central - Extraction": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Carrington Villa - Hostage One": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Chicago - Stealth": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "G5 Building - Reconnaissance": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Area 51 - Infiltration": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Area 51 - Rescue": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Area 51 - Escape": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Air Base - Espionage": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Air Force One - Antiterrorism": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Crash Site - Confrontation": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Pelagic II - Exploration": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Deep Sea - Nullify Threat": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Carrington Institute - Defense": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Attack Ship - Covert Assault": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Skedar Ruins - Battle Shrine": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Mr. Blonde's Revenge": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "Maian SOS": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "WAR!": {"Agent": None, "Special Agent": None, "Perfect Agent": None},
        "The Duel": {"Agent": None, "Special Agent": None, "Perfect Agent": None}
    }
}

def read_times(filename):
    days = {}
    with open(filename, "r") as infile:
        reader = csv.reader(infile, delimiter = ",", quotechar = '"')
        reader.__next__()
        
        for row in reader:
            if row[3] not in days:
                days[row[3]] = []
            days[row[3]].append(row)
            
    return days


def main():
    times = read_times("times.csv")
    
    # for day in date range (start, end)
    # if times for day
    #     add times
    #     generate points snapshot
    # else
    #     points snapshot = yesterday's points snapshot
    
    
    
main()
    