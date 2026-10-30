import requests
import pandas as pd
from datetime import date
import numpy as np

def Rachev_ratio_rus(x, s=None, e=None, VaR=95, board="TQBR"):
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

    p = pd.concat(series, axis=1).sort_index()
  
    # Check if there are fewer than 100 observations
    if len(p) < 100:
        print("Error. Insufficient number of observations.")
        return
    
    # Calculate log returns if requested and remove NA values
    p = np.log(p / p.shift(1)).dropna()
    
    L = pd.DataFrame(index=p.columns)  # Initialize with asset names as index
    
    # Loop over VaR values
    for m in range(len(VaR)):
        rachev = []
        
        # Loop over columns (assets) in x
        for col in p.columns:
            es = p[col].sort_values()  # Sort in ascending order
            
            # Calculate Rachev ratio
            lower_tail = es.iloc[:int((1 - VaR[m] * 0.01) * len(es))]
            upper_tail = es.iloc[int(VaR[m] * 0.01 * len(es)):]
            
            #rachev_ratio = round(upper_tail.mean() / -lower_tail.mean(), 3)
            rachev.append(round(upper_tail.mean() / -lower_tail.mean(), 3))
        
        L[f"Rachev Ratio at {VaR[m]}%"] = rachev
    
    return L

Rachev_ratio_rus(
  x=["GAZP", "SBER"], 
  s="2022-01-01", 
  VaR=[95, 97.5, 99]
  )
