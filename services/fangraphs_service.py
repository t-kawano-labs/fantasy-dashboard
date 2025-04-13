import pandas as pd
import requests

def get_projection_data(projection_system_name, position):
    """
    FangraphsのAPIからデータを取得し、DataFrameに変換する
    projection_system_name: プロジェクションシステムの名前
    position: pit(投手) / bat(野手)
    """
    
    # https://www.fangraphs.com/api/projections?type=rthebatx&stats=bat&pos=all&team=0&players=0&lg=all&z=1743763978
    api_url = f"https://www.fangraphs.com/api/projections?type={projection_system_name}&stats={position}&pos=all&team=0&players=0&lg=all&z=1742355856"
    response = requests.get(api_url)
    response.raise_for_status()  # エラーの場合は例外を発生させる
    data = response.json()
    return pd.DataFrame(data)