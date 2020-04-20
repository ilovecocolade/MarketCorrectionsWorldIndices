# MARKET CORRECTION STRATEGY FOR SINGLE POSITIONS
# AUTHORS: JOHN ALLEN - john@fortunefinancialtechnologies.co.uk &&&& PATRICK-JAMES PORTER - !!!!EMAIL!!!!
# PROPERTY OF FORTUNE FINANCIAL TECHNOLOGIES - https://www.fortunefinancialtechnologies.co.uk

# ALPHA VANTAGE API KEY:  2R17ZP8N3L08HBF9 (use for getting data)

# TO BACKTEST USING COMMAND LINE INTERFACE:
# zipline run -f strategy_single_position.py --start YYYY-D-M --end YYYY-D-M -output correction_backtest.pickle


from zipline.api import order_target_percent, record, symbol, set_benchmark, get_open_orders
import pickle
import os


# ZIPLINE INITIALIZE FUNCTION (runs once at start of backtest)
def initialize(context):

    # List of Major World Indices Yahoo tickers - https://finance.yahoo.com/world-indices
    with open('tickers.pickle', 'rb') as handle:
        indices_tickers = pickle.load(handle)  # load in tickers from pickle

    os.remove('tickers.pickle')  # delete tickers pickle file

    context.indices = [symbol(ticker) for ticker in indices_tickers]  # create list of ticker symbols
    context.days_of_correction = [0 for _ in indices_tickers]  # create list of days since correction has begun
    set_benchmark(symbol('^GSPC'))

    '''-----------------------------PARAMETERS TO BE OPTIMISED--------------------------------'''
    context.correction_margin = 0.1  # the percentage drawdown considered a correction
    print('Drawdown percentage range from peak for correction: ' + str(round(context.correction_margin*100)) + '%')
    context.upturn_coefficient = 0.22  # the ratio upturn from trough indicating end of correction - used in calculate_required_upturn function
    print('Upturn Coefficient: ' + str(round(context.upturn_coefficient, 2)))
    context.min_return = 0.26  # the minimum return required before changing positions
    print('Minimum return per trade: ' + str(round(context.min_return*100)) + '%')
    context.min_gain = 0.07  # the highest the price can be from peak and still be considered for ordering
    print('Mainimum potential gain from peak to be considered: ' + str(round(context.min_gain*100, 0)) + '%')
    context.stop_loss = 0.53  # lowest proportion of investment peak
    print('Stop loss for investments: ' + str(round(context.stop_loss*100)) + '%')


