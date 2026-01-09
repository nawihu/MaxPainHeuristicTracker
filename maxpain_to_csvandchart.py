import glob
from datetime import datetime
import pandas as pd

import datetime_operations
import operations
import matplotlib.pyplot as plt
import data_scraper
from pathlib import Path


tickerlist = open("Inputs/tickers_to_track.txt", "r")
getMP = data_scraper.DataScraper()

#used to change date format.


for ticker in tickerlist.readlines():
    data = []
    ticker = ticker.strip().upper()
    getMP.get_mpdata(ticker)
    dailyCSVentries = glob.glob(f'dataOutput/daily_selenium_scrapedMP/{ticker}_Daily_CSVs/*.csv')

    for csv in dailyCSVentries:
        df = pd.read_csv(csv)
        data.append(df)

    bigframe = pd.concat(data, sort=False, ignore_index=True)
    bigframe.set_index('maturitydate',  inplace=True)
    bigframe.columns = pd.to_datetime(bigframe.columns, format='%m/%d/%y')
    bigframe.index = pd.to_datetime(bigframe.index, format='%m/%d/%y')
    bigframe = bigframe.reindex(sorted(bigframe.index))
    # I couldn't figure out how to sort the columns by value without transposing to index.
    bigframe = bigframe.transpose()
    bigframe = bigframe.reindex(sorted(bigframe.index))

 #def add_close_to_mp_csv
    #creates a list of dates to use for determining if the strike has passed, and appending actual close in the cell to the right of a passed contract exp. date.
    listofmatchingdates = [pd.to_datetime(c, format='%m/%d/%y').strftime("%Y/%m/%d") for c in bigframe.columns if c in bigframe.index]
    today_datetime = datetime.today().strftime("%Y/%m/%d")
## This part is here to ensure I'm not trying to pull closing data from a day in progress.
    if today_datetime in listofmatchingdates:
        listofmatchingdates.remove(today_datetime)
#TODO As it stands, if i miss a day of scraping, close will never be popoulated for the day before.
    listofmatchingdates_backslash = [datetime_operations.swap_backslash(i) for i in listofmatchingdates]
    bigframe.index = pd.to_datetime(bigframe.index, format='%m/%d/%y').strftime("%m/%d/%y")
    bigframe.columns = pd.to_datetime(bigframe.columns, format='%m/%d/%y').strftime("%m/%d/%y")
    tickerhist = operations.RetrieveYFData(f"{ticker}")


    for a in listofmatchingdates_backslash:

        a = f"{a}"
        b = (datetime.strptime(a, '%Y-%m-%d').strftime("%m/%d/%y"))
        closingprice = '{:,.2f}'.format(tickerhist.get_closing_price(a))
        indexvalue = (bigframe.columns.get_loc(b)) + 1
        columnvalue = (bigframe.index.get_loc(b))
        bigframe.iat[columnvalue, indexvalue] = closingprice

# def make_mp_csv():
    output_dir = Path('dataOutput/')
    output_dir2 = Path('dataOutput/graphs/staggered_mp/')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir2.mkdir(parents=True, exist_ok=True)
    bigframe.to_csv(f"dataoutput/{ticker}maxpain.csv")


#def plot_mp_chart():
    bigframe = bigframe.astype(float)
    chart1 = bigframe.plot(alpha=.3, loglog=False, lw=3, colormap='prism', marker='.', linestyle="dotted", markersize=10, title=f'{ticker} Heuristic staggered MaxPain')
    chart1.set_xlabel("Exp. Date")
    chart1.set_ylabel("Price $$$")
    plt.xticks(range(len(bigframe.index)), bigframe.index, rotation=90)
    # ticks=range(len(bigframe)),
    plt.legend(title="Date Gen.")
    plt.show()
    plt.savefig(f"dataOutput/graphs/staggered_mp/{ticker}_sMP_graph")

tickerlist.close()

