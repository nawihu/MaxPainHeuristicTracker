import requests
import json
import os
import wget
from pathlib import Path
import pandas as pd
from datetime import date
import pandas_datareader as pdr
from datetime import timedelta

today = pd.to_datetime(date.today()).strftime("%Y-%m-%d")
yesterday =pd.to_datetime(date.today()-timedelta(1)).strftime("%Y-%m-%d")


AlphaVandtageAPI="yours here"


#
# def last_close_contract_value(contract):

def get_last_adj_close(ticker):
    api_key = AlphaVandtageAPI

    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}'
    response = requests.get(url)
    data = json.loads(response.text)
    last_adj_close = float(data['Global Quote']['05. price'])
    # last_adj_close = 409.06
    print(f'{ticker} Last Adjusted Close: ${last_adj_close}')

    return last_adj_close

#TODO find out what time the site updates.
def retrive_oi_data(ticker):
    ticker = ticker.upper()
    output_dir = Path(f"tempdata/{ticker}")
    output_dir2 = Path(f"dataOutput/{ticker}_daily_OI")
    output_dir.mkdir(mode=0o755,parents=True, exist_ok=True)
    output_dir2.mkdir(mode=0o755,parents=True, exist_ok=True)
    if os.path.exists(f"tempdata/{ticker}/{today}_oi_dl.txt"):
        os.remove(f"tempdata/{ticker}/{today}_oi_dl.txt")
    if os.path.exists(f"tempdata/{ticker}/{today}_oi_dl_UNALTERED.txt"):
        os.remove(f"tempdata/{ticker}/{today}_oi_dl_UNALTERED.txt")
    wget.download(f"https://marketdata.theocc.com/series-search?symbolType=O&symbol={ticker}", f"tempdata/{ticker}/{today}_oi_dl.txt")
    wget.download(f"https://marketdata.theocc.com/series-search?symbolType=O&symbol={ticker}", f"tempdata/{ticker}/{today}_oi_dl_UNALTERED.txt")


def write_oi_data_to_csv(ticker):
    ticker = ticker.upper()
    with open(f"tempdata/{ticker}/{today}_oi_dl.txt", "r+") as infile:
        txt = infile.readlines()[6:]
        txt[0] = txt[0].replace("Position Limit", "PositionLimit")
        txt[0] = txt[0].replace("year", "Year")
        infile.seek(0)
        infile.writelines(txt)
        infile.truncate()

    with open(f"tempdata/{ticker}/{today}_oi_dl.txt", "r+") as infile:
        txt2 = infile.read().replace('\t\t','\t')
        infile.seek(0)
        infile.writelines(txt2)
        infile.truncate()

    oicsv = pd.read_table(f"tempdata/{ticker}/{today}_oi_dl.txt")
    oicsv.drop(oicsv.columns[6], axis=1, inplace=True)
    oicsv.drop(oicsv.columns[8], axis=1, inplace=True)
    oicsv.drop(oicsv.columns[8], axis=1, inplace=True)
    # oicsv.drop(oicsv.columns[0], axis=1, inplace=True)
    dec_as_float = oicsv["Dec"]
    float = dec_as_float/1000

    for value in oicsv["Integer"]:
        oicsv["Strike"] = oicsv["Integer"] + float
    oicsv["TotalOI"] = oicsv['Call'] + oicsv['Put']
    oicsv.drop("Integer", axis=1, inplace=True)
    oicsv.drop("Dec", axis=1, inplace=True)
    oicsv['ExpDate'] = oicsv['Year'].astype(str) + oicsv['Month'].astype(str).str.zfill(2) + oicsv['Day'].astype(str).str.zfill(2)
    oicsv["ExpDate"] = pd.to_datetime(oicsv["ExpDate"], format="%Y%m%d")
    oicsv["DateGen"] = today
    oicsv.drop(["Year"], axis=1,inplace=True)
    oicsv.drop(["Month"], axis=1,inplace=True)
    oicsv.drop(["Day"], axis=1,inplace=True)
    oicsv = oicsv.reindex(columns =["ProductSymbol","DateGen","ExpDate","Strike","Call","Put", "TotalOI"])
    oicsv.to_csv(f"dataOutput/{ticker}_daily_OI/{ticker}_{today}.csv", index_label="index")

