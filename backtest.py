# BACKTEST OF MARKET CORRECTION STRATEGY
# AUTHORS: JOHN ALLEN - john@fortunefinancialtechnologies.co.uk &&&& PATRICK-JAMES PORTER - !!!!EMAIL!!!!
# PROPERTY OF FORTUNE FINANCIAL TECHNOLOGIES - https://www.fortunefinancialtechnologies.co.uk

import zipline
import pandas as pd
import pandas_datareader.data as web
import datetime as dt
import os
import fix_yahoo_finance
import pytz
from collections import OrderedDict
import shutil
import analysis  # import analysis script
import time
import strategy_single_position
import strategy_multiple_positions
import strategy_multiple_positions_Counter
import pickle


fix_yahoo_finance.pdr_override()  # override DataReader function (yahoo finance fix)


# FUNCTION TO GENERATE FOLDER OF CSV FILES FOR YAHOO MAJOR WORLD INDICES
def get_index_data(tickers, start, end, csv_directory):

    os.mkdir(csv_directory)  # create folder for index data

    # Save ticker data to .csv files
    for ticker in tickers:
        # attempt to get ticker data from yahoo
        try:
            # get ticker data from Yahoo finance
            ticker_data = web.get_data_yahoo(ticker, start, end)
            ticker_data.to_csv(csv_directory + '{}.csv'.format(ticker))  # save data to csv
            print(ticker)  # print ticker when data is saved
        except:
            print('Error fetching data from yahoo for {}'.format(ticker))


# FUNCTION TO FORMAT DATA FOR ZIPLINE BACKTEST
def format_data(indices_tickers):

    indices_data = OrderedDict()  # initialize dictionary to store dataframes for each ticker

    # if index data is not already saved locally, get it for corresponding time frame
    csv_directory = 'World_indices_data/'
    if not os.path.exists(csv_directory):
        get_index_data(indices_tickers, dt.datetime(1985, 1, 1), dt. datetime.now(),
                       csv_directory)  # set time frame for data here
    else:
        print('Indices data folder already exists')

    # organise ticker data to open-high-low-close-volume
    for ticker in indices_tickers:
        indices_data[ticker] = pd.read_csv(csv_directory + '{}.csv'.format(ticker), index_col=0, parse_dates=['Date'])  # read csv file
        indices_data[ticker] = indices_data[ticker][['Open', 'High', 'Low', 'Close', 'Volume']]  # swap columns to DateOHLCV

        # Correct for instances of zero volume
        for i, vol in enumerate(indices_data[ticker]['Volume']):
            if vol <= 0:  # if the volume value is 0 or negative
                indices_data[ticker].loc[indices_data[ticker].index[i], 'Volume'] = 10000000  # amend volume

    panel = pd.Panel(indices_data)  # create 'data panel' (3D dataframe)
    panel.minor_axis = ['open', 'high', 'low', 'close', 'volume']  # set minor axis headers to OHLCV
    panel.major_axis = panel.major_axis.tz_localize(pytz.utc)  # localise time on major axis to UTC zone

    return panel  # return data panel


if __name__ == '__main__':

    # List of Major World Indices Yahoo tickers - https://finance.yahoo.com/world-indices
    indices_tickers = ['^GSPC', '^DJI', '^IXIC', '^NYA', '^XAX', '^BUK100P', '^RUT', '^FTSE', '^GDAXI', '^FCHI',
                       '^STOXX50E', '^N100', '^BFX', 'IMOEX.ME', '^N225', '^HSI', '000001.SS', '^STI', '^AXJO', '^AORD',
                       '^BSESN', '^JKSE', '^KLSE', '^NZ50', '^KS11', '^TWII', '^GSPTSE', '^BVSP', '^MXX', '^IPSA',
                       '^MERV', '^TA125.TA', '^CASE30', '^JN0U.JO']

    # pickle parameter dictionary
    with open('tickers.pickle', 'wb') as handle:
        pickle.dump(indices_tickers, handle)

    panel = format_data(indices_tickers)  # format data for zipline backtest
    print('Data formatted for Zipline')

    '''------------------------------------ RUN BACKTEST ------------------------------------'''
    start = dt.datetime(2000, 1, 1, 0, 0, 0, 0, pytz.utc)  # start of backtest
    end = dt.datetime(2019, 12, 31, 0, 0, 0, 0, pytz.utc)  # end of backtest
    initial_capital = 1000000  # set starting capital for backtest

    # create folder to save spreadsheet and pickled backtest dataframe
    backtest_directory = 'Backtest_' + str(start.date()) + '_~_' + str(end.date()) + '_$' + str(initial_capital) + '/'

    if not os.path.exists(backtest_directory):  # determine if backtest has already been completed for given time
        os.mkdir(backtest_directory)  # creates backtest folder
    else:
        print('Backtest already exists over given timeframe and capital base: ' + str(start.date()) + ' ~ ' + str(end.date()) + '  $' + str(initial_capital))
        input('Press <ENTER> to continue and overwrite current backtest for this timeframe and capital base...')
        shutil.rmtree(backtest_directory)  # delete backtest
        os.mkdir(backtest_directory)  # creates backtest folder

    timer = time.time()  # initialise timer

    performance = zipline.run_algorithm(start=start,  # start
                                        end=end,  # end
                                        initialize=strategy_multiple_positions_Counter.initialize,  # initialize function
                                        capital_base=initial_capital,  # initial capital
                                        handle_data=strategy_multiple_positions_Counter.handle_market_corrections,  # handle_data function
                                        data=panel)  # data to test against

    print('SIMULATION TIME : ' + str(dt.timedelta(seconds=round((time.time() - timer), 0))))  # print elapsed time

    backtest_spreadsheet = 'spreadsheet.csv'
    performance.to_csv(backtest_directory + backtest_spreadsheet)  # save backtest results to csv
    performance.to_pickle(backtest_directory + 'backtest.pickle')  # pickle backtest dataframe
    print('Backtest saved to CSV file: ' + backtest_spreadsheet)

    analysis.backtest_analysis(backtest=performance, start=start.date(), end=end.date(), capital=initial_capital)  # run analysis on backtest