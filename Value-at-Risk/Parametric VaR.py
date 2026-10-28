import requests
import pandas as pd
from datetime import date
import numpy as np
from scipy.stats import norm

def rus_VaR_VC(x, s=None, e=None, VaR=95, log_returns=True, board="TQBR"):
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

    data = pd.concat(series, axis=1).sort_index()
    
    # Check if there are less than 100 observations
    if len(data) < 100:
        print("Insufficient number of observations.")
        return None
    
    # Calculate log returns if log_returns is True
    if log_returns:
        data = np.log(data / data.shift(1)).dropna()  # Log returns
    
    # Calculate means and standard deviations of the log returns
    MEAN = data.mean()
    SD = data.std()
    
    # Set up an empty DataFrame to store VaR values
    var_values = pd.DataFrame(index=data.columns, columns=[f"VaR VC {VaR}%"])
    
    # Calculate VaR using the Z-score from the normal distribution
    z_score = norm.ppf(1 - VaR * 0.01)  
    
    # Calculate VaR for each asset
    for col in data.columns:
        var_values.loc[col, f"VaR VC {VaR}%"] = MEAN[col] + z_score * SD[col]
    
    return var_values

rus_VaR_VC(x=["GAZP", "SBER"])
