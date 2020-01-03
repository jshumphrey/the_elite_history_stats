#! /usr/bin/env python

from datetime import datetime

class Player:
    def __init__(self, real_name, alias, has_ge, has_pd):
        self.real_name = real_name
        self.alias = alias
        self.has_ge = has_ge
        self.has_pd = has_pd

        self.hex_code = None
        self.times = {"GoldenEye": set(), "Perfect Dark": set()}
        self.player_url = "https://rankings.the-elite.net/~" + alias.replace(" ", "+")
        self.points = 0
        
    def __str__(self):
        return self.real_name + " / " + self.alias
        
    def __repr__(self):
        return self.real_name + " / " + self.alias
        
    def add_up_points(self, game):
        self.points = sum([time.points for time in self.times if time.stage.game == game])
        
    def has_times(self, game):
        if game == "GoldenEye":
            return self.has_ge
        return self.has_pd

class Stage:
    def __init__(self, level_name, difficulty, game):
        self.level_name = level_name
        self.difficulty = difficulty
        self.game = game
        
        self.times = set()
        
    def __str__(self):
        return self.level_name + " " + self.difficulty
        
    def __repr__(self):
        return self.level_name + " " + self.difficulty

class Time:
    def __init__(self, player, stage, date, system, time):
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
