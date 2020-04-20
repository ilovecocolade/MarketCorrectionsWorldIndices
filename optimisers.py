# OPTIMISATION METHODS FOR MARKET CORRECTION STRATEGY PARAMETERS
# AUTHORS: JOHN ALLEN - john@fortunefinancialtechnologies.co.uk &&&& PATRICK-JAMES PORTER - !!!!EMAIL!!!!
# PROPERTY OF FORTUNE FINANCIAL TECHNOLOGIES - https://www.fortunefinancialtechnologies.co.uk

import pickle
import zipline
import optimize
import strategy_single_position
import strategy_multiple_positions
import os
import numpy as np
import math
import random
import pandas as pd
import datetime
import time
import pytz


# FUNCTION TO RUN OPTIMISATION OF PARAMETERS -- EXHAUSTIVE SEARCH
def exhaustive_search(start, end, initial_capital, panel, random_timeframes=False, years=5, multiple=True):

    first = True  # indicate the first test of parameter sets
    multiple = True  # MULTIPLE POSITION STRATEGY

    '''---------------------------- SET OF PROPOSED PARAMETER VALUES TO BE OPTIMISED ------------------------'''
    correction_margins = [0.1]  # the percentage drawdown considered a correction
    upturn_coefficients = np.arange(0.05, 0.5, 0.01)  # the ratio upturn from trough indicating end of correction
    min_gains = [0.05]  # the highest the price can be from peak and still be considered for ordering

    if not multiple:  # include min return and stop loss if not using multi positions

        min_returns = [0.02]  # the minimum return required before changing positions
        stop_losses = np.linspace(0.82, 0.86, 5)  # lowest proportion of investment peak

        # calculate number of parameter sets
        no_of_sets = len(correction_margins) * len(upturn_coefficients) * len(min_returns) * len(min_gains) * len(stop_losses)
    else:  # if using multiple positions

        state_thresholds = [0.03]  # threshold between bull and bear markets
        # calculate number of parameter sets
        no_of_sets = len(correction_margins) * len(upturn_coefficients) * len(min_gains) * len(state_thresholds)

    no_of_completions = 0  # set number of completed tests to zero

    start_timer = time.time()  # initialise timer

    # search through all possible combinations of values
    for correction_margin in correction_margins:
        for upturn_coefficient in upturn_coefficients:
            for min_gain in min_gains:

                if multiple:  # IF USING MULTI POSITIONS

                    for state_threshold in state_thresholds:

                        if random_timeframes:  # if optimisation uses random timeframes
                            if no_of_completions == 0:  # if this is the first episode
                                start_date = start  # rename starts and ends
                                end_date = end

                            start, end = get_random_timeframe(start_date, end_date, years)  # get new random timeframe

                        # create parameter dictionary
                        parameters = {'correction_margin': correction_margin,
                                      'upturn_coefficient': upturn_coefficient,
                                      'min_gain': min_gain,
                                      'state_threshold': state_threshold}

                        # pickle parameter dictionary
                        with open('parameters.pickle', 'wb') as handle:
                            pickle.dump(parameters, handle)

                        # run zipline backtest
                        performance = zipline.run_algorithm(start=start,  # start
                                                            end=end,  # end
                                                            initialize=optimize.optimize_initialize_multiple,  # initialize function
                                                            capital_base=initial_capital,  # initial capital
                                                            handle_data=strategy_multiple_positions.handle_market_corrections,  # handle_data function
                                                            data=panel)  # data to test against

                        # calculate mean daily return and alpha
                        mean_daily_return = sum(performance['returns']) / len(performance['returns'])
                        alpha = performance['alpha'][-1]

                        # store result for parameters
                        if first is True:
                            # create result dict
                            results = {'mean_daily_return': [mean_daily_return],
                                       'alpha': [alpha],
                                       'correction_margin': [correction_margin],
                                       'upturn_coefficient': [upturn_coefficient],
                                       'min_gain': [min_gain],
                                       'state_threshold': [state_threshold]}
                            first = False  # indicate subsequent optimisation tests
                        else:

                            # update result dict
                            results['mean_daily_return'].insert(0, mean_daily_return)
                            results['alpha'].insert(0, alpha)
                            results['correction_margin'].insert(0, correction_margin)
                            results['upturn_coefficient'].insert(0, upturn_coefficient)
                            results['min_gain'].insert(0, min_gain)
                            results['state_threshold'].insert(0, state_threshold)

                        no_of_completions += 1  # amend completion
                        print('Parameter set ' + str(no_of_completions) + ' of ' + str(no_of_sets))  # print episode number
                        print('Timeframe: ' + str(start.date()) + ' ~ ' + str(end.date()))  # print episode/backtest timeframe
                        print('Mean daily return: ' + str(round(mean_daily_return * 100, 3)) + '%')  # print mean daily return
                        print('Alpha: ' + str(alpha))  # print alpha across whole backtest
                        print('COMPLETION: ' + str(round((no_of_completions / no_of_sets) * 100, 4)) + '%')  # print completion percentage
                        print('TIME ELAPSED: ' + str(datetime.timedelta(seconds=round((time.time() - start_timer), 0))))  # print elapsed time
                        print('---------------------------------------------------------------------------------')  # separate episode data

                else:  # IF NOT USING MULTI POSITIONS

                    for min_return in min_returns:
                        for stop_loss in stop_losses:

                            if random_timeframes:  # if optimisation uses random timeframes
                                if no_of_completions == 0:  # if this is the first episode
                                    start_date = start  # rename starts and ends
                                    end_date = end

                                start, end = get_random_timeframe(start_date, end_date, years)  # get new random timeframe

                            # create parameter dictionary
                            parameters = {'correction_margin': correction_margin,
                                          'upturn_coefficient': upturn_coefficient,
                                          'min_return': min_return,
                                          'min_gain': min_gain,
                                          'stop_loss': stop_loss}

                            # pickle parameter dictionary
                            with open('parameters.pickle', 'wb') as handle:
                                pickle.dump(parameters, handle)

                            # run zipline backtest
                            performance = zipline.run_algorithm(start=start,  # start
                                                                end=end,  # end
                                                                initialize=optimize.optimize_initialize_single,  # initialize function
                                                                capital_base=initial_capital,  # initial capital
                                                                handle_data=strategy_single_position.handle_market_corrections,  # handle_data function
                                                                data=panel)  # data to test against

                            # calculate mean daily return and alpha
                            mean_daily_return = sum(performance['returns']) / len(performance['returns'])
                            alpha = performance['alpha'][-1]

                            # store result for parameters
                            if first is True:
                                # create result dict
                                results = {'mean_daily_return': [mean_daily_return],
                                           'alpha': [alpha],
                                           'correction_margin': [correction_margin],
                                           'upturn_coefficient': [upturn_coefficient],
                                           'min_return': [min_return],
                                           'min_gain': [min_gain],
                                           'stop_loss': [stop_loss]}
                                first = False  # indicate subsequent optimisation tests
                            else:

                                # update result dict
                                results['mean_daily_return'].insert(0, mean_daily_return)
                                results['alpha'].insert(0, alpha)
                                results['correction_margin'].insert(0, correction_margin)
                                results['upturn_coefficient'].insert(0, upturn_coefficient)
                                results['min_return'].insert(0, min_return)
                                results['min_gain'].insert(0, min_gain)
                                results['stop_loss'].insert(0, stop_loss)

                            no_of_completions += 1  # amend completion
                            print('Parameter set ' + str(no_of_completions) + ' of ' + str(no_of_sets))  # print episode number
                            print('Timeframe: ' + str(start.date()) + ' ~ ' + str(end.date()))  # print episode/backtest timeframe
                            print('Mean daily return: ' + str(round(mean_daily_return*100, 3)) + '%')  # print mean daily return
                            print('Alpha: ' + str(alpha))  # print alpha across whole backtest
                            print('COMPLETION: ' + str(round((no_of_completions / no_of_sets) * 100, 4)) + '%')  # print completion percentage
                            print('TIME ELAPSED: ' + str(datetime.timedelta(seconds=round((time.time() - start_timer), 0))))  # print elapsed time
                            print('---------------------------------------------------------------------------------')  # separate episode data

    os.remove('parameters.pickle')  # delete remaining parameters pickle file

    return results  # return the stored parameters and mean daily returns and alphas