# ZIPLINE HANDLE_DATA FUNCTION (runs according to data frequency set for backtest variable assignment)
def handle_market_corrections(context, data):

    # create list of each ticker for last 300 days price and get the data for correcting indices since the correction start
    history = [data.history(context.indices[i], 'price', 500, '1d') for i in range(len(context.indices))]
    correction_history = [data.history(context.indices[i], 'price', context.days_of_correction[i], '1d') if context.days_of_correction[i] > 0 else 0 for i in range(len(context.indices))]

    # create lists of troughs, peaks and todays prices
    troughs = [correction_history[i].min() if type(correction_history[i]) != int else -1 for i in range(len(context.indices))]
    peaks = [history[i].max() for i in range(len(context.indices))]
    prices = [history[i][-1] for i in range(len(context.indices))]

    # determine number of and price of shares held for each index
    no_of_shares = [context.portfolio.positions[index].amount for index in context.indices]

    if sum(no_of_shares) > 0:  # if we have an open position

        # get prices since investment
        investment_prices = data.history(context.bought_symbol, 'price', context.days_since_investment, '1d')
        peak_investment_price = max(investment_prices)  # determine peak price of investment

    # create list to identify correcting indices and update the days since corrections
    corrections = [1-(peaks[i]-prices[i])/peaks[i] if prices[i] <= peaks[i]*(1-context.min_gain) and troughs[i] <= (1-context.correction_margin)*peaks[i] else -1 for i in range(len(context.indices))]
    context.days_of_correction = [days+1 if corrections[i] > 0 else 0 for i, days in enumerate(context.days_of_correction)]

    # create list to identify increase from trough of correction (percentage change from trough)
    upturns = [(prices[i]-troughs[i])/troughs[i] if troughs[i] > 0 and prices[i] >= calculate_required_upturn(peaks[i], troughs[i], context.upturn_coefficient)*troughs[i] else -1 for i in range(len(context.indices))]

    # if there exists at least one upturning index
    if max(upturns) > 0 and len(get_open_orders()) == 0:
        # determine rank of positions and their list locations
        ranked_symbols, ranked_symbol_indices = determine_best_position(peaks, prices, upturns, context.indices)

        for i, symbol in enumerate(ranked_symbols):   # iterate through symbol ranking

            # check if there are no open positions
            if sum(no_of_shares) == 0:
                order_target_percent(symbol, 1.0)  # order best position with 100% of portfolio value
                context.bought_symbol = symbol  # save the bought symbol
                context.buy_price = prices[ranked_symbol_indices[i]]  # save buy_price
                context.bought_list_index = ranked_symbol_indices[i]  # save list index of bought symbol
                context.days_since_investment = 1  # initialise number of days investment has been held
                break

            # OTHERWISE, if we are not currently holding the best index and have met the minimum return requirement per position and can afford to buy
            elif symbol is not context.bought_symbol and (prices[context.bought_list_index]/context.buy_price >= context.min_return+1 or prices[context.bought_list_index] < context.stop_loss*peak_investment_price) and prices[ranked_symbol_indices[i]] < context.portfolio.portfolio_value and symbol not in get_open_orders():
                order_target_percent(context.bought_symbol, 0.0)  # neutralise current position
                order_target_percent(symbol, 1.0)  # order best position with 100% of portfolio value
                context.bought_symbol = symbol  # save the bought symbol
                context.buy_price = prices[ranked_symbol_indices[i]]  # save buy_price
                context.bought_list_index = ranked_symbol_indices[i]  # save list index of bought symbol
                context.days_since_investment = 1  # initialise number of days investment has been held
                break

            elif symbol is context.bought_symbol:  # if the current position is the best position stop looking through ranking
                context.days_since_investment += 1  # add one to number of days since has been held
                break

    elif sum(no_of_shares) > 0:  # if we have an open position
        context.days_since_investment += 1  # add one to number of days since has been held

        # if investment drops below stop loss
        if prices[context.bought_list_index] < context.stop_loss * peak_investment_price and context.bought_symbol not in get_open_orders():
            order_target_percent(context.bought_symbol, 0.0)  # neutralise position


# FUNCTION TO CALCULATE THE REQUIRED RETURN BASED ON THE TROUGH, PEAK AND UPTURN COEFFICIENT
def calculate_required_upturn(peak, trough, upturn_coefficient):

    required_upturn = 1 + (((upturn_coefficient * 100 * ((peak-trough)/peak)) ** 2) / 100)

    return required_upturn


# FUNCTION TO DETERMINE THE CORRECTING INDEX WITH THE BEST POTENTIAL RETURN
# Calculated by determining the index ENDING its correction with LARGEST potential gain at current price
# potential gain is measured by taking the difference between the ending correction indices peak and price
def determine_best_position(peaks, prices, upturns, indices):

    # determine potential gains for each upturning index
    potential_gains = [(peaks[i]-prices[i]/prices[i]) if upturns[i] > 0 else -1 for i in range(len(prices))]
    shortened_gains = [gain for gain in potential_gains if gain > 0]  # remove indices with insufficient gain
    ranked_gains = sorted(shortened_gains, reverse=True)  # rank gains from highest to lowest
    ranked_symbol_indices = [potential_gains.index(ranked_gain) for ranked_gain in ranked_gains]  # determine index in list of best potential gain
    ranked_symbols = [indices[ranked_symbol_index] for ranked_symbol_index in ranked_symbol_indices]  # determine symbol with best potential gain

    return ranked_symbols, ranked_symbol_indices  # return the best symbol and its associated list index


