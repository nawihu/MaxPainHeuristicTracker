import pandas
import operations as op
import openinterestapi as oi


tickerlist = "spy"
    # open("Inputs/tickers_to_track.txt", "r")




ticker = tickerlist.strip().upper()

oi.retrive_oi_data(ticker)
oi.write_oi_data_to_csv(ticker)
oi.calculate_maximum_pain(ticker)

# display OI(5 callOI and 5 PUToi), Max Pain?, previous close date generated?
#or a dataframe?
# think i need big nested dict for all data
# for each date in exp dates, take top 5 callOI and respective strikes as dict?
# dict = {"dategen":{expdate:{strike}}}

tickerlist.close()