#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 23 18:09:39 2022

@author: max
"""

import requests
import pandas as pd
import numpy as np
from bs4  import BeautifulSoup
import re
import time
#%%
def scrape_api(game_id):
    '''
    ***
    FEATURE THAT COULD BE COOL : FIND WHO IS IN THE PENALTY BOX WHEN EVENTS HAPPEN
    - my idea : make a list of dictionaries for each player in the penalty box
    penalty_dic = {'player_penalized_name' : [his name],
                   'player_penalized_id' : [his id],
                   'player_penalized_home_away' : [is he on the home or away team],
                   'player_penalized_team' : [his team abv],
                   'player_penalized_infraction' : [why hes in the penalty box],
                   'player_penalized_sentence' : [how much time he should spend in the box],
                   'player_penalized_time_in_the_box' : [the time he has spent in the box for this specific penalty],
                   'player_penalized_time_left' : [how much time left he is scheduled to spend in the box],
                   'player_penalized_is_goal' : [is the event a goal while player is in penalty_box],
                   'player_penalized_infraction' : [why hes in the penalty box],
                    }
    
    NEED TO FIX : GOALIES SHOULD NOT BE EVENT_PLAYERS 2 AND 3 ON SHOTS EVENTS
    
    FUTURE PROBLEM : SHOOTOUTS AND PENALTY SHOTS
    ***
    '''
    
    #game_id = 2021021035
    
    # starting time
    start = time.time()
    print(f"Beginning scrapping for game {game_id}.")

    #game_id = 2021021035
    
    
    event_list = []
    
    game = requests.get(
        f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live?site=en_nhl").json()
    
    shifts = requests.get(
        f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id}").json()
    
    shifts_df = pd.DataFrame(shifts['data'])
    
    s_time = []
    for i in range(len(shifts_df)):
        s_time.append((int(shifts_df.period.iloc[i])-1)*1200 + (sum(x * int(t) for x, t in zip([3600, 60, 1], (shifts_df.startTime.iloc[i]).split(":")))/60))
    shifts_df["s_time"] = s_time 
    
    e_time = []
    for i in range(len(shifts_df)):
        e_time.append((int(shifts_df.period.iloc[i])-1)*1200 + (sum(x * int(t) for x, t in zip([3600, 60, 1], (shifts_df.endTime.iloc[i]).split(":")))/60))
    shifts_df["e_time"] = e_time
    
    shifts_df["dur"] = shifts_df["e_time"] - shifts_df["s_time"]
    
    shifts_df["fullName"] = shifts_df[["firstName", "lastName"]].apply(lambda x: " ".join(x), axis =1)
    
    is_goalie = []
    for i in range(len(shifts_df)):
        if (shifts_df.playerId.iloc[i] in game["liveData"]["boxscore"]["teams"]["away"]["goalies"]) or (shifts_df.playerId.iloc[i] in game["liveData"]["boxscore"]["teams"]["home"]["goalies"]):
            is_goalie.append(1)
        else:
            is_goalie.append(0)
    
    shifts_df["is_goalie"] = is_goalie
    
    events = game["liveData"]["plays"]["allPlays"]
    season = game["gameData"]["game"]["season"]
    game_date = game["gameData"]["datetime"]["dateTime"][0:10]
    home_team_name = game['gameData']['teams']['home']['name']
    home_team_acc = game['gameData']['teams']['home']['triCode']
    away_team_name = game['gameData']['teams']['away']['name']
    away_team_acc = game['gameData']['teams']['away']['triCode']
    home_coach = game["liveData"]["boxscore"]["teams"]["home"]["coaches"][0]["person"]["fullName"]
    away_coach = game["liveData"]["boxscore"]["teams"]["away"]["coaches"][0]["person"]["fullName"]
    session = game["gameData"]["game"]["type"]
    
    
    
    for i in range(len(events)):
        
        #Try/except : event_player_1
        try:
            event_player_1 = events[i]['players'][0]['player']['fullName']
        except KeyError:
            event_player_1 = np.nan
        
        try:
            event_player_1_id = events[i]['players'][0]['player']['id']
        except KeyError:
            event_player_1_id = np.nan
        
        #Try/except : event_player_2
        try:
            event_player_2 = events[i]['players'][1]['player']['fullName']
        except Exception:
            event_player_2 = np.nan
        
        try:
            event_player_2_id = events[i]['players'][1]['player']['id']
        except Exception:
            event_player_2_id = np.nan
        
        #Try/except : event_player_3
        try:
            event_player_3 = events[i]['players'][2]['player']['fullName']
        except Exception as error:
            event_player_3 = np.nan
            
        try:
            event_player_3_id = events[i]['players'][2]['player']['id']
        except Exception as error:
            event_player_3_id = np.nan
            
        #Try/except : x_coord
        try:
            x_coord = events[i]['coordinates']['x']
        except KeyError:
            x_coord = np.nan
    
        #Try/except : y_coord
        try:
            y_coord = events[i]['coordinates']['y']
        except KeyError:
            y_coord = np.nan
            
        #Try/except : event_team
        try:
            event_team = events[i]['team']['triCode']
        except Exception:
            event_team = np.nan
       
    
            
        game_seconds = (int(events[i]['about']['period'])-1)*1200 + (sum(x * int(t) for x, t in zip([3600, 60, 1], events[i]['about']['periodTime'].split(":")))/60)
        
        
        home_sktrs_arr = []
        home_id_arr = []
        away_sktrs_arr = []
        away_id_arr = []
        home_skaters = 0
        away_skaters = 0
        home_goalie_arr = []
        away_goalie_arr = []
        
        for j in range(len(shifts_df)):
            if shifts_df.s_time.iloc[j] <= game_seconds < shifts_df.e_time.iloc[j]:
                
                name = shifts_df.fullName.iloc[j]
                playerid = shifts_df.playerId.iloc[j]
                
                '''
                Assuming that the maximum of skaters on each side is 7
                *still need to review this*
                '''
                if  shifts_df.teamName.iloc[j] == home_team_name:
                    if shifts_df.is_goalie.iloc[j] == 1:
                        home_goalie_arr.append(name)
                        home_goalie = name
                        home_goalie_id = playerid
                    else:
                        home_skaters += 1
                        home_sktrs_arr.append(name)
                        home_id_arr.append(playerid)
                        
                        if home_skaters == 1 : 
                            home_on_1 = name
                            home_on_1_id = playerid
                            
                            home_on_2 = np.nan
                            home_on_2_id = np.nan
                            home_on_3 = np.nan
                            home_on_3_id = np.nan
                            home_on_4 = np.nan
                            home_on_4_id = np.nan
                            home_on_5 = np.nan
                            home_on_5_id = np.nan
                            home_on_6 = np.nan
                            home_on_6_id = np.nan
                            home_on_7 = np.nan
                            home_on_7_id = np.nan
                            
                        elif home_skaters == 2:
                            home_on_2 = name
                            home_on_2_id = playerid
                            
                            home_on_3 = np.nan
                            home_on_3_id = np.nan
                            home_on_4 = np.nan
                            home_on_4_id = np.nan
                            home_on_5 = np.nan
                            home_on_5_id = np.nan
                            home_on_6 = np.nan
                            home_on_6_id = np.nan 
                            home_on_7 = np.nan
                            home_on_7_id = np.nan
                            
                        elif home_skaters == 3:
                            home_on_3 = name
                            home_on_3_id = playerid
                            
                            home_on_4 = np.nan
                            home_on_4_id = np.nan
                            home_on_5 = np.nan
                            home_on_5_id = np.nan
                            home_on_6 = np.nan
                            home_on_6_id = np.nan
                            home_on_7 = np.nan
                            home_on_7_id = np.nan
                            
                        elif home_skaters == 4:
                            home_on_4 = name
                            home_on_4_id = playerid
                            
                            home_on_5 = np.nan
                            home_on_5_id = np.nan
                            home_on_6 = np.nan
                            home_on_6_id = np.nan
                            home_on_7 = np.nan
                            home_on_7_id = np.nan
                            
                        elif home_skaters == 5:
                            home_on_5 = name
                            home_on_5_id = playerid
                            
                            home_on_6 = np.nan
                            home_on_6_id = np.nan
                            home_on_7 = np.nan
                            home_on_7_id = np.nan
                            
                        elif home_skaters == 6:
                            home_on_6 = name
                            home_on_6_id = playerid
                            
                            home_on_7 = np.nan
                            home_on_7_id = np.nan
                            
                        elif home_skaters == 7:
                            home_on_7 = name
                            home_on_7_id = playerid

                        else:
                            home_on_1 = np.nan
                            home_on_1_id = np.nan
                            home_on_2 = np.nan
                            home_on_2_id = np.nan
                            home_on_3 = np.nan
                            home_on_3_id = np.nan
                            home_on_4 = np.nan
                            home_on_4_id = np.nan
                            home_on_5 = np.nan
                            home_on_5_id = np.nan
                            home_on_6 = np.nan
                            home_on_6_id = np.nan
                            home_on_7 = np.nan
                            home_on_7_id = np.nan
                        
        
                else: #For away
                    if (shifts_df.is_goalie.iloc[j] == 1) & (shifts_df.teamName.iloc[j] == away_team_name) :
                        away_goalie_arr.append(name)
                        away_goalie = name
                        away_goalie_id = playerid
                    else:
                        away_skaters += 1
                        away_sktrs_arr.append(name)
                        away_id_arr.append(playerid)
                        
                        if away_skaters == 1 :
                            away_on_1 = name
                            away_on_1_id = playerid
                            
                            away_on_2 = np.nan
                            away_on_2_id = np.nan
                            away_on_3 = np.nan
                            away_on_3_id = np.nan
                            away_on_4 = np.nan
                            away_on_4_id = np.nan
                            away_on_5 = np.nan
                            away_on_5_id = np.nan
                            away_on_6 = np.nan
                            away_on_6_id = np.nan
                            away_on_7 = np.nan
                            away_on_7_id = np.nan
                            
                        elif away_skaters == 2:
                            away_on_2 = name
                            away_on_2_id = playerid
                            
                            away_on_3 = np.nan
                            away_on_3_id = np.nan
                            away_on_4 = np.nan
                            away_on_4_id = np.nan
                            away_on_5 = np.nan
                            away_on_5_id = np.nan
                            away_on_6 = np.nan
                            away_on_6_id = np.nan
                            away_on_7 = np.nan
                            away_on_7_id = np.nan
                            
                        elif away_skaters == 3:
                            away_on_3 = name
                            away_on_3_id = playerid
                            
                            away_on_4 = np.nan
                            away_on_4_id = np.nan
                            away_on_5 = np.nan
                            away_on_5_id = np.nan
                            away_on_6 = np.nan
                            away_on_6_id = np.nan
                            away_on_7 = np.nan
                            away_on_7_id = np.nan
                            
                        elif away_skaters == 4:
                            away_on_4 = name
                            away_on_4_id = playerid
                            
                            away_on_5 = np.nan
                            away_on_5_id = np.nan
                            away_on_6 = np.nan
                            away_on_6_id = np.nan
                            away_on_7 = np.nan
                            away_on_7_id = np.nan
                            
                        elif away_skaters == 5:
                            away_on_5 = name
                            away_on_5_id = playerid
                            
                            away_on_6 = np.nan
                            away_on_6_id = np.nan
                            away_on_7 = np.nan
                            away_on_7_id = np.nan
                            
                        elif away_skaters == 6:
                            away_on_6 = name
                            away_on_6_id = playerid
                            
                            away_on_6 = np.nan
                            away_on_6_id = np.nan
                            away_on_7 = np.nan
                            away_on_7_id = np.nan
                            
                        elif away_skaters == 7:
                            away_on_7 = name
                            away_on_7_id = playerid
                            
                        else:
                            away_on_1 = np.nan
                            away_on_1_id = np.nan
                            away_on_2 = np.nan
                            away_on_2_id = np.nan
                            away_on_3 = np.nan
                            away_on_3_id = np.nan
                            away_on_4 = np.nan
                            away_on_4_id = np.nan
                            away_on_5 = np.nan
                            away_on_5_id = np.nan
                            away_on_6 = np.nan
                            away_on_6_id = np.nan
                            away_on_7 = np.nan
                            away_on_7_id = np.nan
                
                
        
    
        #Goalies
        if len(home_goalie_arr) < 1:
            home_goalie = np.nan
            home_goalie_id = np.nan
            
        if len(away_goalie_arr) < 1:
            away_goalie = np.nan
            away_goalie_id = np.nan
        
        #Empty nets
        if (len(home_goalie_arr) < 1) & (len(home_goalie_arr) < 1):
            empty_net = "BOTH"
        elif (len(home_goalie_arr) < 1) & (len(home_goalie_arr) == 1):
            empty_net = "HOME"
        elif (len(home_goalie_arr) == 1) & (len(home_goalie_arr) < 1):
            empty_net = "AWAY" 
        else:
           empty_net = False 
           
        
        #Game score
        game_score = f"{events[i]['about']['goals']['home']}:{events[i]['about']['goals']['away']}"
        
        #Game strength
        game_strength = f"{home_skaters}v{away_skaters}"
        
        
        event_list.append(pd.DataFrame.from_dict({'season' : [season],
                                                  'game_id' : [game_id],
                                                  'game_date' : [game_date],
                                                  'session' : [session],
                                                  'home_team_name':[home_team_name],
                                                  'home_team_acc' : [home_team_acc],
                                                  'away_team_name' : [away_team_name],
                                                  'away_team_acc' : [away_team_acc],
                                                  'event_index' : [i],
                                                  'period': [events[i]['about']['period']],
                                                  'game_seconds' : [game_seconds],
                                                  'event_type' : [events[i]['result']['eventTypeId']],
                                                  'event_description' : [events[i]['result']['description']],
                                                  'event_detail' : [(events[i]['result']['secondaryType']) if 'secondaryType' in events[i]['result'].keys() else np.nan],
                                                  'empty_net' : [empty_net],
                                                  'event_team' : [event_team],
                                                  'event_player_1' : [event_player_1],
                                                  'event_player_1_id' : [event_player_1_id],
                                                  'event_player_2' : [event_player_2],
                                                  'event_player_2_id' : [event_player_2_id],
                                                  'event_player_3' : [event_player_3],
                                                  'event_player_3_id' : [event_player_3_id],
                                                  'home_goals': [events[i]['about']['goals']['home']],
                                                  'away_goals': [events[i]['about']['goals']['away']],
                                                  'x_coord' : [x_coord],
                                                  'y_coord' : [y_coord],
                                                  'home_goalie' : [home_goalie],
                                                  'home_goalie_id' : [home_goalie_id],
                                                  'away_goalie' : [away_goalie],
                                                  'away_goalie_id' : [away_goalie_id],
                                                  'n_home_skaters' : [home_skaters],
                                                  'n_away_skaters' : [away_skaters],
                                                  'home_sktrs_arr' : [home_sktrs_arr],
                                                  'away_sktrs_arr' : [away_sktrs_arr],
                                                  'home_id_arr' : [home_id_arr],
                                                  'away_id_arr' : [away_id_arr],
                                                  'home_on_1' : [home_on_1],
                                                  'home_on_1_id' : [home_on_1_id],
                                                  'home_on_2' : [home_on_2],
                                                  'home_on_2_id' : [home_on_2_id],
                                                  'home_on_3' : [home_on_3],
                                                  'home_on_3_id' : [home_on_3_id],
                                                  'home_on_4' : [home_on_4],
                                                  'home_on_4_id' : [home_on_4_id],
                                                  'home_on_5' : [home_on_5],
                                                  'home_on_5_id' : [home_on_5_id],
                                                  'home_on_6' : [home_on_6],
                                                  'home_on_6_id' : [home_on_6_id],
                                                  'home_on_7' : [home_on_6],
                                                  'home_on_7_id' : [home_on_6_id],
                                                  'away_on_1' : [away_on_1],
                                                  'away_on_1_id' : [away_on_1_id],
                                                  'away_on_2' : [away_on_2],
                                                  'away_on_2_id' : [away_on_2_id],
                                                  'away_on_3' : [away_on_3],
                                                  'away_on_3_id' : [away_on_3_id],
                                                  'away_on_4' : [away_on_4],
                                                  'away_on_4_id' : [away_on_4_id],
                                                  'away_on_5' : [away_on_5],
                                                  'away_on_5_id' : [away_on_5_id],
                                                  'away_on_6' : [away_on_6],
                                                  'away_on_6_id' : [away_on_6_id],
                                                  'away_on_7' : [away_on_6],
                                                  'away_on_7_id' : [away_on_6_id],
                                                  'home_coach' : [home_coach],
                                                  'away_coach' : [away_coach],
                                                  'game_score_state' : [game_score],
                                                  'game_strength' : [game_strength]
                                                  }))
    event_df = pd.concat(event_list).reset_index(drop=True)
    
    # end time
    end = time.time()
    print(f"Done! Runtime of scrapping is {end - start}.")
    return event_df

    
a = scrape_api(2021020983)


#%%    
game_id = 2021021035

# starting time
start = time.time()
print(f"Beginning scrapping for game {game_id}.")

#game_id = 2021021035


event_list = []

game = requests.get(
    f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live?site=en_nhl").json()

shifts = requests.get(
    f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id}").json()

shifts_df = pd.DataFrame(shifts['data'])

s_time = []
for i in range(len(shifts_df)):
    s_time.append((int(shifts_df.period.iloc[i])-1)*1200 + (sum(x * int(t) for x, t in zip([3600, 60, 1], (shifts_df.startTime.iloc[i]).split(":")))/60))
shifts_df["s_time"] = s_time 

e_time = []
for i in range(len(shifts_df)):
    e_time.append((int(shifts_df.period.iloc[i])-1)*1200 + (sum(x * int(t) for x, t in zip([3600, 60, 1], (shifts_df.endTime.iloc[i]).split(":")))/60))
shifts_df["e_time"] = e_time

shifts_df["dur"] = shifts_df["e_time"] - shifts_df["s_time"]

shifts_df["fullName"] = shifts_df[["firstName", "lastName"]].apply(lambda x: " ".join(x), axis =1)

is_goalie = []
for i in range(len(shifts_df)):
    if (shifts_df.playerId.iloc[i] in game["liveData"]["boxscore"]["teams"]["away"]["goalies"]) or (shifts_df.playerId.iloc[i] in game["liveData"]["boxscore"]["teams"]["home"]["goalies"]):
        is_goalie.append(1)
    else:
        is_goalie.append(0)

shifts_df["is_goalie"] = is_goalie

events = game["liveData"]["plays"]["allPlays"]
season = game["gameData"]["game"]["season"]
game_date = game["gameData"]["datetime"]["dateTime"][0:10]
home_team_name = game['gameData']['teams']['home']['name']
home_team_acc = game['gameData']['teams']['home']['triCode']
away_team_name = game['gameData']['teams']['away']['name']
away_team_acc = game['gameData']['teams']['away']['triCode']
home_coach = game["liveData"]["boxscore"]["teams"]["home"]["coaches"][0]["person"]["fullName"]
away_coach = game["liveData"]["boxscore"]["teams"]["away"]["coaches"][0]["person"]["fullName"]
session = game["gameData"]["game"]["type"]



for i in range(len(events)):
    
    #Try/except : event_player_1
    try:
        event_player_1 = events[i]['players'][0]['player']['fullName']
    except KeyError:
        event_player_1 = np.nan
    
    try:
        event_player_1_id = events[i]['players'][0]['player']['id']
    except KeyError:
        event_player_1_id = np.nan
    
    #Try/except : event_player_2
    try:
        event_player_2 = events[i]['players'][1]['player']['fullName']
    except Exception:
        event_player_2 = np.nan
    
    try:
        event_player_2_id = events[i]['players'][1]['player']['id']
    except Exception:
        event_player_2_id = np.nan
    
    #Try/except : event_player_3
    try:
        event_player_3 = events[i]['players'][2]['player']['fullName']
    except Exception as error:
        event_player_3 = np.nan
        
    try:
        event_player_3_id = events[i]['players'][2]['player']['id']
    except Exception as error:
        event_player_3_id = np.nan
        
    #Try/except : x_coord
    try:
        x_coord = events[i]['coordinates']['x']
    except KeyError:
        x_coord = np.nan

    #Try/except : y_coord
    try:
        y_coord = events[i]['coordinates']['y']
    except KeyError:
        y_coord = np.nan
        
    #Try/except : event_team
    try:
        event_team = events[i]['team']['triCode']
    except Exception:
        event_team = np.nan
   

        
    game_seconds = (int(events[i]['about']['period'])-1)*1200 + (sum(x * int(t) for x, t in zip([3600, 60, 1], events[i]['about']['periodTime'].split(":")))/60)
    
    
    home_sktrs_arr = []
    home_id_arr = []
    away_sktrs_arr = []
    away_id_arr = []
    home_skaters = 0
    away_skaters = 0
    home_goalie_arr = []
    away_goalie_arr = []
    
    for j in range(len(shifts_df)):
        if shifts_df.s_time.iloc[j] <= game_seconds < shifts_df.e_time.iloc[j]:
            
            name = shifts_df.fullName.iloc[j]
            playerid = shifts_df.playerId.iloc[j]
            
            '''
            Assuming that the maximum of skaters on each side is 7
            *still need to review this*
            '''
            if  shifts_df.teamName.iloc[j] == home_team_name:
                if shifts_df.is_goalie.iloc[j] == 1:
                    home_goalie_arr.append(name)
                    home_goalie = name
                    home_goalie_id = playerid
                else:
                    home_skaters += 1
                    home_sktrs_arr.append(name)
                    home_id_arr.append(playerid)
                    
                    if home_skaters == 1 : 
                        home_on_1 = name
                        home_on_1_id = playerid
                        
                        home_on_2 = np.nan
                        home_on_2_id = np.nan
                        home_on_3 = np.nan
                        home_on_3_id = np.nan
                        home_on_4 = np.nan
                        home_on_4_id = np.nan
                        home_on_5 = np.nan
                        home_on_5_id = np.nan
                        home_on_6 = np.nan
                        home_on_6_id = np.nan
                        home_on_7 = np.nan
                        home_on_7_id = np.nan
                        
                    elif home_skaters == 2:
                        home_on_2 = name
                        home_on_2_id = playerid
                        
                        home_on_3 = np.nan
                        home_on_3_id = np.nan
                        home_on_4 = np.nan
                        home_on_4_id = np.nan
                        home_on_5 = np.nan
                        home_on_5_id = np.nan
                        home_on_6 = np.nan
                        home_on_6_id = np.nan 
                        home_on_7 = np.nan
                        home_on_7_id = np.nan
                        
                    elif home_skaters == 3:
                        home_on_3 = name
                        home_on_3_id = playerid
                        
                        home_on_4 = np.nan
                        home_on_4_id = np.nan
                        home_on_5 = np.nan
                        home_on_5_id = np.nan
                        home_on_6 = np.nan
                        home_on_6_id = np.nan
                        home_on_7 = np.nan
                        home_on_7_id = np.nan
                        
                    elif home_skaters == 4:
                        home_on_4 = name
                        home_on_4_id = playerid
                        
                        home_on_5 = np.nan
                        home_on_5_id = np.nan
                        home_on_6 = np.nan
                        home_on_6_id = np.nan
                        home_on_7 = np.nan
                        home_on_7_id = np.nan
                        
                    elif home_skaters == 5:
                        home_on_5 = name
                        home_on_5_id = playerid
                        
                        home_on_6 = np.nan
                        home_on_6_id = np.nan
                        home_on_7 = np.nan
                        home_on_7_id = np.nan
                        
                    elif home_skaters == 6:
                        home_on_6 = name
                        home_on_6_id = playerid
                        
                        home_on_7 = np.nan
                        home_on_7_id = np.nan
                        
                    elif home_skaters == 7:
                        home_on_7 = name
                        home_on_7_id = playerid

                    else:
                        home_on_1 = np.nan
                        home_on_1_id = np.nan
                        home_on_2 = np.nan
                        home_on_2_id = np.nan
                        home_on_3 = np.nan
                        home_on_3_id = np.nan
                        home_on_4 = np.nan
                        home_on_4_id = np.nan
                        home_on_5 = np.nan
                        home_on_5_id = np.nan
                        home_on_6 = np.nan
                        home_on_6_id = np.nan
                        home_on_7 = np.nan
                        home_on_7_id = np.nan
                    
    
            else: #For away
                if (shifts_df.is_goalie.iloc[j] == 1) & (shifts_df.teamName.iloc[j] == away_team_name) :
                    away_goalie_arr.append(name)
                    away_goalie = name
                    away_goalie_id = playerid
                else:
                    away_skaters += 1
                    away_sktrs_arr.append(name)
                    away_id_arr.append(playerid)
                    
                    if away_skaters == 1 :
                        away_on_1 = name
                        away_on_1_id = playerid
                        
                        away_on_2 = np.nan
                        away_on_2_id = np.nan
                        away_on_3 = np.nan
                        away_on_3_id = np.nan
                        away_on_4 = np.nan
                        away_on_4_id = np.nan
                        away_on_5 = np.nan
                        away_on_5_id = np.nan
                        away_on_6 = np.nan
                        away_on_6_id = np.nan
                        away_on_7 = np.nan
                        away_on_7_id = np.nan
                        
                    elif away_skaters == 2:
                        away_on_2 = name
                        away_on_2_id = playerid
                        
                        away_on_3 = np.nan
                        away_on_3_id = np.nan
                        away_on_4 = np.nan
                        away_on_4_id = np.nan
                        away_on_5 = np.nan
                        away_on_5_id = np.nan
                        away_on_6 = np.nan
                        away_on_6_id = np.nan
                        away_on_7 = np.nan
                        away_on_7_id = np.nan
                        
                    elif away_skaters == 3:
                        away_on_3 = name
                        away_on_3_id = playerid
                        
                        away_on_4 = np.nan
                        away_on_4_id = np.nan
                        away_on_5 = np.nan
                        away_on_5_id = np.nan
                        away_on_6 = np.nan
                        away_on_6_id = np.nan
                        away_on_7 = np.nan
                        away_on_7_id = np.nan
                        
                    elif away_skaters == 4:
                        away_on_4 = name
                        away_on_4_id = playerid
                        
                        away_on_5 = np.nan
                        away_on_5_id = np.nan
                        away_on_6 = np.nan
                        away_on_6_id = np.nan
                        away_on_7 = np.nan
                        away_on_7_id = np.nan
                        
                    elif away_skaters == 5:
                        away_on_5 = name
                        away_on_5_id = playerid
                        
                        away_on_6 = np.nan
                        away_on_6_id = np.nan
                        away_on_7 = np.nan
                        away_on_7_id = np.nan
                        
                    elif away_skaters == 6:
                        away_on_6 = name
                        away_on_6_id = playerid
                        
                        away_on_6 = np.nan
                        away_on_6_id = np.nan
                        away_on_7 = np.nan
                        away_on_7_id = np.nan
                        
                    elif away_skaters == 7:
                        away_on_7 = name
                        away_on_7_id = playerid
                        
                    else:
                        away_on_1 = np.nan
                        away_on_1_id = np.nan
                        away_on_2 = np.nan
                        away_on_2_id = np.nan
                        away_on_3 = np.nan
                        away_on_3_id = np.nan
                        away_on_4 = np.nan
                        away_on_4_id = np.nan
                        away_on_5 = np.nan
                        away_on_5_id = np.nan
                        away_on_6 = np.nan
                        away_on_6_id = np.nan
                        away_on_7 = np.nan
                        away_on_7_id = np.nan
            
            
    

    #Goalies
    if len(home_goalie_arr) < 1:
        home_goalie = np.nan
        home_goalie_id = np.nan
        
    if len(away_goalie_arr) < 1:
        away_goalie = np.nan
        away_goalie_id = np.nan
    
    #Empty nets
    if (len(home_goalie_arr) < 1) & (len(home_goalie_arr) < 1):
        empty_net = "BOTH"
    elif (len(home_goalie_arr) < 1) & (len(home_goalie_arr) == 1):
        empty_net = "HOME"
    elif (len(home_goalie_arr) == 1) & (len(home_goalie_arr) < 1):
        empty_net = "AWAY" 
    else:
       empty_net = False 
       
    
    #Game score
    game_score = f"{events[i]['about']['goals']['home']}:{events[i]['about']['goals']['away']}"
    
    #Game strength
    game_strength = f"{home_skaters}v{away_skaters}"
    
    
    event_list.append(pd.DataFrame.from_dict({'season' : [season],
                                              'game_id' : [game_id],
                                              'game_date' : [game_date],
                                              'session' : [session],
                                              'home_team_name':[home_team_name],
                                              'home_team_acc' : [home_team_acc],
                                              'away_team_name' : [away_team_name],
                                              'away_team_acc' : [away_team_acc],
                                              'event_index' : [i],
                                              'period': [events[i]['about']['period']],
                                              'game_seconds' : [game_seconds],
                                              'event_type' : [events[i]['result']['eventTypeId']],
                                              'event_description' : [events[i]['result']['description']],
                                              'event_detail' : [(events[i]['result']['secondaryType']) if 'secondaryType' in events[i]['result'].keys() else np.nan],
                                              'empty_net' : [empty_net],
                                              'event_team' : [event_team],
                                              'event_player_1' : [event_player_1],
                                              'event_player_1_id' : [event_player_1_id],
                                              'event_player_2' : [event_player_2],
                                              'event_player_2_id' : [event_player_2_id],
                                              'event_player_3' : [event_player_3],
                                              'event_player_3_id' : [event_player_3_id],
                                              'home_goals': [events[i]['about']['goals']['home']],
                                              'away_goals': [events[i]['about']['goals']['away']],
                                              'x_coord' : [x_coord],
                                              'y_coord' : [y_coord],
                                              'home_goalie' : [home_goalie],
                                              'home_goalie_id' : [home_goalie_id],
                                              'away_goalie' : [away_goalie],
                                              'away_goalie_id' : [away_goalie_id],
                                              'n_home_skaters' : [home_skaters],
                                              'n_away_skaters' : [away_skaters],
                                              'home_sktrs_arr' : [home_sktrs_arr],
                                              'away_sktrs_arr' : [away_sktrs_arr],
                                              'home_id_arr' : [home_id_arr],
                                              'away_id_arr' : [away_id_arr],
                                              'home_on_1' : [home_on_1],
                                              'home_on_1_id' : [home_on_1_id],
                                              'home_on_2' : [home_on_2],
                                              'home_on_2_id' : [home_on_2_id],
                                              'home_on_3' : [home_on_3],
                                              'home_on_3_id' : [home_on_3_id],
                                              'home_on_4' : [home_on_4],
                                              'home_on_4_id' : [home_on_4_id],
                                              'home_on_5' : [home_on_5],
                                              'home_on_5_id' : [home_on_5_id],
                                              'home_on_6' : [home_on_6],
                                              'home_on_6_id' : [home_on_6_id],
                                              'home_on_7' : [home_on_6],
                                              'home_on_7_id' : [home_on_6_id],
                                              'away_on_1' : [away_on_1],
                                              'away_on_1_id' : [away_on_1_id],
                                              'away_on_2' : [away_on_2],
                                              'away_on_2_id' : [away_on_2_id],
                                              'away_on_3' : [away_on_3],
                                              'away_on_3_id' : [away_on_3_id],
                                              'away_on_4' : [away_on_4],
                                              'away_on_4_id' : [away_on_4_id],
                                              'away_on_5' : [away_on_5],
                                              'away_on_5_id' : [away_on_5_id],
                                              'away_on_6' : [away_on_6],
                                              'away_on_6_id' : [away_on_6_id],
                                              'away_on_7' : [away_on_6],
                                              'away_on_7_id' : [away_on_6_id],
                                              'home_coach' : [home_coach],
                                              'away_coach' : [away_coach],
                                              'game_score_state' : [game_score],
                                              'game_strength' : [game_strength]
                                              }))
event_df = pd.concat(event_list).reset_index(drop=True)

# end time
end = time.time()
print(f"Done! Runtime of scrapping is {end - start}.")
