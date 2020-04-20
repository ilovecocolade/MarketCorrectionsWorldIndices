# MARKET CORRECTION STRATEGY FOR MULTIPLE POSITIONS
# AUTHORS: JOHN ALLEN - john@fortunefinancialtechnologies.co.uk &&&& PATRICK-JAMES PORTER - !!!!EMAIL!!!!
# PROPERTY OF FORTUNE FINANCIAL TECHNOLOGIES - https://www.fortunefinancialtechnologies.co.uk

# ALPHA VANTAGE API KEY:  2R17ZP8N3L08HBF9 (use for getting data)

# TO BACKTEST USING COMMAND LINE INTERFACE:
# zipline run -f strategy_single_position.py --start YYYY-D-M --end YYYY-D-M -output correction_backtest.pickle


from zipline.api import symbol, set_benchmark, get_open_orders, set_commission
from zipline.api import order as Order
from zipline.finance import commission
import pickle
import math
import os
import numpy as np


# ZIPLINE INITIALIZE FUNCTION (runs once at start of backtest)
def initialize(context):

    # List of Major World Indices Yahoo tickers - https://finance.yahoo.com/world-indices
    with open('tickers.pickle', 'rb') as handle:
        indices_tickers = pickle.load(handle)  # load in tickers from pickle

    os.remove('tickers.pickle')  # delete tickers pickle file

    context.indices = [symbol(ticker) for ticker in indices_tickers]  # create list of ticker symbols
    set_benchmark(symbol('^GSPC'))
    set_commission(commission.PerTrade(cost=15.0))  # commission for IBKR, UK for Stocks, ETF's & Warrants - https://www.interactivebrokers.co.uk/en/index.php?f=39753&p=stocks1

    '''-----------------------------PARAMETERS TO BE OPTIMISED--------------------------------'''
    context.correction_margin = 0.05  # the percentage drawdown considered a correction
    print('Drawdown percentage range from peak for correction: ' + str(round(context.correction_margin*100)) + '%')
    context.upturn_coefficient = 0.0727  # the ratio upturn from trough indicating end of correction - used in calculate_required_upturn function
    print('Upturn Coefficient: ' + str(round(context.upturn_coefficient, 4)))
    context.min_gain = -0.05  # the highest the price can be from peak and still be considered for ordering
    print('Mainimum potential gain from peak to be considered: ' + str(round(context.min_gain*100, 0)) + '%')
    context.state_threshold = -10.0  # 0.0002 threshold between bull and bear markets
    print('Market state threshhold: ' + str(round(context.state_threshold, 4)) + '%')


# ZIPLINE HANDLE_DATA FUNCTION (runs according to data frequency set for backtest variable assignment)
def handle_market_corrections(context, data):

    bar_days = 500  # number of previous prices

    # create list of each ticker for last prices and get the data for correcting indices since the correction start
    history = [data.history(context.indices[i], 'price', bar_days, '1d') for i in range(len(context.indices))]

    # calculate average weekly prices across all indices to determine market direction
    '''first_week = [sum([(history[i][-7+n]-history[i][-8+n])/history[i][-8+n] for n in range(7)])/7 for i in range(len(context.indices)) if not math.isnan(history[i][-29])]
    second_week = [sum([(history[i][-14+n]-history[i][-15+n])/history[i][-15+n] for n in range(7)])/7 for i in range(len(context.indices)) if not math.isnan(history[i][-29])]
    third_week = [sum([(history[i][-21+n]-history[i][-22+n])/history[i][-22+n] for n in range(7)])/7 for i in range(len(context.indices)) if not math.isnan(history[i][-29])]
    fourth_week = [sum([(history[i][-28+n]-history[i][-29+n])/history[i][-29+n] for n in range(7)])/7 for i in range(len(context.indices)) if not math.isnan(history[i][-29])]'''

    # determine previous 5 day average for consideration
    five_prev_days_avg = [sum([(history[i][-10+n]-history[i][-11+n])/history[i][-11+n] for n in range(10)])/10 if not math.isnan(history[i][-10]) else -99.9 for i in range(len(context.indices))]

    # average across all indices currently available
    '''first_week = sum(first_week) / len(first_week)
    second_week = sum(second_week) / len(second_week)
    third_week = sum(third_week) / len(third_week)
    fourth_week = sum(fourth_week) / len(fourth_week)'''

    # add line for individual index states (bear or bull)
    # consider = [True if first_week[i] > context.state_threshold and second_week[i] > context.state_threshold and third_week[i] > context.state_threshold and fourth_week[i] > context.state_threshold and first_week != 999.9 else False for i in range(len(context.indices))]
    consider = [True if five_prev_days_avg[i] > context.state_threshold else False for i in range(len(context.indices))]

    # create lists of peaks and todays prices
    prices = [history[i][-1] for i in range(len(context.indices))]
    peaks = [history[i].max() for i in range(len(context.indices))]

    # determine the number of days since the peak for each index
    reset_history = [history[i].reset_index(drop=True) for i in range(len(context.indices))]
    days_since_peaks = [bar_days - max(np.where(reset_history[i] == peaks[i])[0]) if not math.isnan(history[i][-1]) else -1 for i in range(len(context.indices))]

    # determine the trough since the peak for each index
    # troughs = [data.history(context.indices[i], 'price', int(days_since_peaks[i]), '1d').min() if days_since_peaks[i] > 0 else -1 for i in range(len(context.indices))]
    troughs = [history[i][-days_since_peaks[i]:].min() if days_since_peaks[i] > 0 else -1 for i in range(len(context.indices))]

    # determine number of and price of shares held for each index
    no_of_shares = [context.portfolio.positions[index].amount for index in context.indices]

    # create list to identify correcting indices
    corrections = [1-(peaks[i]-prices[i])/peaks[i] if prices[i] <= peaks[i]*(1-context.min_gain) and 0 < troughs[i] <= (1-context.correction_margin)*peaks[i] else -1 for i in range(len(context.indices))]

    # create list to identify increase from trough of correction (percentage change from trough)
    upturns = [(prices[i]-troughs[i])/troughs[i] if corrections[i] > 0 and prices[i] >= calculate_required_upturn(peaks[i], troughs[i], context.upturn_coefficient)*troughs[i] else -1 for i in range(len(context.indices))]

    # if the market is bear
    '''if first_week < context.state_threshold and second_week < context.state_threshold and third_week < context.state_threshold and fourth_week < context.state_threshold:

        for position in context.portfolio.positions.keys():  # iterate through all open positions
            order_target_percent(position, 0)  # neutralize all open positions'''

    # if there exists at least one upturning index and no open orders
    if max(upturns) > 0 and len(get_open_orders()) == 0:

        order_stack(peaks, prices, upturns, context.indices, context, no_of_shares, consider)  # order optimal stacked portfolio