### must be ran after 7am or somehting?  ###TODO figure out when and how to sync price and option oi data.  morning? noon?\

def calculate_maximum_pain(ticker):

    oicsv = pd.read_csv(f"dataOutput/{ticker}_daily_OI/{ticker}_{today}.csv")
    stock_price = get_last_adj_close(ticker)
    groups = oicsv.groupby('ExpDate')
    results = []
    print(stock_price)
    for exp_date, group in groups:
        print(exp_date)

        strikes = group['Strike'].unique()

      #pain is ITM puts/calls
        pain = []
        allPain = []
        calls = group.loc[group['Call'] >= 0, ["Strike",'Call']].set_index('Strike').to_dict()

        puts = group.loc[group['Put'] >= 0, ["Strike",'Put']].set_index('Strike').to_dict()


        # All_PC_Ratio =
        # Money_weighted_PC_Ratio =
        ALL_PC_Ratio = group["Put"].sum() / group['Call'].sum()

        for strike in strikes:
            print(strike)
            Allput = puts.get('Put', {}).get(strike, 0)

            Allcall = calls.get('Call', {}).get(strike, 0)
           ##get only ITM puts/calls
            if strike > stock_price:
                calls.get('Call').pop(float(strike))

                # print(calls)
                # print(stock_price)
            elif strike < stock_price:
                puts.get('Put').pop(float(strike))

            #specific call/put OI for the strike
            call = calls.get('Call', {}).get(strike, 0)
            put = puts.get('Put', {}).get(strike, 0)

            ##flipped sp and strike below.
            all_pain_value = (abs(strike - stock_price)) * (Allcall + Allput)
            allPain.append((strike, all_pain_value))
            ###TODO the error in max pain lies here, not taking the sum of all ITM callOI+PutOI.
            ### was * (call + put)
            pain_value = (abs(strike - stock_price)) * (calls.sum() + puts.sum())

            pain.append((strike, pain_value))


        print(calls)
        print(puts)
        ITM_PC_Ratio = group["Put"].sum() / group["Call"].sum()
        ###origninac.
        # ITM_PC_Ratio = group["Put"].sum() / group["Call"].sum()

        # print(f'ITM put/call ratio : {ticker} - {ITM_PC_Ratio}')
        max_allPain = max(allPain, key=lambda x: x[1])[0]
        max_pain = max(pain, key=lambda x: x[1])[0]
        date_gen = group['DateGen'].unique()[0]
        top_five_calls = group.loc[group['Call'] > 0].sort_values(by='Call', ascending=False).head(5)
        top_five_calls_dict = top_five_calls[['Strike', 'Call']].set_index('Strike').to_dict()['Call']
        highestTotalOI = group.loc[group['TotalOI'] > 0].sort_values(by='TotalOI', ascending=False).head(5)
        highestTotalOI_dict = highestTotalOI[['Strike', 'TotalOI']].set_index('Strike').to_dict()['TotalOI']
        top_five_puts = group.loc[group['Put'] > 0].sort_values(by='Put', ascending=False).head(5)
        top_five_puts_dict = top_five_puts[['Strike', 'Put']].set_index('Strike').to_dict()['Put']

        results.append({
            'DateGen': date_gen,
            'ExpDate': exp_date,
            'ITM Maximum Pain': max_pain,
            'All Maxpain' : max_allPain,
            'Top 5 Calls': top_five_calls_dict,
            'Top 5 Puts': top_five_puts_dict,
            'highestOIstrike': highestTotalOI_dict,
            'ITM P/C Ratio' : ITM_PC_Ratio,
            'All P/C Ratio' : ALL_PC_Ratio
        })
    oiDF = pd.DataFrame(results)
    directory = f"dataOutput/oi_mp_csvs/{ticker}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    oiDF.to_csv(f'dataOutput/oi_mp_csvs/{ticker}/{today}_{ticker}.csv')

