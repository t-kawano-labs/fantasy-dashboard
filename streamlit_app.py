import streamlit as st
import pandas as pd
import numpy as np
import json
import tempfile
import datetime as dt
import ast
from yahoo_fantasy_api import game
from yahoo_oauth import OAuth2

from services.yfa_service import get_waivers, get_roster, get_team, get_free_agents, get_current_week
from services.idmap_service import load_player_id_map
from services.fangraphs_service import get_projection_data
from services.data_service import merge_rosters_and_free_agents, merge_all_data, standardize_pitcher_stats, standardize_batter_stats, style_pitcher_stats, style_batter_stats, apply_position_filters, groupby_team, pitcher_stats_calc, batter_stats_calc
from services.savant_service import get_pitcher_running_game

league_id = "458.l.111045"

# タイトル
st.set_page_config(page_title="Fantasy Dashboard", layout="wide")
st.title("Fantasy Dashboard")   

# Sidebar
fg_projection_system_dict = {
    'ATC': 'ratcdc',
    'BATX': 'rthebatx',
    'STEA': 'steamerr',
    'OOP' : 'roopsydc',
    'DC': 'rfangraphsdc',
    'ZIPS': 'rzips'
}
# pitcher_proj_system = st.sidebar.selectbox(
#     "Pitcher Projection System",
#     options=list(fg_projection_system_dict.keys()),
#     index=list(fg_projection_system_dict.keys()).index('OOPSY'),
#     key="pitcher_proj_system_selectbox"
# )
# pitcher_proj_system_value = fg_projection_system_dict[pitcher_proj_system]

# batter_proj_system = st.sidebar.selectbox(
#     "Batter Projection System",
#     options=list(fg_projection_system_dict.keys()),
#     index=list(fg_projection_system_dict.keys()).index('THE BAT X'),
#     key="batter_proj_system_selectbox"
# )
# batter_proj_system_value = fg_projection_system_dict[batter_proj_system]

week_option = st.sidebar.selectbox("Select Roster Week", ["Current Week", "Next Week"], index=0)
current_week = get_current_week(league_id)
selected_week = None if week_option == "Current Week" else current_week + 1

if st.sidebar.button("Data Update"):
    # Yahooデータ取得
    df_teams = get_team(league_id)

    all_rosters = []
    for index, row in df_teams.iterrows():
        team_key = row['team_key']
        team_name = row['team_name']
        df_roster = get_roster(team_key, week=selected_week)

        df_roster['percent_owned'] = np.nan
        df_roster['team_key'] = team_key
        df_roster['team_name'] = team_name

        all_rosters.append(df_roster)

    df_all_rosters = pd.concat(all_rosters, ignore_index=True)
    df_all_rosters = df_all_rosters[['team_key', 'team_name', 'player_id', 'name', 'status', 'position_type', 'eligible_positions', 'selected_position']]

    df_waivers = get_waivers(league_id)
    df_fa_pitcher = get_free_agents(league_id, "P")
    df_fa_batter = get_free_agents(league_id, "B")

    df_all_players = merge_rosters_and_free_agents(df_all_rosters, df_waivers, df_fa_pitcher, df_fa_batter)
    df_all_players.to_csv("./data/all_players.csv", index=False)

    # Player IDマップ取得
    df_player_id_map = load_player_id_map()
    df_player_id_map.to_csv("./data/player_id_map.csv", index=False)

    # Fangraphsデータ取得
    df_fg_pitcher = None
    df_fg_batter = None

    for name, system in fg_projection_system_dict.items():
        df_proj_pit = get_projection_data(system, 'pit')
        if not df_proj_pit.empty:
            df_proj_pit = df_proj_pit.add_suffix(f"_{name}")
            df_proj_pit = df_proj_pit.rename(columns={f'playerid_{name}': 'playerid'})
            if df_fg_pitcher is None:
                df_fg_pitcher = df_proj_pit
            else:
                df_fg_pitcher = df_fg_pitcher.merge(df_proj_pit, on='playerid', how='outer')
        
        df_proj_bat = get_projection_data(system, 'bat')
        if not df_proj_bat.empty:
            df_proj_bat = df_proj_bat.add_suffix(f"_{name}")
            df_proj_bat = df_proj_bat.rename(columns={f'playerid_{name}': 'playerid'})
            if df_fg_batter is None:
                df_fg_batter = df_proj_bat
            else:
                df_fg_batter = df_fg_batter.merge(df_proj_bat, on='playerid', how='outer')

    df_fg_pitcher.to_csv("./data/fg_pitcher.csv", index=False)
    df_fg_batter.to_csv("./data/fg_batter.csv", index=False)

    # Savantデータ取得
    df_pitcher_running_game = get_pitcher_running_game()
    df_pitcher_running_game.to_csv("./data/pitcher_running_game.csv", index=False)

# データマージ-----------------
df_all_players = pd.read_csv("./data/all_players.csv")
df_player_id_map = pd.read_csv("./data/player_id_map.csv")
df_fg_pitcher = pd.read_csv("./data/fg_pitcher.csv")
df_fg_batter = pd.read_csv("./data/fg_batter.csv")
df_pitcher_running_game = pd.read_csv("./data/pitcher_running_game.csv")

df_pitcher, df_batter = merge_all_data(df_all_players, df_player_id_map, df_fg_pitcher, df_fg_batter, df_pitcher_running_game)

df_pitcher = pitcher_stats_calc(df_pitcher)

df_pitcher = standardize_pitcher_stats(df_pitcher)
df_pitcher = apply_position_filters(df_pitcher, position_key="pitcher")
df_pitcher_styled = style_pitcher_stats(df_pitcher)

st.subheader("Pitcher Stats (Individual)")
st.dataframe(df_pitcher_styled, use_container_width=True)
st.subheader("Pitcher Stats (Team Total)")
st.dataframe(style_pitcher_stats(groupby_team(df_pitcher)), use_container_width=True)

df_batter = batter_stats_calc(df_batter)
df_batter = standardize_batter_stats(df_batter)
df_batter = apply_position_filters(df_batter, position_key="batter")
df_batter_styled = style_batter_stats(df_batter)

st.subheader("Batter Stats (Individual)")
st.dataframe(df_batter_styled, use_container_width=True)
st.subheader("Batter Stats (Team Total)")
st.dataframe(style_pitcher_stats(groupby_team(df_batter)), use_container_width=True)