# FUNCTION TO OPTIMISE WEIGHTS WITH MONTE CARLO CONTROL
def monte_carlo(start, end, initial_capital, panel, random_timeframes=False, years=5, multiple=True):

    first = True  # indicate the first test of parameter sets
    exploit_method = 'return'
    num_episodes = 500   # input number of episodes
    no_of_completions = 0  # set number of completed tests to zero

    '''---------------------------- SET OF PROPOSED PARAMETER VALUES TO BE OPTIMISED ------------------------'''
    if not multiple:  # if not using multiple positions

        # create parameter dictionary
        parameters = {'correction_margin': 0,
                      'upturn_coefficient': 0,
                      'min_return': 0,
                      'min_gain': 0,
                      'stop_loss': 0}

        # create range dictionary
        ranges = {'correction_margin': (0, 1),
                  'upturn_coefficient': (0, 1),
                  'min_return': (0, 1),
                  'min_gain': (0, 1),
                  'stop_loss': (0, 1)}

    else:  # if using multiple positions

        # create parameter dictionary
        parameters = {'correction_margin': 0,
                      'upturn_coefficient': 0,
                      'min_gain': 0,
                      'state_threshold': 0}

        # create range dictionary
        ranges = {'correction_margin': [0.05],
                  'upturn_coefficient': (0.05, 0.25),
                  'min_gain': [-0.05],
                  'state_threshold': [-10.0]}

    start_timer = time.time()  # initialise timer
    results = None  # initialise results placeholder

    for episode in range(num_episodes):  # go through episodes

        if random_timeframes:  # if optimisation uses random timeframes
            if no_of_completions == 0:  # if this is the first episode
                start_date = start  # rename starts and ends
                end_date = end

            start, end = get_random_timeframe(start_date, end_date, years)  # get new random timeframe

        exploration_prob = 1 - math.exp(20 * ((episode/num_episodes) - 1))  # determine the probability of exploration for this episode

        parameters = multi_armed_bandit(parameters, ranges, exploration_prob, results, exploit_method, multiple)  # choose explore or exploit

        # pickle parameter dictionary
        with open('parameters.pickle', 'wb') as handle:
            pickle.dump(parameters, handle)

        if multiple:  # if using multiple positions

            # run zipline backtest
            performance = zipline.run_algorithm(start=start,  # start
                                                end=end,  # end
                                                initialize=optimize.optimize_initialize_multiple,  # initialize function
                                                capital_base=initial_capital,  # initial capital
                                                handle_data=strategy_multiple_positions.handle_market_corrections,  # handle_data function
                                                data=panel)  # data to test against

            # calculate mean daily return and alpha
            mean_daily_return = sum(performance['returns']) / len(performance['returns'])
            alpha = performance['alpha'][-1]

            # store result for parameters
            if first is True:
                # create result dict
                results = {'mean_daily_return': [mean_daily_return],
                           'alpha': [alpha],
                           'correction_margin': [parameters['correction_margin']],
                           'upturn_coefficient': [parameters['upturn_coefficient']],
                           'min_gain': [parameters['min_gain']],
                           'state_threshold': [parameters['state_threshold']]}
                first = False  # indicate subsequent optimisation tests
            else:

                # update result dict
                results['mean_daily_return'].insert(0, mean_daily_return)
                results['alpha'].insert(0, alpha)
                results['correction_margin'].insert(0, parameters['correction_margin'])
                results['upturn_coefficient'].insert(0, parameters['upturn_coefficient'])
                results['min_gain'].insert(0, parameters['min_gain'])
                results['state_threshold'].insert(0, parameters['state_threshold'])

        else:  # if not using multiple positions

            # run zipline backtest
            performance = zipline.run_algorithm(start=start,  # start
                                                end=end,  # end
                                                initialize=optimize.optimize_initialize_single,  # initialize function
                                                capital_base=initial_capital,  # initial capital
                                                handle_data=strategy_single_position.handle_market_corrections,  # handle_data function
                                                data=panel)  # data to test against

            # calculate mean daily return and alpha
            mean_daily_return = sum(performance['returns']) / len(performance['returns'])
            alpha = performance['alpha'][-1]

            # store result for parameters
            if first is True:
                # create result dict
                results = {'mean_daily_return': [mean_daily_return],
                           'alpha': [alpha],
                           'correction_margin': [parameters['correction_margin']],
                           'upturn_coefficient': [parameters['upturn_coefficient']],
                           'min_return': [parameters['min_return']],
                           'min_gain': [parameters['min_gain']],
                           'stop_loss': [parameters['stop_loss']]}
                first = False  # indicate subsequent optimisation tests
            else:

                # update result dict
                results['mean_daily_return'].insert(0, mean_daily_return)
                results['alpha'].insert(0, alpha)
                results['correction_margin'].insert(0, parameters['correction_margin'])
                results['upturn_coefficient'].insert(0, parameters['upturn_coefficient'])
                results['min_return'].insert(0, parameters['min_return'])
                results['min_gain'].insert(0, parameters['min_gain'])
                results['stop_loss'].insert(0, parameters['stop_loss'])

        no_of_completions += 1  # amend completion
        print('Episode ' + str(no_of_completions) + ' of ' + str(num_episodes))  # print episode number
        print('Timeframe: ' + str(start.date()) + ' ~ ' + str(end.date()))  # print episode/backtest timeframe
        print('Mean daily return: ' + str(round(mean_daily_return * 100, 3)) + '%')  # print mean daily return
        print('Alpha: ' + str(alpha))  # print alpha across whole backtest
        print('COMPLETION: ' + str(round((no_of_completions / num_episodes) * 100, 4)) + '%')  # print completion percentage
        print('TIME ELAPSED: ' + str(datetime.timedelta(seconds=round((time.time() - start_timer), 0))))  # print elapsed time
        print('---------------------------------------------------------------------------------')  # separate episode data

    os.remove('parameters.pickle')  # delete remaining parameters pickle file

    return results  # return the stored parameters and mean daily returns and alphas


