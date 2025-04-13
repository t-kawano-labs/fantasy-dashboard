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
    df = df.drop_duplicates(subset="YAHOOID", keep="first") #大谷用
    # 主要列だけ抽出（必要に応じて追加可能）
    cols = ["PLAYERNAME", "IDFANGRAPHS", "YAHOOID", "MLBID"]
    return df[cols].copy()