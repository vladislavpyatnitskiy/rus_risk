import requests
import pandas as pd
from datetime import date
import numpy as np

def histVaR_rus(x, s=None, e=None, VaR=95, log_returns=True, board="TQBR"):
    if isinstance(x, str):
        x = [x]

    s = s or "2007-01-01"
    e = e or date.today().isoformat()

    series = []

    for ticker in x:
        url = (
            f"https://iss.moex.com/iss/engines/stock/markets/shares/"
            f"boards/{board}/securities/{ticker}/candles.json"
        )
        params = {"from": s, "till": e, "interval": 24}

        all_rows, start = [], 0
        while True:
            params["start"] = start
            r = requests.get(url, params=params)
            r.raise_for_status()
            candles = r.json()["candles"]
            columns, rows = candles["columns"], candles["data"]
            if not rows:
                break
            all_rows.extend(rows)
            start += len(rows)

        df = pd.DataFrame(all_rows, columns=columns)
        df["Date"] = pd.to_datetime(df["begin"]).dt.normalize()
        s_ = (df.drop_duplicates("Date")
                .set_index("Date")["close"]
                .rename(ticker))
        series.append(s_)

    dfs = pd.concat(series, axis=1).sort_index()
  
    data = dfs
      
    # Check if there are less than 100 observations
    if len(data) < 100:
      print("Insufficient number of observations.")
      return None
      
    # Calculate log returns if log_returns is True
    if log_returns:
      data = np.log(data / data.shift(1)).dropna()  # Log returns
      
    # Calculate the historical VaR (quantile of the distribution)
    var_values = data.apply(
      lambda col: np.percentile(col, 100 - VaR), 
      axis=0
      )
      
    # Convert to a DataFrame to display results
    var_df = pd.DataFrame(var_values)
    var_df.columns = [f"VaR {VaR}%"]
      
    return var_df
  
histVaR_rus(x=["GAZP", "SBER"])
