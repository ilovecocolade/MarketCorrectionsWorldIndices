# RUNS AN OPTIMISER FOR MARKET CORRECTION STRATEGY PARAMETERS
# AUTHORS: JOHN ALLEN - john@fortunefinancialtechnologies.co.uk &&&& PATRICK-JAMES PORTER - !!!!EMAIL!!!!
# PROPERTY OF FORTUNE FINANCIAL TECHNOLOGIES - https://www.fortunefinancialtechnologies.co.uk

import pickle
import backtest
from datetime import datetime
import pytz
from zipline.api import symbol
import os
import pandas as pd
import shutil
import optimisers


# ADAPTED INITIALIZE FUNCTION TO SEQUENTIALLY READ IN NEW PARAMETERS FOR SINGLE POSITIONS
def optimize_initialize_single(context):

    # List of Major World Indices Yahoo tickers - https://finance.yahoo.com/world-indices
    with open('optimisation_tickers.pickle', 'rb') as handle:
        indices_tickers = pickle.load(handle)  # load in tickers from pickle

    context.indices = [symbol(ticker) for ticker in indices_tickers]  # create list of ticker symbols
    context.days_of_correction = [0 for _ in indices_tickers]  # create list of days since correction has begun

    # read in parameter dictionary
    with open('parameters.pickle', 'rb') as handle:
        parameters = pickle.load(handle)

    '''---------------------------------------------- PARAMETERS --------------------------------------------------'''
    context.correction_margin = parameters['correction_margin']  # the percentage drawdown considered a correction
    context.upturn_coefficient = parameters['upturn_coefficient']  # the ratio upturn from trough indicating end of correction
    context.min_return = parameters['min_return']  # the minimum return required before changing positions
    context.min_gain = parameters['min_gain']  # the highest the price can be from peak and still be considered for ordering
    context.stop_loss = parameters['stop_loss']  # lowest proportion of investment peak


def optimize_initialize_multiple(context):

    # List of Major World Indices Yahoo tickers - https://finance.yahoo.com/world-indices
    with open('optimisation_tickers.pickle', 'rb') as handle:
        indices_tickers = pickle.load(handle)  # load in tickers from pickle

    # read in parameter dictionary
    with open('parameters.pickle', 'rb') as handle:
        parameters = pickle.load(handle)

    context.indices = [symbol(ticker) for ticker in indices_tickers]  # create list of ticker symbols
    context.days_of_correction = [0 for _ in indices_tickers]  # create list of days since correction has begun

    '''-----------------------------PARAMETERS TO BE OPTIMISED--------------------------------'''
    context.correction_margin = parameters['correction_margin']  # the percentage drawdown considered a correction
    context.upturn_coefficient = parameters['upturn_coefficient']  # the ratio upturn from trough indicating end of correction
    context.min_gain = parameters['min_gain']  # the highest the price can be from peak and still be considered for ordering
    context.state_threshold = parameters['state_threshold']


# FUNCTION TO FORMAT AND SAVE OPTIMISATION RESULTS TO CSV
def format_results(results, optimize_directory, multiple=True):

    result_df = pd.DataFrame(data=results)  # create dataframe from results dictionary

    if multiple:

        result_df_returns = result_df[['mean_daily_return', 'alpha', 'correction_margin', 'upturn_coefficient', 'min_gain', 'state_threshold']]
        result_df_alpha = result_df[['alpha', 'mean_daily_return', 'correction_margin', 'upturn_coefficient', 'min_gain', 'state_threshold']]

    else:

        result_df_returns = result_df[['mean_daily_return', 'alpha', 'correction_margin', 'upturn_coefficient', 'min_return', 'min_gain', 'stop_loss']]
        result_df_alpha = result_df[['alpha', 'mean_daily_return', 'correction_margin', 'upturn_coefficient', 'min_return', 'min_gain', 'stop_loss']]

    result_df.to_pickle(optimize_directory + 'optimisation_results.pickle')  # pickle results

    # rank results by returns and alpha and save to csv files
    result_df_returns.sort_values('mean_daily_return', ascending=False).to_csv(optimize_directory + 'ranked_by_return.csv')
    result_df_alpha.sort_values('alpha', ascending=False).to_csv(optimize_directory + 'ranked_by_alpha.csv')


if __name__ == '__main__':

    # List of Major World Indices Yahoo tickers - https://finance.yahoo.com/world-indices
    indices_tickers = ['^GSPC', '^DJI', '^IXIC', '^NYA', '^XAX', '^BUK100P', '^RUT', '^FTSE', '^GDAXI', '^FCHI',
                       '^STOXX50E', '^N100', '^BFX', 'IMOEX.ME', '^N225', '^HSI', '000001.SS', '^STI', '^AXJO', '^AORD',
                       '^BSESN', '^JKSE', '^KLSE', '^NZ50', '^KS11', '^TWII', '^GSPTSE', '^BVSP', '^MXX', '^IPSA',
                       '^MERV', '^TA125.TA', '^CASE30', '^JN0U.JO']

    # pickle tickers
    with open('optimisation_tickers.pickle', 'wb') as handle:
        pickle.dump(indices_tickers, handle)

    panel = backtest.format_data(indices_tickers)  # format data for zipline backtests
    print('Data formatted for Zipline')

    '''-------------------------- TIMEFRAME & CAPITAL ---------------------------'''
    start = datetime(2000, 1, 1, 0, 0, 0, 0, pytz.utc)  # start of backtests
    end = datetime(2019, 12, 31, 0, 0, 0, 0, pytz.utc)  # end of backtests
    initial_capital = 10000000  # set starting capital for backtests

    # directory for storing optimisation results
    optimize_directory = 'Optimize_' + str(start.date()) + '_~_' + str(end.date()) + '_$' + str(initial_capital) + '/'

    if not os.path.exists(optimize_directory):  # determine if optimisation has already been completed for given time
        os.mkdir(optimize_directory)  # creates optimisation folder
    else:
        print('Optimisation already exists over given timeframe and capital base: ' + str(start.date()) + ' ~ ' + str(end.date()) + '  $' + str(initial_capital))
        input('Press <ENTER> to continue and overwrite current optimisation for this timeframe and capital base...')
        shutil.rmtree(optimize_directory)  # delete optimisation
        os.mkdir(optimize_directory)  # creates optimisation folder

    # RUN OPTIMISATION FUNCTION
    results = optimisers.monte_carlo(start, end, initial_capital, panel, random_timeframes=False, years=None, multiple=True)  # CHANGE OPTIMISATION TECHNIQUE HERE

    format_results(results, optimize_directory, multiple=True)  # format and save optimisation results

    os.remove('optimisation_tickers.pickle')  # delete tickers pickle file
