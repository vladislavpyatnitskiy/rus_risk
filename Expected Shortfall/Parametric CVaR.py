import requests
import pandas as pd
from datetime import date
import numpy as np
from scipy.stats import norm

def rus_CVaR_VC(x, s=None, e=None, es=95, log_returns=True, board="TQBR"):
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

    # Check whether there are less than 100 observations
    if len(p) < 100:
        print("Insufficient number of observations.")
        return
    
    # Calculate log returns if requested and remove NAs
    if log_returns:
        p = np.log(p / p.shift(1)).dropna()
    
    v = p.apply([np.mean, np.std], axis=0) # Means & Standard Deviations
    
    l = [] # Set up list to contain future values
    
    # Calculate VaR using standard normal probabilities
    for col in p.columns:
        MEAN = v.loc['mean', col]
        SD = v.loc['std', col]
        l.append(MEAN - (norm.pdf(norm.ppf(es * .01)) / (1 - es * .01)) * SD)
    
    # Return DataFrame with CVaR values
    return pd.DataFrame(l, index=p.columns, columns=[f"ES VC {es}%"])

rus_CVaR_VC(x=["GAZP", "SBER"])
