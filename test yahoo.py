import yfinance as yf
import pandas as pd
from datetime import datetime, date
from pathlib import Path
import numpy as np

##TODO for some reason, the last exp date was missing the #1 OI Put.

###TODO make sure this is runnign before market hours change options prices. can i get realtime?
###TODO maybe look for delta between my MP and mainstream MP sites, use that as edge.
###TODO something to check for errors, sometimes it makes OI=0 for some reason? timeout?idk
#TODO HIGHEST OI CALLS/PUTS BY DOLLAR VALUE.
YYMMDD = date.today().strftime("%y%m%d")
dategen = date.today().strftime("%Y-%m-%d")
print(YYMMDD)
tickerlist = open("Inputs/tickers_to_track.txt", "r")

for ticker in tickerlist:


    ticker = ticker.strip().upper()
    current_ticker = yf.Ticker(f'{ticker}')

    ticker_hist = current_ticker.history()
    merged_chain = []
###TODO NOTE --- YAHOO WILL USE THE ADJ. CLOSE FROM THURSDAY, IF RAN BEFORE MONDAY MARKET OPEN?
    last_adj_close = ticker_hist["Close"][-1]
    print(ticker)
    print(last_adj_close)
    # Get the expiration dates for the stock options
    expiration_dates = current_ticker.options

    # Loop through each expiration date
    for date in expiration_dates:

        # Get the option chain data for the current expiration date
        option_chain = current_ticker.option_chain(date)
        # Extract the put and call data
        puts = option_chain.puts
        calls = option_chain.calls
        puts['Puts_dollarsFromStrike'] = abs(puts['strike'] - last_adj_close)
        calls['Calls_dollarsFromStrike'] = abs(calls['strike'] - last_adj_close)

        puts['Puts_dollarsFromStrikeXoi'] = puts['Puts_dollarsFromStrike'] * puts['openInterest']
        calls['Calls_dollarsFromStrikeXoi'] = calls['Calls_dollarsFromStrike'] * calls['openInterest']
        calls['Calls_lastPriceXoi'] = calls['lastPrice'] * calls['openInterest']
        puts['Puts_lastPriceXoi'] = puts['lastPrice'] * puts['openInterest']

        # Filter for in-the-money options (inthemoney = True)
        # calls = calls[calls['inTheMoney']]
        # puts = puts[puts['inTheMoney']]
        merged = calls.merge(puts, on='strike', how='left')

        merged_chain.append(merged)

    data = pd.concat(merged_chain)
    data.rename(columns = {'inTheMoney_x':'CallInMoney','lastPrice_x':'CallLastPrice','lastPrice_y':'PutLastPrice','volume_x':'CallsVolume','volume_y':'PutsVolume', 'impliedVolatility_x':'CallIV', 'impliedVolatility_y':'PutIV', 'inTheMoney_y':'PutInMoney', 'openInterest_x':'CallsOI',
                           'openInterest_y':'PutsOI', 'strike':'Strike'}, inplace = True)

    data['TotalOI'] = data['CallsOI'] + data['PutsOI']
    maxpains = []
    # Extract the expiration date from the contractSymbol
    data['expirationDate_y'] = data['contractSymbol_y'].str[-15:-9]
    data['expirationDate_x'] = data['contractSymbol_x'].str[-15:-9]
    data['expirationDate'] = data['expirationDate_y'].fillna(data['expirationDate_x'])

    data['expirationDate'] = pd.to_datetime(data['expirationDate'], yearfirst=True)
    data.set_index(['expirationDate'], inplace=True)
    data = data[['Strike', 'CallsOI', 'CallsVolume', 'CallLastPrice', 'CallIV', 'CallInMoney', 'Calls_dollarsFromStrike', 'Calls_dollarsFromStrikeXoi', 'CallLastPrice','Calls_lastPriceXoi','PutsOI', 'PutsVolume', 'PutLastPrice', 'Puts_lastPriceXoi', 'PutIV', 'PutInMoney', 'Puts_dollarsFromStrike', 'Puts_dollarsFromStrikeXoi', 'PutLastPrice', 'TotalOI']]
    # print(data.columns)
    results = []
    data.to_csv("aaaaaa.csv")
    groups = data.groupby("expirationDate")
    #divide into groups by exp date, call info from group.
    for exp_date, group in groups:
        pain_list = []
        strike_LASTPRICExOI_list = []
        itmDFSxOI_list = []
        strike_DFSxOI_list = []
        strike = group['Strike']
        # pain is ITM puts/calls
        # for each strike, all all the dollar values of the puts beneath.
        calls_OI_dict = group.loc[group['CallsOI'] >= 0, ["Strike", 'CallsOI']].set_index('Strike').to_dict()
        puts_OI_dict = group.loc[group['PutsOI'] >= 0, ["Strike", 'PutsOI']].set_index('Strike').to_dict()
        calls_LASTPRICExOI_dict = group.loc[group['Calls_lastPriceXoi'] >= 0, ["Strike", 'Calls_lastPriceXoi']].set_index('Strike').to_dict()
        puts_LASTPRICExOI_dict =  group.loc[group['Puts_lastPriceXoi'] >= 0, ["Strike", 'Puts_lastPriceXoi']].set_index('Strike').to_dict()
        calls_DFSxOI_dict = group.loc[group['Calls_dollarsFromStrikeXoi'] >= 0, ["Strike", 'Calls_dollarsFromStrikeXoi']].set_index('Strike').to_dict()
        puts_DFSxOI_dict =  group.loc[group['Puts_dollarsFromStrikeXoi'] >= 0, ["Strike", 'Puts_dollarsFromStrikeXoi']].set_index('Strike').to_dict()
        itm_calls_OI_dict = group.loc[
            (group['Strike'] < last_adj_close) & (~group['CallsOI'].isnull()), ["Strike", 'CallsOI']].set_index(
            'Strike').to_dict()
        itm_puts_OI_dict = group.loc[
            (group['Strike'] > last_adj_close) & (~group['PutsOI'].isnull()), ["Strike", 'PutsOI']].set_index(
            'Strike').to_dict()
        ITM_CallsOI = group.loc[(group["Strike"] < last_adj_close), 'CallsOI'].sum()
        ITM_PutsOI = group.loc[(group["Strike"] > last_adj_close), 'PutsOI'].sum()
        # if ITM_CallsOI != 0 and not np.isnan(ITM_CallsOI):
        PC_Ratio = ITM_PutsOI / ITM_CallsOI
        # else:
            # PC_Ratio = np.nan
        # print(calls_OI_dict)
        # print(puts_OI_dict)
        # DFSxOI_dict = group.loc[group['Puts_dollarsFromStrikeXoi'] >= 0, ["Strike", 'Puts_dollarsFromStrikeXoi']].set_index('Strike').to_dict()
                              # print(puts_dict)
        # All_PC_Ratio =
        # Money_weighted_PC_Ratio =
    ###TODO figure out WHEN this needs to run... probalby after 6pm eastern and before mrkt open.  remove otm

        for strikeprice in strike:

            itmCalls_dollarsFromStrikeXoiSum = group.loc[(group["Strike"] < strikeprice), 'Calls_dollarsFromStrikeXoi'].sum()
            itmPuts_dollarsFromStrikeXoiSum = group.loc[(group["Strike"] > strikeprice), 'Puts_dollarsFromStrikeXoi'].sum()


            call_LASTPRICExOI = calls_LASTPRICExOI_dict.get("Calls_lastPriceXoi", {}).get(strikeprice, 0)
            put_LASTPRICExOI = puts_LASTPRICExOI_dict.get("Puts_lastPriceXoi", {}).get(strikeprice, 0)
            call_DFSxOI = calls_LASTPRICExOI_dict.get("Calls_dollarsFromStrikeXoi", {}).get(strikeprice, 0)
            put_DFSxOI = puts_LASTPRICExOI_dict.get("Puts_dollarsFromStrikeXoi", {}).get(strikeprice, 0)
            pain_value = itmPuts_dollarsFromStrikeXoiSum + itmCalls_dollarsFromStrikeXoiSum
            pain_list.append((strikeprice, pain_value))
            strike_LASTPRICExOI = call_LASTPRICExOI + put_LASTPRICExOI
            strike_LASTPRICExOI_list.append((strikeprice, strike_LASTPRICExOI))
            strike_DFSxOI = call_DFSxOI + put_DFSxOI
            strike_DFSxOI_list.append((strikeprice, strike_DFSxOI))


        # print(f'ITM put/call ratio : {ticker} - {ITM_PC_Ratio}')
        # ITM_PC_Ratio = group["Put"].sum() / group["Call"].sum()

        highest_premium_strike = max(strike_LASTPRICExOI_list, key=lambda x: x[1])[0]
        max_pain = min(pain_list, key=lambda x: x[1])[0]
        max_DFSxOI = max(strike_DFSxOI_list, key=lambda x: x[1])[0]

        top_five_calls = group.loc[group['CallsOI'] > 0].sort_values(by='CallsOI', ascending=False).head(5)
        top_five_calls_dict = top_five_calls[['Strike', 'CallsOI']].set_index('Strike').to_dict()['CallsOI']
        highestTotalOI = group.loc[group['TotalOI'] > 0].sort_values(by='TotalOI', ascending=False).head(2)
        highestTotalOI_dict = highestTotalOI[['Strike', 'TotalOI']].set_index('Strike').to_dict()['TotalOI']
        top_five_puts = group.loc[group['PutsOI'] > 0].sort_values(by='PutsOI', ascending=False).head(5)
        top_five_puts_dict = top_five_puts[['Strike', 'PutsOI']].set_index('Strike').to_dict()['PutsOI']

        results.append({

            'ExpDate': exp_date,
            'Maximum Pain': max_pain,
            ###TODO divide into highest premium calls/puts.
            'Highest Premium Strike' : highest_premium_strike,
            'Highest DFSxOI Strike' : max_DFSxOI,
            'Top 2 OI Strikes': highestTotalOI_dict,
            'ITM P/C Ratio': PC_Ratio,
            'Top 5 ITM OI Calls': sorted(itm_calls_OI_dict["CallsOI"].items(), key=lambda item: item[1], reverse=True)[:5],
            'Top 5 ITM OI Puts': sorted(itm_puts_OI_dict["PutsOI"].items(), key=lambda item: item[1], reverse=True)[:5],
            'Top 5 OI Calls': top_five_calls_dict,
            'Top 5 OI Puts': top_five_puts_dict,

        })

    df = pd.DataFrame(results)
    output_dir = Path(f'dataOutput/{ticker}/dailydata')
    output_dir.mkdir(mode=0o755,parents=True, exist_ok=True)
    df.to_csv(f'dataOutput/{ticker}/dailydata/testyahoo{YYMMDD}.csv')