# FUNCTION TO DETERMINE WHETHER TO EXPLORE OR EXPLOIT (MULTI-ARMED BANDIT)
def multi_armed_bandit(parameters, ranges, exploration_prob, results, exploit_method, multiple):

    if results is not None:  # if there are already results (i.e. not first episode)
        result_df = pd.DataFrame(data=results)  # create dataframe of current results
    else:  # if there are no results yet (i.e. first episode)
        result_df = None  # set results data frame to none

    for key in parameters.keys():  # iterate through parameters

        if key is 'correction_margin':
            parameters[key] = 0.05

        elif key is 'min_gain':
            parameters[key] = -0.05

        elif key is 'state_threshold':
            parameters[key] = -10.0

        elif random.random() > exploration_prob:  # exploit
            if exploit_method is 'return':  # use mean daily return
                result_df.sort_values('mean_daily_return', ascending=False)  # sort results according to return

            elif exploit_method is 'alpha':  # use mean daily alpha
                result_df.sort_values('alpha', ascending=False)  # sort results according to alpha

            best_value = result_df[key][0]  # select best parameter according to alpha or return

            displacement = (max(ranges[key]) - min(ranges[key])) * 0.025

            # set parameter value to a random value within 0.025 of the best value
            parameters[key] = round(random.uniform(best_value - displacement, best_value + displacement), 4)

        else:  # explore
            parameters[key] = round(random.uniform(min(ranges[key]), max(ranges[key])), 4)  # set random parameter value between given ranges

    if parameters['min_gain'] <= parameters['correction_margin']:  # if the minimum gain is lower than the correction margin
        if not multiple:  # if using multi positions
            if parameters['min_gain'] <= parameters['min_return']:  # if the minimum gain is lower than the min_return
                return parameters  # return the parameter values
        else:  # if not using multi positions
            return parameters  # return parameters values

    else:  # if the minimum gain is higher than the correction margin
        parameters = multi_armed_bandit(parameters, exploration_prob, results, exploit_method, multiple)  # determine new parameter values
        return parameters  # return new parameter values


# FUNCTION TO GET RANDOM YEARS FOR BACKTEST TO AVOID OVERFITTING
def get_random_timeframe(start_date,  end_date, years):

    min_year = start_date.year  # get maximum and minimum years
    max_year = end_date.year

    rand_min_year = random.randint(min_year, max_year-years)  # determine random timeframe
    rand_max_year = rand_min_year + years

    start = datetime.datetime(rand_min_year, 1, 1, 0, 0, 0, 0, pytz.utc)  # set random datetimes
    end = datetime.datetime(rand_max_year, 1, 1, 0, 0, 0, 0, pytz.utc)

    return start, end
