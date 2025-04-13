import pandas as pd
import numpy as np
import streamlit as st
import ast

def merge_rosters_and_free_agents(df_rosters, df_waivers, df_fa_pitcher, df_fa_batter):
    df_waivers['team_key'] = np.nan
    df_waivers['team_name'] = "Waiver"
    df_waivers['selected_position'] = "Waiver"

    df_fa_pitcher['team_key'] = np.nan
    df_fa_pitcher['team_name'] = "FA"
    df_fa_pitcher['selected_position'] = "FA"

    df_fa_batter['team_key'] = np.nan
    df_fa_batter['team_name'] = "FA"
    df_fa_batter['selected_position'] = "FA"

    df_waivers_fa = pd.concat([df_waivers, df_fa_pitcher, df_fa_batter], ignore_index=True)
    df_waivers_fa = df_waivers_fa[['team_key', 'team_name', 'player_id', 'name', 'status', 'position_type', 'eligible_positions', 'selected_position']]

    df_all_players = pd.concat([df_rosters, df_waivers_fa], ignore_index=True)
    return df_all_players

def merge_all_data(df_all_players, df_player_id_map, df_fg_pitcher, df_fg_batter, df_pitcher_running_game):
    # 大谷翔平（Batter / Pitcher）対策
    df_all_players["player_id"] = df_all_players["player_id"].replace({1000001: 10835, 1000002: 10835})

    # IDマッピング
    df_all_players = df_all_players.merge(df_player_id_map, left_on='player_id', right_on='YAHOOID', how='inner')

    # Fangraphs 投手データとマージ（大谷バッター版は除外）
    df_pitcher = df_all_players.merge(df_fg_pitcher, left_on='IDFANGRAPHS', right_on='playerid', how='inner')
    df_pitcher = df_pitcher[~df_pitcher["name"].isin(["Shohei Ohtani (Batter)"])]

    # Fangraphs 野手データとマージ（大谷ピッチャー版は除外）
    df_batter = df_all_players.merge(df_fg_batter, left_on='IDFANGRAPHS', right_on='playerid', how='inner')
    df_batter = df_batter[~df_batter["name"].isin(["Shohei Ohtani (Pitcher)"])]

    # 投手ランニングデータとマージ
    df_pitcher = df_pitcher.merge(df_pitcher_running_game, left_on='MLBID', right_on='player_id', how='left')

    return df_pitcher, df_batter

def pitcher_stats_calc(df_pitcher: pd.DataFrame) -> pd.DataFrame:
    df_pitcher['IP'] = df_pitcher['IP_ATC']
    df_pitcher['W'] = df_pitcher['W_ATC']
    df_pitcher['HR'] = df_pitcher['HR_STEA']
    df_pitcher['BB'] = df_pitcher['BB_STEA']
    df_pitcher['SO'] = df_pitcher['SO_OOP']
    df_pitcher['H'] = df_pitcher['H_ATC']
    df_pitcher['ERA'] = df_pitcher['ERA_ATC']
    df_pitcher['K/BB'] = df_pitcher['K/BB_STEA']
    # df_pitcher['RAPP'] = df_pitcher['RAPP_DC']
    df_pitcher['QS'] = df_pitcher['QS_DC']
    df_pitcher['SV'] = df_pitcher['SV_DC']
    df_pitcher['HLD'] = df_pitcher['HLD_DC']
    df_pitcher['G'] = df_pitcher['G_DC']
    df_pitcher['GS'] = df_pitcher['GS_DC']

    df_pitcher['SV+H'] = df_pitcher['SV'] + df_pitcher['HLD']
    df_pitcher['RAPP'] = df_pitcher['G'] - df_pitcher['GS']
    df_pitcher['rate_sbx'] = df_pitcher['rate_sbx'].fillna(0.014)
    df_pitcher['SB_oppo'] = (df_pitcher['H'] + df_pitcher['BB'])
    df_pitcher['SB'] = df_pitcher['SB_oppo'] * df_pitcher['rate_sbx']
    df_pitcher = df_pitcher[['team_name', 'name', 'status', 'position_type', 'eligible_positions', 'selected_position', 'IP', 'W', 'HR', 'BB', 'SO', 'SB', 'ERA', 'K/BB', 'RAPP', 'QS', 'SV+H']]
    return df_pitcher


def batter_stats_calc(df_batter: pd.DataFrame) -> pd.DataFrame:
    df_batter['R'] = df_batter['R_BATX']
    df_batter['H'] = df_batter['H_ATC']
    df_batter['HR'] = df_batter['HR_BATX']
    df_batter['RBI'] = df_batter['RBI_BATX']
    df_batter['SH'] = df_batter['SH_DC']
    df_batter['BB'] = df_batter['BB_BATX']
    df_batter['SO'] = df_batter['SO_STEA']
    df_batter['OPS'] = df_batter['OPS_BATX']
    df_batter['SB'] = df_batter['SB_ZIPS']
    df_batter['CS'] = df_batter['CS_ZIPS']

    df_batter['NSB'] = df_batter['SB'] + df_batter['CS']
    df_batter = df_batter[['team_name', 'name', 'status', 'position_type', 'eligible_positions', 'selected_position', 'R', 'H', 'HR', 'RBI', 'SH', 'BB', 'SO', 'OPS', 'NSB']]

    return df_batter

