import pandas as pd
import requests
import io

PLAYERIDMAP_URL = "https://www.smartfantasybaseball.com/PLAYERIDMAPCSV"

def load_player_id_map() -> pd.DataFrame:
    """
    PLAYERIDMAP.csv を SmartFantasyBaseball からダウンロードして
    Fangraphs ID / Yahoo ID / PLAYERNAME 情報を含む DataFrame を返す。
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/csv,application/csv,application/octet-stream,*/*",
    }
    response = requests.get(PLAYERIDMAP_URL, headers=headers, timeout=10)
    response.raise_for_status()
    
    df = pd.read_csv(io.StringIO(response.content.decode("utf-8")))
    # 主要列だけ抽出（必要に応じて追加可能）
    cols = ["PLAYERNAME", "IDFANGRAPHS", "YAHOOID", "MLBID"]
    return df[cols].copy()


def get_pitcher_running_game():
    """MLBの走塁データを取得してDataFrameに変換する"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/csv,application/csv,application/octet-stream,*/*"
    }
    response = requests.get("https://baseballsavant.mlb.com/leaderboard/pitcher-running-game?game_type=Regular&n=1&pitch_hand=all&runner_moved=All&target_base=All&prior_pk=All&season_end=2025&season_start=2024&sortColumn=simple_prevented_on_running_attr&sortDirection=desc&split=no&team=&type=Pit&with_team_only=1&expanded=0&csv=true", headers=headers)
    if response.status_code == 200:
        df = pd.read_csv(io.StringIO(response.content.decode("utf-8")))
        cols = ["player_id", "player_name", "n_init", "rate_sbx"]
    else:
        print(f"CSVの取得に失敗しました。ステータスコード: {response.status_code}")
    return df[cols].copy()