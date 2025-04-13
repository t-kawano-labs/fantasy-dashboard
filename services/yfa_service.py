import streamlit as st
import pandas as pd
import datetime as dt
import tempfile
import json

from yahoo_fantasy_api import Game
from yahoo_fantasy_api import League
from yahoo_fantasy_api import Team
from yahoo_oauth import OAuth2

def get_oauth():
    oauth_dict = dict(st.secrets["yahoo"])
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        json.dump(oauth_dict, tmp)
        tmp.flush()
        return OAuth2(None, None, from_file=tmp.name)
    
def get_team(league_id):
    """Yahooファンタジーのチームデータを取得してDataFrameに変換する"""
    oauth = get_oauth()
    league = League(oauth, league_id)

    data = league.teams()
    # データを整形してリスト化
    teams = []
    for team in data.values():
        manager_info = team['managers'][0]['manager']
        team_info = {
            'team_key': team['team_key'],
            'team_id': team['team_id'],
            'team_name': team['name'],
            'division_id': team['division_id'],
            'waiver_priority': team['waiver_priority'],
            'moves': team['number_of_moves'],
            'trades': team['number_of_trades'],
            'weekly_adds': team['roster_adds']['value'],
            'draft_position': team['draft_position'],
            'manager_nickname': manager_info['nickname'],
            'felo_score': manager_info['felo_score'],
            'felo_tier': manager_info['felo_tier'],
            'team_url': team['url'],
            'team_logo_url': team['team_logos'][0]['team_logo']['url']
        }
        teams.append(team_info)
    return pd.DataFrame(teams)

def get_roster(team_id, week=None):
    """Yahooファンタジーのロースターデータを取得してDataFrameに変換する"""
    oauth = get_oauth()

    team = Team(oauth, team_id)
    roster = team.roster(week=week)
    return pd.DataFrame(roster)

def get_waivers(league_id):
    """Yahooファンタジーのウェーバーデータを取得してDataFrameに変換する"""
    oauth = get_oauth()

    league = League(oauth, league_id)
    waivers = league.waivers()
    return pd.DataFrame(waivers)

def get_free_agents(league_id, position):
    """YahooファンタジーのFAデータを取得してDataFrameに変換する"""
    oauth = get_oauth()

    league = League(oauth, league_id)
    free_agents = league.free_agents(position)
    return pd.DataFrame(free_agents)

def get_current_week(league_id):
    """Yahooファンタジーの現在の週を取得する"""
    oauth = get_oauth()

    league = League(oauth, league_id)
    current_week = league.current_week()
    return current_week