# FUNCTION TO CALCULATE THE REQUIRED RETURN BASED ON THE TROUGH, PEAK AND UPTURN COEFFICIENT
def calculate_required_upturn(peak, trough, upturn_coefficient):

    required_upturn = 1 + (((upturn_coefficient * 100 * ((peak-trough)/peak)) ** 2) / 100)

    return required_upturn


# FUNCTION TO DETERMINE THE CORRECTING INDEX WITH THE BEST POTENTIAL RETURN
# Calculated by determining the index ENDING its correction with LARGEST potential gain at current price
# potential gain is measured by taking the difference between the ending correction indices peak and price
def determine_best_positions(peaks, prices, upturns, indices, consider):

    # determine potential gains for each upturning index ~ and consider[i] is True ~ ADD TO POTENTIAL GAINS LIST COMPREHENSION FOR INDIVIDUAL INDICES STATES
    potential_gains = [(peaks[i]-prices[i]/prices[i]) if upturns[i] > 0 and consider[i] is True else -1 for i in range(len(prices))]
    shortened_gains = [gain for gain in potential_gains if gain > 0]  # remove indices with insufficient gain
    ranked_gains = sorted(shortened_gains, reverse=True)  # rank gains from highest to lowest
    ranked_symbol_indices = [potential_gains.index(ranked_gain) for ranked_gain in ranked_gains]  # determine index in list of best potential gain
    ranked_symbols = [indices[ranked_symbol_index] for ranked_symbol_index in ranked_symbol_indices]  # determine symbol with best potential gain

    return ranked_symbols, ranked_symbol_indices  # return the best symbol and its associated list index


# FUNCTION TO DETERMINE OPTIMAL PORTFOLIO ACCORDING TO STACKED SHARES
def stack_portfolio(peaks, prices, upturns, context, consider):

    ranked_symbols, ranked_symbol_indices = determine_best_positions(peaks, prices, upturns, context.indices, consider)  # get position ranking

    ranked_prices = [prices[symbol_index] for symbol_index in ranked_symbol_indices]
    symbol_orders = [0 for _ in prices]  # initialise order list

    if len(ranked_symbols) == 0:  # if there are no potential positions
        return symbol_orders  # return orders of 0 for all symbols

    else:  # if there are potential positions

        value = context.portfolio.portfolio_value  # set value variable
        i = 0  # set counter to 0

        while value > min(ranked_prices):  # iterate through symbol ranking

            if prices[ranked_symbol_indices[i]] < value:  # determine if the price is less than our current disposable value

                symbol_orders[ranked_symbol_indices[i]] += 1  # add one to order
                value -= math.ceil(prices[ranked_symbol_indices[i]])  # take away price from value

            if i < len(ranked_symbols) - 1:  # if we are not at the end of ranking
                i += 1  # increase counter by 1
            else:  # if end of ranking has been reached
                i = 0  # set counter to 0

    return symbol_orders  # return the orders to be issued


# FUNCTION TO ISSUE ORDERS TO REACH OPTIMAL PORTFOLIO
def order_stack(peaks, prices, upturns, indices, context, no_of_shares, consider):

    stack = stack_portfolio(peaks, prices, upturns, context, consider)  # determine optimal stack
    orders = [0 for _ in prices]  # initialise order share amounts

    for i, shares in enumerate(stack):  # iterate through stack for sells

        orders[i] = shares - no_of_shares[i]  # determine the order amount

        if orders[i] < 0:  # if the order is a SELL

            Order(context.indices[i], orders[i])  # execute sell order

    for i, order in enumerate(orders):  # iterate through stack for buys

        if order > 0:  # if the order amount is positive

            Order(indices[i], order)  # execute buys