def standardize_pitcher_stats(df: pd.DataFrame) -> pd.DataFrame:
    target_cols = ['IP', 'W', 'HR', 'BB', 'SO', 'SB', 'ERA', 'K/BB', 'RAPP', 'QS', 'SV+H']
    for col in target_cols:
        if col in df.columns:
            if col in ['SB', 'ERA', 'K/BB']:
                mean = df[col].mean()
                std = df[col].std()
                upper_limit = mean + 1.5 * std
                df[col] = np.where(df[col] > upper_limit, upper_limit, df[col])
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val != min_val:
                score = (df[col] - min_val) / (max_val - min_val) * 10
            else:
                score = 5
            if col in ['HR', 'BB', 'ERA', 'SB']:
                df[f"{col}_pts"] = 10 - score
            else:
                df[f"{col}_pts"] = score
    meta_cols = ["team_name", "name", "status", "position_type", "eligible_positions", "selected_position"]
    pts_cols = [f"{col}_pts" for col in target_cols if f"{col}_pts" in df.columns]
    df["Total_pts"] = df[pts_cols].sum(axis=1)
    ordered_cols = [col for col in meta_cols if col in df.columns] + ["Total_pts"] + pts_cols + target_cols
    df = df[[col for col in ordered_cols if col in df.columns]]
    return df

def standardize_batter_stats(df: pd.DataFrame) -> pd.DataFrame:
    target_cols = ['R', 'H', 'HR', 'RBI', 'SH', 'BB', 'SO', 'OPS', 'NSB']
    for col in target_cols:
        if col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val != min_val:
                score = (df[col] - min_val) / (max_val - min_val) * 10
            else:
                score = 5
            if col in ['SO']:
                df[f"{col}_pts"] = 10 - score
            else:
                df[f"{col}_pts"] = score
    meta_cols = ["team_name", "name", "status", "position_type", "eligible_positions", "selected_position"]
    pts_cols = [f"{col}_pts" for col in target_cols if f"{col}_pts" in df.columns]
    df["Total_pts"] = df[pts_cols].sum(axis=1)
    ordered_cols = [col for col in meta_cols if col in df.columns] + ["Total_pts"] + pts_cols + target_cols
    df = df[[col for col in ordered_cols if col in df.columns]]
    return df

def apply_position_filters(df, position_key=""):

    team_options = df["team_name"].dropna().unique().tolist()
    selected_teams = st.multiselect(f"Filter by Team {position_key}", options=team_options, default=team_options, key=f"filter_team_{position_key}")
    df["eligible_positions"] = df["eligible_positions"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

    all_positions = sorted(set(pos for sublist in df["eligible_positions"] for pos in sublist))
    selected_positions = st.multiselect(f"Filter by Eligible Positions {position_key}", options=all_positions, default=all_positions, key=f"filter_ep_{position_key}")
    df = df[df["eligible_positions"].apply(lambda positions: any(pos in positions for pos in selected_positions))]

    pos_options = df["selected_position"].dropna().unique().tolist()
    selected_selected_pos = st.multiselect(f"Filter by Position {position_key}", options=pos_options, default=pos_options, key=f"filter_pos_{position_key}")

    df = df[df["team_name"].isin(selected_teams) & df["selected_position"].isin(selected_selected_pos)]
    return df

def style_pitcher_stats(df: pd.DataFrame):
    pts_cols = [col for col in df.columns if col.endswith("_pts") or col == "Total_pts"]
    format_dict = {col: "{:.0f}" for col in pts_cols}
    # 整数で表示したい元カラム
    int_cols = ["IP", "W", "HR", "BB", "SO", "SB", "RAPP", "QS", "SV+H"]
    for col in int_cols:
        if col in df.columns:
            format_dict[col] = "{:.0f}"

    # 小数点第3位まで表示したいカラム
    float_cols = ["ERA", "K/BB"]
    for col in float_cols:
        if col in df.columns:
            format_dict[col] = "{:.2f}"
    return df.style.format(format_dict).background_gradient(subset=pts_cols, cmap="bwr", axis=0)

def style_batter_stats(df: pd.DataFrame):
    pts_cols = [col for col in df.columns if col.endswith("_pts") or col == "Total_pts"]
    format_dict = {col: "{:.0f}" for col in pts_cols}
    # 整数で表示したい元カラム
    int_cols = ["R", "H", "HR", "RBI", "SH", "BB", "SO", "NSB"]
    for col in int_cols:
        if col in df.columns:
            format_dict[col] = "{:.0f}"

    # 小数点第3位まで表示したいカラム
    float_cols = ["OPS"]
    for col in float_cols:
        if col in df.columns:
            format_dict[col] = "{:.3f}"
    return df.style.format(format_dict).background_gradient(subset=pts_cols, cmap="bwr", axis=0)

def groupby_team(df: pd.DataFrame):
    df = df.groupby("team_name").sum(numeric_only=True).reset_index()
    pts_columns = [col for col in df.columns if col.endswith("_pts")]
    df = df[["team_name"] + pts_columns]
    df = df[~df["team_name"].isin(["FA", "Waiver"])] # 大谷用
    return df