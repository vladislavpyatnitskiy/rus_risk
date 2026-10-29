import numpy as np
import pandas as pd
import requests
from datetime import date

def histCVaR_rus(x, s=None, e=None, CVaR=95, log_returns=True, board="TQBR"):
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
        print("Error. Insufficient number of observations.")
        return None
    
    # Calculate log returns if log_returns is True
    if log_returns:
        data = np.log(data / data.shift(1)).dropna()  # Log returns
    
    ES = [] # Initialize an empty list to store CVaR values
    
    # Loop through each column (asset) in the DataFrame
    for col in data.columns:
        sorted_returns = data[col].sort_values(ascending=True)  # Sort returns
        
        # Select the worst (1 - CVaR%) returns and calculate their mean
        cutoff = int((1-CVaR*.01)*len(sorted_returns))
        worst_returns = sorted_returns.iloc[:cutoff]
        
        # Calculate the mean of the worst returns (Expected Shortfall)
        ES.append(worst_returns.mean())
    
    # Create a DataFrame to display CVaR values for each column
    return pd.DataFrame(ES, index=data.columns, columns=[f"CVaR {CVaR}%"])

histCVaR_rus(x=["GAZP", "SBER"])
