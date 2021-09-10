from statistics import mean
import os
import time
import mplfinance as mpf
import pandas as pd
import datetime
import numpy as np
from pandas import DataFrame, Series, Timestamp
from mytools import dataframe_to_dict, format_print, time_stamp_to_string
from mytools import series_range, find_all
from mytools import is_increasing, is_decreasing, index_object_to_int
from kite_tools import return_historical_data


# Defining Annotations types:-
date_type = Timestamp
date_string = str  # contains date as string Eg. 'Mar 03, 2021'
price_type = float
num_touches_type = int
index_groups_type = list[tuple[num_touches_type, dict[date_type, price_type]]]
# Eg. [(3, {Timestamp('2020-08-19 00:00:00'): 2154.0, Timestamp('2021-02-25 00:00:00'): 2152.0}),
# # (3, {Timestamp('2020-09-30 00:00:00'): 2267.0})]
condition_string_type = str  # boolean conditions as string


class Support:
    """
    A class to hold data and secondary methods for support objects. Each support
    object has the following data stored about it in instance variables:

    1. stock_name: str = The name of the stock for which this is a support

    2. num_touches: int = The number of times the support level was touched and it held.

    3. data: DataFrame = A table containing date and price data for the days when support held.

    4. data_dict: dict = Dictionary form of the 'data' DataFrame. This is generally just used
    to display the data in the summarize() method of this class.

    5. most_recents: tuple = A tuple containing the most recent date for which data 
    is available along with the closing price on that date.

    6. avg: float = The average support price calculated by calculating the average of
    the prices on the days on which the support held.

    7. status: float = A parameter containing the (current price - average support price)

    8. num_days_bw_tests: numpy.array = A numpy array containing number of days between each test of 
    the support level. (We use a numpy array to allow vectorised comparisons on array values.
    See examples in 'filter_supports', 'filter_resistances')

    9. time_period_int: int = The number of days for which the support level held

    10. days_since_last_tested: int = The number of days since the support level was last tested (from then to today)

    11. is_breached: bool = A boolean stating whether or not the support level has been breached
    after the time it last held.

    12. breach_data: DataFrame = A table containing date and price data for the days when the
    support was breached after the last time it held.

    13. breach_data_dict: dict = Dictionary form of the 'breach_data' DataFrame. This is generally just used
    to display the data in the summarize() method of this class.
    """

    def __init__(self, data_tuple: tuple[num_touches_type, dict[date_type, price_type]], is_breached: bool,
                breach_data: DataFrame, most_recents: tuple[date_type, price_type], stock_name: str) -> None:

        self.stock_name = stock_name

        self.num_touches = data_tuple[0]

        df = pd.DataFrame()
        df['date'] = data_tuple[1].keys()
        df['price'] = data_tuple[1].values()
        df = df.sort_values(by='date')
        self.data = df

        self.data_dict: dict[date_string, price_type]
        self.data_dict = {time_stamp_to_string(date): price for date, price in data_tuple[1].items()}

        self.most_recents = most_recents
        
        self.avg: float = df.price.mean()

        most_recent_price = most_recents[1]
        self.status = most_recent_price - self.avg

        # Here the dates obtained from the 'self.data' DateFrame are in the
        # form of Pandas Timestamp objects

        most_recent_date = df.iloc[-1, 0]
        least_recent_date = df.iloc[0, 0]
        date_difference = most_recent_date - least_recent_date

        # Now the 'date_difference' TimeDelta object has a string representation
        # that looks like this: '131 days 00:00:00'. In the next line we extract
        # the integer number of days from this string

        time_period_int = int(str(date_difference).split()[0])
        self.time_period_int = time_period_int

        days_since_last_tested = datetime.date.today() - most_recent_date.date() 

        # Here the 'days_since_last_tested' variable is a TimeDelta object. We 
        # extract the integer number of days from this string like before.

        self.days_since_last_tested = int(str(days_since_last_tested).split()[0])

        num_days_bw_tests = []
        dates_list = list(data_tuple[1].keys())

        for i in range(len(dates_list) - 1):
            date_difference = dates_list[i + 1] - dates_list[i]

            # Here the 'date_difference' variable is a TimeDelta object. We 
            # extract the integer number of days from this string like before.

            date_difference_int = int(str(date_difference).split()[0])
            num_days_bw_tests.append(date_difference_int)

        self.num_days_bw_tests = np.array(num_days_bw_tests)

        self.is_breached = is_breached

        self.breach_data = breach_data

        breach_data_dict = {time_stamp_to_string(date): price for index, date, price in breach_data.itertuples()}

        self.breach_data_dict: dict[date_string, price_type]
        self.breach_data_dict = breach_data_dict

    def summary(self, show_breach_data: bool = True, breach_data_truncated: bool = True) -> None:
        """
        This method returns a text-based summary of a given support/resistance level
        in terms of Most recent price data, Average Price, Number of touches, Date - Price data, 
        Number of days between each test, Time Period, Is_Breached, Breach data,
        Days since level was last tested and Current price status.

        If 'show_breach_data' is set to 'True', only then will breach_data be displayed

        By default, if the breach data is more than 8 rows long, it will be displayed in
        a truncated format with only the first 4 and the last 4 rows being displayed. In this
        case, to display the full dataset, set 'breach_data_truncated' = 'False'.
        """
        print('Most recent data:')
        print(f'Date: {self.most_recents[0]}')
        print(f'Price: {self.most_recents[1]}\n')

        print(f"Average price:\n{round(self.avg, 2)}\n")

        print(f'Number of touches:\n{self.num_touches}\n')

        print(f'Date - Price data:\n')
        format_print(self.data_dict)

        print('Number of days between tests:')
        print(tuple([f'{item} days' for item in self.num_days_bw_tests]))
        print('\n')

        print(f"Time period:")
        if self.time_period_int >= 365:
            time_period_str = f'{self.time_period_int // 365} years {self.time_period_int % 365} days\n'
        else:
            time_period_str = f'{self.time_period_int} days\n'
        print(time_period_str)

        print(f'Breached:\n{self.is_breached}\n')

        if show_breach_data and self.is_breached:
            if len(self.breach_data_dict) > 8:
                truncate_possible = True
            else:
                truncate_possible = False

            print(f'Breach Data:\n')

            if breach_data_truncated and truncate_possible:
                head_dict = {date: price for index, date, price in self.breach_data.head(4).itertuples()}
                tail_dict = {date: price for index, date, price in self.breach_data.tail(4).itertuples()}
                format_print(head_dict, suppress_lower=True)
                print('.' * 10)
                format_print(tail_dict, suppress_upper=True)
            else:
                format_print(self.breach_data_dict)
        
        print('Days since last tested:')

        if self.days_since_last_tested >= 365:
            print(f'{self.days_since_last_tested // 365} years {self.days_since_last_tested % 365} days\n')
        else:
            print(f'{self.days_since_last_tested} days\n')

        print('Current Price Status:')
        if self.status >= 0:
            print('Above support/resistance level')
            print(f'+{round(self.status, 2)}')
        else:
            print('Below support/resistance level')
            print(round(self.status, 2))

        print('\n\n\n\n')

    def summary_pdf(self, show_breach_data: bool = True, breach_data_truncated: bool = True) -> None:
        """
        This method returns a text-based summary of a given support/resistance level
        in terms of Most recent price data, Average Price, Number of touches, Date - Price data, 
        Number of days between each test, Time Period, Is_Breached, Breach data,
        Days since level was last tested and Current price status to the text file 'pdf_text.txt'.

        If 'show_breach_data' is set to 'True', only then will breach_data be displayed

        By default, if the breach data is more than 8 rows long, it will be displayed in
        a truncated format with only the first 4 and the last 4 rows being displayed. In this
        case, to display the full dataset, set 'breach_data_truncated' = 'False'.
        """
        with open('pdf_text.txt', mode='a') as pdf_text_object:

            print('Most recent data:', file=pdf_text_object)
            print(f'Date: {self.most_recents[0]}', file=pdf_text_object)
            print(f'Price: {self.most_recents[1]}\n', file=pdf_text_object)

            print(f"Average price:\n{round(self.avg, 2)}\n", file=pdf_text_object)

            print(f'Number of touches:\n{self.num_touches}\n', file=pdf_text_object)

            print(f'Date - Price data:\n', file=pdf_text_object)
            format_print(self.data_dict, file=pdf_text_object)

            print(f"Time period:", file=pdf_text_object)
            if self.time_period_int >= 365:
                time_period_str = f'{self.time_period_int // 365} years {self.time_period_int % 365} days\n'
            else:
                time_period_str = f'{self.time_period_int} days\n'
            print(time_period_str, file=pdf_text_object)

            print('Number of days between tests:', file=pdf_text_object)
            print(tuple([f'{item} days' for item in self.num_days_bw_tests]), file=pdf_text_object)
            print('\n', file=pdf_text_object)

            print(f'Breached:\n{self.is_breached}\n', file=pdf_text_object)

            if show_breach_data and self.is_breached:
                if len(self.breach_data_dict) > 8:
                    truncate_possible = True
                else:
                    truncate_possible = False

                print(f'Breach Data:\n', file=pdf_text_object)

                if breach_data_truncated and truncate_possible:
                    head_dict = {date: price for index, date, price in self.breach_data.head(4).itertuples()}
                    tail_dict = {date: price for index, date, price in self.breach_data.tail(4).itertuples()}
                    format_print(head_dict, suppress_lower=True, file=pdf_text_object)
                    print('.' * 10)
                    format_print(tail_dict, suppress_upper=True, file=pdf_text_object)
                else:
                    format_print(self.breach_data_dict, file=pdf_text_object)

            print('Days since last tested:', file=pdf_text_object)

            if self.days_since_last_tested >= 365:
                print(f'{self.days_since_last_tested // 365} years {self.days_since_last_tested % 365} days\n', file=pdf_text_object)
            else:
                print(f'{self.days_since_last_tested} days\n', file=pdf_text_object)

            print('Current Price Status:', file=pdf_text_object)
            if self.status >= 0:
                print('Above support/resistance level', file=pdf_text_object)
                print(f'+{round(self.status, 2)}')
            else:
                print('Below support/resistance level', file=pdf_text_object)
                print(round(self.status, 2))

            print('\n\n\n\n', file=pdf_text_object)

    def summarize(self, show_breach_data: bool = True, breach_data_truncated: bool = True, pdf: bool = False) -> None:
        """
        This method was created so a 'print("Support")' statement could be added
        before calling summary() or summary_pdf(). In the Resistance class which inherits from
        this one, a 'print("Resistance")' statement will be added instead before
        calling summary() or summary_pdf().

        If 'pdf' is set to 'True', summary_pdf() will be called, otherwise
        summary() wil be called.
        """
        if pdf:
            with open('pdf_text.txt', mode='a') as pdf_text_object:
                print(f'Stock Name: {self.stock_name}\n', file=pdf_text_object)
                print('Support\n', file=pdf_text_object)
            self.summary_pdf(show_breach_data=show_breach_data, breach_data_truncated=breach_data_truncated)
        else:
            print(f'Stock Name: {self.stock_name}\n')
            print('Support\n')
            self.summary(show_breach_data=show_breach_data, breach_data_truncated=breach_data_truncated)


class Resistance(Support):
    """
    A class to hold data and secondary methods for resistance objects. Each resistance
    object has the following data stored about it in instance variables:

    1. stock_name: str = The name of the stock for which this is a support

    2. num_touches: int = The number of times the resistance level was touched and it held.

    3. data: DataFrame = A table containing date and price data for the days when resistance held.

    4. data_dict: dict = Dictionary form of the 'data' DataFrame. This is generally just used
    to display the data in the summarize() method of this class.

    5. num_days_bw_tests = A list containing number of days between each test of the resistance level

    6. most_recents: tuple = A tuple containing the most recent date for which data 
    is available along with the closing price on that date.

    7. avg: float = The average resistance price calculated by calculating the average of
    the prices on the days on which the resistance held.

    8. status: float = A parameter containing the (current price - average support price)

    9. time_period_int: int = The number of days for which the resistance level held

    10. days_since_last_tested = The number of days since the resistance level was last tested (from then to today)

    11. is_breached: bool = A boolean stating whether or not the resistance level has been breached
    after the time it last held.

    12. breach_data: DataFrame = A table containing date and price data for the days when the
    resistance was breached after the last time it held.

    13. breach_data_dict: dict = Dictionary form of the 'breach_data' DataFrame. This is generally just used
    to display the data in the summarize() method of this class.
    """

    def summarize(self, show_breach_data: bool = True, breach_data_truncated: bool = True, pdf: bool = False) -> None:
        """
        This method was created so a 'print("Resistance")' statement will be added before
        calling summary() or summary_pdf().

        If 'pdf' is set to 'True', summary_pdf() will be called, otherwise
        summary() wil be called.
        """
        if pdf:
            with open('pdf_text.txt', mode='a') as pdf_text_object:
                print(f'Stock Name: {self.stock_name}\n', file=pdf_text_object)
                print('Resistance\n', file=pdf_text_object)
            self.summary_pdf(show_breach_data=show_breach_data, breach_data_truncated=breach_data_truncated)
        else:
            print(f'Stock Name: {self.stock_name}\n')
            print('Resistance\n')
            self.summary(show_breach_data=show_breach_data, breach_data_truncated=breach_data_truncated)


class Stock:
    """
    A class to hold data and secondary methods for stock objects. Each stock
    object has the following data stored about it in instance variables:

    1. stock_name: str = The name of the stock. This is the same as the name
    of the csv file containing the stock data.

    2. supports: list[Support] = This is a list of filtered support objects.
    By default, this contains a list of support objects associated with supports
    that haven't been breached.

    3. resistances: list[resistance] = This is a list of filtered resistance objects.
    By default, this contains a list of resistance objects associated with resistances
    that haven't been breached.

    4. final_support: Support = The 'Support' object of the most recent support that
    hasn't been breached. If the 'Stock' object has no supports that haven't been
    breached, 'final_support' is set to 'None'.

    5. final_resistance: Resistance = The 'Resistance' object of the most recent resistance that
    hasn't been breached. If the 'Stock' object has no resistances that haven't been
    breached, 'final_resistance' is set to 'None'.

    6. is_range_bound: bool = If the given stock has at least 1 support and
    1 resistance that hasn't been breached, then range trading is possible for the stock.
    If this is the case, then 'is_range_bound' is set to 'True'. Otherwise,
    it is set to 'False'.

    7. range_width: float = If range trading is possible for a given stock, then the 
    'range_width' of the stock is equal to the difference of the average price of the
    the final resistance and the average price of the final support for that stock.
    """
    def __init__(self, stock_name: str, supports: list[Support] = None, resistances: list[Resistance] = None):
        
        self.stock_name = stock_name

        if supports is None:
            self.supports = []
        else:
            self.supports = supports

        if resistances is None:
            self.resistances = []
        else:
            self.resistances = resistances

        self.final_support = None
        if supports:
            sorted_supports = sorted(supports, key=lambda x:x.avg)
            # Finding the most recent support i.e. the final support
            self.final_support = sorted_supports[-1]

        self.final_resistance = None
        if resistances:
            sorted_resistances = sorted(resistances, key=lambda x:x.avg)
            # Finding the most recent resistance i.e. the final resistance
            self.final_resistance = sorted_resistances[-1]

        if self.final_support is not None and self.final_resistance is not None:
            self.is_range_bound = True
            self.range_width = self.final_resistance.avg - self.final_support.avg
        else:
            self.is_range_bound = False
            self.range_width = None

    def summarize(self):
        """
        This function prints a summary of the stock object in terms of
        final support, final resistance and the stock being range-bound.
        """
        print(f'{self.stock_name}:\n')

        if self.final_support is not None:
            print('Final Support:')
            self.final_support.summarize()
        else:
            print("This stock does not have a final support\n")

        if self.final_resistance is not None:
            print('Final Resistance:')
            self.final_resistance.summarize()
        else:
            print("This stock does not have a final resistance\n")

        if self.is_range_bound:
            print("Range trading is possible in this stock")
            print("Range width:")
            print(round(self.range_width, 2))
            print('\n')
        else:
            print("Range trading is not possible in this stock\n")


def search_list_of_stocks_with_csv_data(stock_name: str) -> bool:
    """
    This function checks if the stock given by the name 'stock_name'
    has its csv data stored in the 'saved_csv_data' folder. 
    
    It returns 'True' if the stock's data is stored. Otherwise, 
    it returns 'False'.

    It does this by checking if the stock's name is present in the 
    'list_of_stocks_with_csv_data.txt' text file in that folder.
    """
    current_path = os.getcwd()
    saved_csv_data_folder_path = os.path.join(current_path, 'saved_csv_data')
    os.chdir(saved_csv_data_folder_path)

    with open('list_of_stocks_with_csv_data.txt') as txt_file:
        list_of_stocks = txt_file.readlines()
        cleaned_up_list_of_stocks = [stock_name.strip() for stock_name in list_of_stocks]

    os.chdir(current_path)

    if stock_name in cleaned_up_list_of_stocks:
        return True
    else:
        return False


def setup_table(stock_name: str, num_years: float = 1, volume: bool = False, refresh: bool = False,
                sort: bool = True, reverse: bool = False) -> DataFrame:
    """
    This function creates and returns a pandas dataframe containing OHLC (and optional Volume) 
    stock data over multiple years for the stock whose name is given by 'stock_name'.

    If this stock's data has been calculated earlier today, then it will simply be loaded from memory
    for the number of years for which it was originally calculated. 
    
    If this stock's data has been calculated before, but not today, then it will 
    be refreshed to add today's data by calling the 'return_historical_data()' 
    function from the 'kite_tools' module. The refreshed data will contain
    'num_years' of data and not the number of years of data that had been calculated before
    
    If this stock's data hasn't been calculated before, then it is obtained by calling
    the 'return_historical_data()' function from the 'kite_tools' module. 

    The 'num_years' parameter represents the number of years for which stock data is returned.
    It has a default vaue of 1 assigned to it. This argument should be used when creating stock 
    data for a given stock for the first time or when refreshing data. It will not work if you 
    are simply loading stock data from memory.

    The 'refresh' parameter is pretty much only used when you use a custom value of the
    'num_years' parameter besides 1.
    
    If the number of days for which the stock's data exists, is less than the number of days in
    'num_years' years, then all the data for the stock will be returned without raising a
    Warning or Exception.
    
    The 'num_years' parameter can take a decimal value as input.

    If the 'sort' parameter is set to 'True' and the 'reverse' parameter is set to False, the dataframe will be
    sorted in ascending order by 'date'.
    If the 'sort' parameter is set to 'True' and the 'reverse' parameter is set to 'True', the dataframe will be
    sorted in descending order by 'date'.

    If the 'volume' parameter to 'True', the table returned will have a 'volume' column.
    """
    current_path = os.getcwd()
    
    if not os.path.exists('saved_csv_data'):
        os.makedirs('saved_csv_data')

    saved_csv_data_folder_path = os.path.join(current_path, 'saved_csv_data')

    # Checking if this stock's OHLC data is stored as a CSV file
    # in the 'saved_csv_data' folder. 

    is_stock_saved = search_list_of_stocks_with_csv_data(stock_name)

    if is_stock_saved and not refresh:

        # This option is used to load the data already stored in a csv 
        # file. However if the data in the csv file is not updated upto
        # today's date, the 'refresh' parameter will be set to 'True'
        # and the data will be refreshed with 'num_years' of data
        # being returned and stored in the csv file.

        # Switching path to the 'saved_csv_data' folder so that the csv
        # files stored there can be read

        os.chdir(saved_csv_data_folder_path)

        table = pd.read_csv(f'{stock_name}.csv', usecols=['date', 'open', 'high', 'low', 'close', 'volume'])

        # When we read the table from the csv file, the data in the date 
        # column is read as string data. Therefore, we convert the data 
        # in the date column from 'str' to 'Timestamp'.

        table.date = table.date.apply(Timestamp)

        most_recent_date: Timestamp = table.date[len(table) - 1]

        # Converting the Timestamp object to a datetime object

        most_recent_date_datetime_obj = most_recent_date.to_pydatetime()

        # Converting the datetime object to a date object

        most_recent_date_as_a_date_object = most_recent_date_datetime_obj.date()

        todays_date = datetime.date.today()

        # If the most recent data in the table is today's data, then the
        # data does not need to be refreshed. Otherwise, the data in the
        # table needs to be refreshed.

        if most_recent_date_as_a_date_object == todays_date:    
            refresh = False
        else:
            refresh = True

        os.chdir(current_path)

    if (not is_stock_saved) or (is_stock_saved and refresh):
        # If the stock's OHLC data needs to be refreshed with current data
        # or if it hasn't been saved in the past, then the data
        # needs to be generated by calling the 'return_historical_data()'
        # function from the 'kite_tools' module

        # Deleting the csv file if it already exists. The csv file 
        # will already exist if you are refreshing data

        if os.path.exists(f'{stock_name}.csv'):
            os.remove(f'{stock_name}.csv')

        # In order for the 'return_historical_data()' function to work,
        # it needs to access the access token stored in the 'access_token.txt'
        # text file in the main folder.

        table = return_historical_data(stock_name, num_years=num_years)

        # Now, to store a newly created csv, we switch the current path
        # to the 'saved_csv_data' folder again.

        os.chdir(saved_csv_data_folder_path)

        # Adding the name of the stock to the 'list_of_stocks_with_csv_data.txt'
        # text file if it isn't already there

        if not is_stock_saved:
            with open('list_of_stocks_with_csv_data.txt', 'a') as txt_file:
                txt_file.write(f'{stock_name}\n')

        table.to_csv(f'{stock_name}.csv')

    # Remember that volume data is always stored in the csv file
    # and always loaded into the dataframe.

    # Dropping the volume column if it's not needed

    if not volume:
        table = table[['date', 'open', 'high', 'low', 'close']]    

    if sort and not reverse:
        table = table.sort_values(by='date', ascending=True)
    elif sort and reverse:
        table = table.sort_values(by='date', ascending=False)

    # Switching the path back to the main folder

    os.chdir(current_path)

    return table


def plot_graph(table: DataFrame, title: str = None, moving_average: tuple[int] = None, volume: bool = False,
                dark_mode: bool = False, supports: list[Support] = None, resistances: list[Resistance] = None):
    """
    This function creates a candlestick plot of stock data provided in OHLC (with optional Volume data) form in
    the pandas dataframe specified in the 'table' attribute.

    If the 'volume' attribute is set to 'True', then the volume data associated with the stock will be
    plotted as well.

    If the 'title' attribute is provided, the chart will have the title given by this attribute

    The 'moving_average' attribute should be set to a tuple containing the number of days for which moving
    averages are to be calculated and plotted on the chart.

    If the 'dark_mode' attribute is set to 'True', the candlestick plot will be created with a Dark Theme.
    """
    if supports is None:
        supports = []
    
    if resistances is None:
        resistances = []


    # Checking if there is a 'volume' column in the table
    # passed to this function by counting the number of columns 
    # in the input table

    num_columns = len(table.columns)

    if num_columns == 6:
        volume_column_present_in_table = True
    elif num_columns == 5:
        volume_column_present_in_table = False

    # Setting the date column as the index column so that
    # the mplfinance library can parse this table's data
    # and plot it

    indexed_table = table.set_index('date')

    # Setting the theme data for the 2 possible graph
    # themes

    if not dark_mode:
        mc = mpf.make_marketcolors(base_mpf_style='yahoo')
        s = mpf.make_mpf_style(marketcolors=mc, y_on_right=False, gridstyle='-')

    else:
        mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
        s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, y_on_right=False, gridstyle='-')

    kwargs = dict(figratio=(14, 8), figscale=1.2)

    if moving_average is not None:
        kwargs['mav'] = moving_average

    if title is not None:
        kwargs['title'] = title

    if volume:

        # If volume column is not present in input data
        # and the volume parameter in this function is set 
        # to 'True', then a Value Error is raised.

        if not volume_column_present_in_table:
            raise ValueError('Volume column not present in table')

        else:
            kwargs['volume'] = True

    if not supports and not resistances:
        mpf.plot(indexed_table, **kwargs, style=s, type='candle')

    else:
        line_list: list[list[tuple[date_type, price_type], tuple[date_type, price_type]]]
        line_list = []

        if supports:
            for support in supports:
                start_and_end_pt_data = [(support.data.date[0], support.avg), (support.data.date[len(support.data)-1], support.avg)]
                line_list.append(start_and_end_pt_data)
        
        if resistances:
            for resistance in resistances:
                start_and_end_pt_data = [(resistance.data.date[0], resistance.avg), (resistance.data.date[len(resistance.data)-1], resistance.avg)]
                line_list.append(start_and_end_pt_data)
        

        colors_list = ['g'] * len(supports) + ['r'] * len(resistances)

        mpf.plot(indexed_table, **kwargs, style=s, type ='candle', alines=dict(alines=line_list, colors=colors_list))


def plot_final(table: DataFrame, supports: list[Support] = None, resistances: list[Resistance] = None,
            volume: bool = False, title: str = None, moving_average: tuple[int] = None,
            dark_mode: bool = False, relevant_regions: bool = False) -> None:
    
    if supports is None:
        supports = []

    if resistances is None:
        resistances = []

    if supports or resistances:

        if relevant_regions:

            # If 'relevant_regions' is set to True, only that portion of the OHLC
            # candlestick graph that is associated with the final support and resistance will be displayed
            # So if only supports or only resistances are present, nothing will happen

            if not supports or not resistances:
                return

            # If the execution got here, that means that there is at least 1 support
            # and at least 1 resistance that have not been breached.

            if supports:
                sorted_supports = sorted(supports, key=lambda x:x.avg)

                # Finding the most recent support i.e. the final support
                
                final_support = sorted_supports[-1]
                
                # Finding the first date on which the final support was tested
                
                final_support_start_date = final_support.data.date[0]

            if resistances:
                sorted_resistances = sorted(resistances, key=lambda x:x.avg)

                # Finding the most recent resistance i.e. the final resistance
                
                final_resistance = sorted_resistances[-1]
                
                # Finding the first date on which the final resistance was tested
                
                final_resistance_start_date = final_resistance.data.date[0]

            # Finding the first date on which either the final support
            # or the final resistance was tested
    
            start_date = min(final_support_start_date, final_resistance_start_date)

            # Finding the integer index of the row in which the date is 'start_date'
            # by extracting the integer from the string representation of the 'Int64Index' object.

            start_date_index = index_object_to_int(table.index[table.date == start_date])

            # Taking the index 2 values behind the original so that 2 data points before the 
            # final support/resistance can be seen in graph
            
            start_date_index = start_date_index - 2

            # Extracting the last ('start_date_index' + 1) rows from the dataframe

            truncated_table = table.iloc[start_date_index:]

            # In the 'plot_graph()' function call, we pass only the final support and 
            # the final resistance to the 'supports' and 'resistances' parameters
            # respectively.

            plot_graph(table=truncated_table, title=f'{title} close up', moving_average=moving_average, 
            dark_mode=dark_mode, supports=[final_support], resistances=[final_resistance], volume=volume)

        else:
            plot_graph(table=table, title=title, moving_average=moving_average, 
            dark_mode=dark_mode, supports=supports, resistances=resistances, volume=volume)

    else:
        plot_graph(table=table, title=title, moving_average=moving_average, dark_mode=dark_mode, volume=volume)


def calculate_tolerance(column: Series) -> int:
    """
    Returns absolute value of tolerance for calculation of supports and resistances
    """
    spread = series_range(column)
    tolerance_value = None
    if spread <= 50:
        tolerance_value = 3
    elif 50 < spread <= 100:
        tolerance_value = 5
    elif spread > 100:
        tolerance_value = 10
    return tolerance_value


def create_tolerance_function(column: Series):
    """
    This function factory creates a custom tolerance function for a given column
    """
    tolerance = calculate_tolerance(column)

    def wrapper(value1, value2):
        if abs(value1 - value2) <= tolerance:
            return True
        return False

    return wrapper


def at_least_2_common(dict1: dict, dict2: dict) -> bool:
    """
    This function returns 'True' if the dictionaries 'dict1' and 'dict2' have 2 or more
    equal key pairs. Otherwise, it returns 'False'
    """
    count = 0
    for key1 in dict1.keys():
        for key2 in dict2.keys():
            if key1 == key2:
                count += 1
                if count == 2:
                    return True
                break
    return False


def remove_duplicates(values_list: list[tuple[num_touches_type, dict[date_type, price_type]]]) -> list[tuple[num_touches_type, dict[date_type, price_type]]]:
    """
    This function filters out duplicate values from a list of  two
    element tuples and returns a list of unique tuples.
    """
    unique_values_list: index_groups_type
    unique_values_list = []

    for value1, value2 in values_list:
        if (value1, value2) not in unique_values_list:
            unique_values_list.append((value1, value2))
    return unique_values_list


def find_supports(table: DataFrame, series: str) -> dict[date_type, price_type]:
    """
    The 'table' attribute of this function takes a pandas DataFrame containing OHLC values as input.

    The 'series' attribute of this function takes a data series, either 'low' or 'close' as input.

    This function searches the series data for troughs that could represent possible support values
    and returns a dictionary containing dates and prices as key - value pairs.
    """
    # calculating the (total number of rows - 4) to find cutoff
    # row for for loop later in this function

    cutoff = len(table) - 4

    possible_supports: dict[date_type, price_type]
    possible_supports = {}

    for i in range(cutoff):
        first: price_type = table.iloc[i][series]
        second: price_type = table.iloc[i + 1][series]
        third: price_type = table.iloc[i + 2][series]
        fourth: price_type = table.iloc[i + 3][series]
        fifth: price_type = table.iloc[i + 4][series]
        date: date_type = table.iloc[i + 2].date

        if first > second > third and third < fourth < fifth:
            possible_supports[date] = third

    return possible_supports
    

def create_tolerance_group(possible_levels_dict: dict[date_type, price_type], tolerance_function) -> dict[price_type, dict[date_type, price_type]]:
    """
    This function takes the 'possible_levels_dict' dictionary containing dates and prices
    as key-value pairs as input.

    It returns a dictionary where the keys are prices and the values are dictionaries containing
    dates and prices within the calculated tolerance level as key-value pairs
    """
    items = possible_levels_dict.items()

    tolerance_groups: dict[price_type, dict[date_type, price_type]]
    tolerance_groups = {value: {} for value in possible_levels_dict.values()}

    for key1, value1 in items:
        for key2, value2 in items:
            if tolerance_function(value1, value2):
                tolerance_groups[value1][key2] = value2

    return tolerance_groups


def manipulate_groups(tolerance_groups: dict[price_type, dict[date_type, price_type]],
                      test_manipulation: bool = False) -> list[tuple[num_touches_type, dict[date_type, price_type]]]:
    """
    This function takes a tolerance group dictionary as input and returns
    a sorted, unique list of tuples with each tuple containing a number of touches value
    and a dictionary containing date and price key-value pairs.
    """
    
    index_groups: list[tuple[num_touches_type, dict[date_type, price_type]]]
    index_groups = [(len(value), value) for value in tolerance_groups.values() if len(value) >= 3]

    index_groups_unique = remove_duplicates(index_groups)

    index_groups_sorted = [(key, value) for key, value in sorted(index_groups_unique, reverse=True, key=lambda x: x[0])]

    if test_manipulation:
        print('\n\nIndex_groups: (Possible support/resistance values with 3 or more touches)')
        format_print(index_groups)
        print('\n\nIndex_groups_unique: (Duplicate values removed)')
        format_print(index_groups_unique)
        print('\n\nIndex_groups_sorted: (List sorted in descending order of number of touches)')
        format_print(index_groups_sorted)

    return index_groups_sorted


def remove_redundant_groups(index_groups_sorted: list[tuple[num_touches_type, dict[date_type, price_type]]]) -> list[tuple[num_touches_type, dict[date_type, price_type]]]:
    """
    This function takes a sorted, unique list of tuples with each tuple
    containing a number of touches value and a dictionary containing date and price
    key-value pairs as input and returns the same list after removing redundant
    values
    """
    remove_list: index_groups_type
    remove_list = []

    for index1, value1 in index_groups_sorted:
        for index2, value2 in index_groups_sorted:
            if (index1, value1) != (index2, value2) and at_least_2_common(value1, value2):
                remove_list.append((index2, value2))

        for index, value in remove_list:
            if (index, value) in index_groups_sorted:
                index_groups_sorted.remove((index, value))

    return index_groups_sorted


def process_groups(series: Series, possible_levels_values: dict[date_type, price_type],
                   testing_process: bool = False) -> list[tuple[num_touches_type, dict[date_type, price_type]]]:
    """
    This function takes the 'possible_levels_values' dictionary containing dates and prices
    as key-value pairs and a given columns data as input.

    It returns a list of tuples with each tuple representing a possible support/resistance.

    Each tuple contains the number of touches along with a date-price dictionary
    associated with the possible support/resistance level.
    """
    within_tolerance = create_tolerance_function(series)

    tolerance_groups = create_tolerance_group(possible_levels_dict=possible_levels_values,
                                              tolerance_function=within_tolerance)

    if testing_process:
        print('\n\nTolerance groups: (groups containing date-price values within tolerance levels of a given price)')
        format_print(tolerance_groups)

    index_groups_sorted = manipulate_groups(tolerance_groups, test_manipulation=testing_process)

    index_groups_final = remove_redundant_groups(index_groups_sorted)

    return index_groups_final


def is_support_valid(level: tuple[num_touches_type, dict[date_type, price_type]], table: DataFrame, 
                    testing: bool = False, invalid_data_truncated: bool = True) -> bool:
    """
    This function takes a tuple from an 'index_groups_final' object
    as input along with a date-values dataframe as input.

    If 'testing' is set to 'True', the invalid data that caused 
    this support to not be considered valid will be printed.

    If 'invalid_data_truncated' is set to False, the invalid data that caused
    this support to not be considered valid will be printed in its entirety.
    Otherwise, only the first and last 3 rows of this data will be printed.

    It returns a boolean 'is_valid' that mentions whether or not a
    support level is valid. The validity of a support level is checked
    by determining whether the stock price ever went below the support
    price by a value greater than tolerance for the time for which
    the calculated support existed.
    """
    dates: list[date_type]
    dates = sorted(list(level[1].keys()), reverse=True)

    most_recent_date = dates[0]
    least_recent_date = dates[-1]

    avg_price: float = mean(level[1].values())

    table.columns = ['date', 'price']
    tolerance = calculate_tolerance(table.price)

    invalid_data = table.loc[(table.price < (avg_price - tolerance)) & (table.date >= least_recent_date) & (table.date <= most_recent_date)]

    if invalid_data.empty:
        if testing:
            print('Support is valid')

        is_valid = True
    else:
        if testing:
            print('Support is not valid because of the following date - price data:\n')

            # Truncating the invalid data  if it is more than 6 rows long
            # unless explicitly stated otherwise, by displaying only the 
            # first 3 and last 3 rows

            if len(invalid_data) > 6:
                truncate_possible = True
            else:
                truncate_possible = False
            
            if invalid_data_truncated and truncate_possible:
                invalid_data_head_dict = dataframe_to_dict(invalid_data.head(3))
                invalid_data_tail_dict = dataframe_to_dict(invalid_data.tail(3))

                format_print(invalid_data_head_dict, suppress_lower=True)
                print('.' * 30 + '\n')
                format_print(invalid_data_tail_dict, suppress_upper=True)

            else:
                invalid_data_dict = dataframe_to_dict(invalid_data)
                format_print(invalid_data_dict)

        is_valid = False

    return is_valid


def is_support_broken(level: tuple[num_touches_type, dict[date_type, price_type]], table: DataFrame) -> tuple[bool, DataFrame]:
    """
    This function takes a tuple from an 'index_groups_final' object
    as input along with a date-values dataframe as input.

    It returns a boolean 'is_breached' that mentions whether or not a
    support level was breached after the last time it held. It also
    returns 'breach_data', a DataFrame that contains date-price data
    of when the support was breached.
    """
    dates: list[date_type]
    dates = sorted(list(level[1].keys()), reverse=True)

    most_recent_date = dates[0]

    avg_price: float = mean(level[1].values())

    table.columns = ['date', 'price']
    tolerance = calculate_tolerance(table.price)

    breach_data = table.loc[(table.price < (avg_price - tolerance)) & (table.date > most_recent_date)]

    if breach_data.empty:
        is_breached = False
    else:
        is_breached = True

    return is_breached, breach_data


def create_support_objects_list(group: list[tuple[num_touches_type, dict[date_type, price_type]]], table: DataFrame, 
                                most_recents: tuple[date_type, price_type], stock_name: str, testing: bool = False) -> list[Support]:
    """
    This function takes an 'index_groups_final' object along
    with a date-values dataframe as input in the 'group'
    and 'table' attributes respectively.

    It also takes the parameter 'most_recents', which is a
    tuple containing the most recent date for which data 
    is available along with the closing price on that date, as input.

    The input parameter 'stock_name' contains the name of the stock
    as a string.

    It returns a list of objects of class 'Support'
    """
    list_of_support_objects: list[Support]
    list_of_support_objects = []

    for support in group:

        support: tuple[num_touches_type, dict[date_type, price_type]]

        if is_support_valid(level=support, table=table, testing=testing):

            is_breached, breach_data = is_support_broken(level=support, table=table)

            support_obj = Support(data_tuple=support, is_breached=is_breached, breach_data=breach_data, most_recents=most_recents, stock_name=stock_name)
            list_of_support_objects.append(support_obj)

    return list_of_support_objects


def calculate_supports(table: DataFrame, stock_name: str, data_series: str = 'low', testing: bool = False) -> list[Support]:
    """
    This function takes an OHLC DataFrame as input along with the name of a
    'data_series' like 'low' or 'close' as input.

    It also takes a parameter 'stock_name' as input which contains the stock's
    name as a string. This parameter is then passed to the 'stock_name' 
    parameter of the 'create_support_objects_list()' function.

    It then returns a list of objects of class 'Support' which contain data on
    the calculated support levels.

    If the 'testing' attribute is set to True, then a breakdown of the different steps
    to calculate the final support levels will be displayed.
    """
    # Storing the most recent date for which data is available
    # as a string

    most_recent_date = time_stamp_to_string(table.date[len(table) - 1])
    most_recent_closing_price = table.close[len(table) - 1]

    most_recents = (most_recent_date, most_recent_closing_price)

    date_values_table = table[['date', data_series]]

    possible_supports = find_supports(table=date_values_table, series=data_series)

    index_groups_final = process_groups(series=table[data_series], possible_levels_values=possible_supports)

    if testing:
        print(f'{stock_name}\n')

        print('Supports\n')

        print('Possible supports (Troughs in graph):')
        format_print(possible_supports)

        process_groups(series=table[data_series], possible_levels_values=possible_supports, testing_process=testing)

        print("\n\nIndex_groups_final (Redundant data representing the same support/resistance has been removed)\n"
            "This list may contain invalid resistance/support values that have been breached between their start "
            "and end dates.")
        format_print(index_groups_final)

    list_of_support_objects = create_support_objects_list(group=index_groups_final, table=date_values_table, most_recents=most_recents, stock_name=stock_name, testing=testing)

    return list_of_support_objects


def summarize_data(levels: list = None, show_breach_data: bool = True, breach_data_truncated: bool = True,
                   pdf: bool = False) -> None:
    """
    This function takes a list of supports/resistances directly as input.
    It then displays the summary of each support/resistance calculated.

    If the parameter 'pdf' is set to 'True', the summaries of support/resistance
    data will be outputted to the file 'pdf_text.txt' and the summarize() methods
    of the given support/resistance objects will be called with pdf=True.
    """
    for level in levels:
        level.summarize(show_breach_data=show_breach_data, breach_data_truncated=breach_data_truncated, pdf=pdf)


def process_num_days_bw_tests(condition_str: str, level_type: str, comparison_operator: str) -> str:
    """
    This function aims to replace all occurrences of a substring like
    'support/resistance.num_days_bw_tests >= 3' in the input
    condition string with 'all(support/resistance.num_days_bw_tests >= 3)'.
    This is done because if the original string is evaluated directly in the 
    eval() function in 'filter_supports()' / 'filter_resistances()', it will
    generate a boolean array rather than return a 'True' or 'False' value.

    The 'condition_str' parameter of this function takes the condition string
    that needs to be processed as input.

    This function takes the same value of the 'level_type' parameter as input
    as the process_conditions() function. The parameter 'level_type' can take 
    either the value 'support' or 'resistance' with the value of this parameter 
    being substituted in the place of type in the '{type}.{attribute}' strings
    in the process_conditions() function.

    The 'comparison_operator' parameter of this function can take the values
    '>', '<', '<=', '>=', '==' or '!=' as input.
    """
    condition = condition_str
    if f'{level_type}.num_days_bw_tests {comparison_operator} ' in condition:
            # Here, we are trying to replace all occurrences of 
            # 'support/resistance.num_days_bw_tests >= 3'
            # with 'all(support/resistance.num_days_bw_tests >= 3)' 
            # This is because the original string when evaluated will 
            # generate a boolean array.

            firsts = find_all(f'{level_type}.num_days_bw_tests {comparison_operator} ', condition)
            num_occurrences = len(firsts)
        
            for ocurrence_index in range(num_occurrences):
                # We recalculate the 'firsts' and 'lasts' lists each time the loop runs
                # because the condition string changes each time the loop runs.
                firsts = find_all(f'{level_type}.num_days_bw_tests {comparison_operator} ', condition)
                lasts = find_all(f'{level_type}.num_days_bw_tests {comparison_operator} ', condition, lasts=True)
                
                first_index = firsts[ocurrence_index]
                last_index = lasts[ocurrence_index]
                # Finding the index of the next space after f'{level_type}.num_days_bw_tests {comparison_operator} '
                # that is, finding the index of the space before 3 in 'support/resistance.num_days_bw_tests >= 3'
                if condition[last_index + 1:].find(' ') == -1:
                    condition = (condition[:first_index] + 'all(' + f'{level_type}.num_days_bw_tests {comparison_operator} ' 
                + condition[last_index + 1:] + ')')
                
                else:
                    next_space_index = condition[last_index + 1:].find(' ') + last_index + 1
                    condition = (condition[:first_index] + 'all(' + f'{level_type}.num_days_bw_tests {comparison_operator} ' 
                + condition[last_index+1 : next_space_index] + ')' + condition[next_space_index:])
            
            return condition


def process_conditions(conditions: tuple[str], level_type: str) -> list[condition_string_type]:
    """
    This function takes a list of condition strings and replaces the short forms
    of the attribute names with their corresponding full names in each string.

    It then replaces each occurrence of each attribute in each string with
    a '{type}.{attribute}' string. This is done so each support/resistance object
    in the 'filter_supports'/'filter_resistances' function can use this condition string.
    
    The parameter 'level_type' can take either the value 'support' or 'resistance' 
    with the value of this parameter being substituted in the place of type in the 
    '{type}.{attribute}' string.

    If any condition string uses the '>=', '<=', '!=' or '==' operators
    with an avg value, then a ValueError will be raised since float values
    like avg can not be compared properly using these operators.

    The list of modified condition strings is then returned
    """
    conditions_list: list[condition_string_type]
    conditions_list = []

    for condition in conditions:
        condition: str = condition.lower()
        
        if 'nums' in condition:
            condition = condition.replace('nums', 'num_touches')
        if 'duration' in condition:
            condition = condition.replace('duration', 'time_period_int')
        if 'average' in condition:
            condition = condition.replace('average', 'avg')
        if 'num_days_since' in condition:
            condition = condition.replace('num_days_since', 'days_since_last_tested')
        if 'days_between' in condition:
            condition = condition.replace('days_between', 'num_days_bw_tests')    

        for attribute in ('avg', 'num_touches', 'time_period_int', 'days_since_last_tested', 'num_days_bw_tests', 'status'):
            condition = condition.replace(attribute, f'{level_type}.{attribute}')

        if ('==' not in condition and '>=' not in condition and '<=' not in condition
                and '!=' not in condition and '=' in condition):
            condition = condition.replace('=', '==')

        if f'{level_type}.num_days_bw_tests.increasing' in condition:
            condition = condition.replace(f'{level_type}.num_days_bw_tests.increasing', f'is_increasing({level_type}.num_days_bw_tests)')
        if f'{level_type}.num_days_bw_tests.decreasing' in condition:
            condition = condition.replace(f'{level_type}.num_days_bw_tests.decreasing', f'is_decreasing({level_type}.num_days_bw_tests)')

        # Here, we are trying to replace all occurrences of 
        # 'support/resistance.num_days_bw_tests >= 3'
        # with 'all(support/resistance.num_days_bw_tests >= 3) 
        # This is because the original string when evaluated will 
        # generate a boolean array.

        if f'{level_type}.num_days_bw_tests >= ' in condition:
            condition = process_num_days_bw_tests(condition_str=condition, level_type=level_type, comparison_operator='>=')
        if f'{level_type}.num_days_bw_tests <= ' in condition:
            condition = process_num_days_bw_tests(condition_str=condition, level_type=level_type, comparison_operator='<=')
        if f'{level_type}.num_days_bw_tests < ' in condition:
            condition = process_num_days_bw_tests(condition_str=condition, level_type=level_type, comparison_operator='<')
        if f'{level_type}.num_days_bw_tests > ' in condition:
            condition = process_num_days_bw_tests(condition_str=condition, level_type=level_type, comparison_operator='>')    

        if f'{level_type}.num_days_bw_tests == ' in condition:
            raise ValueError("Warning: '==' operator can not be used with the 'num_days_bw_tests' parameter")
        if f'{level_type}.num_days_bw_tests != ' in condition:
            raise ValueError("Warning: '!=' operator can not be used with the 'num_days_bw_tests' parameter")      

        if f'{level_type}.avg ==' in condition:
            raise ValueError("Warning: Average values can not be compared using '=' operator.")
        if f'{level_type}.avg !=' in condition:
            raise ValueError("Warning: Average values can not be compared using '!=' operator.")
        if f'{level_type}.avg >=' in condition:
            raise ValueError("Warning: Average values can not be compared using '>=' operator. Use '>' instead.")
        if f'{level_type}.avg <=' in condition:
            raise ValueError("Warning: Average values can not be compared using '<=' operator. Use '<' instead.")

        conditions_list.append(condition)

    return conditions_list


def filter_supports(supports: list[Support], *args: str, is_breached: bool = False, ignore_is_breach: bool = False, testing: bool = False):
    """
    This function takes a list of support objects as input and then
    returns a list of those supports that satisfy all the conditions given.

    It first checks if each support object has the same value of 'is_breached' as
    this function's parameter.

    The 'is_breached' function parameter is set to 'False' by default so if this
    function is called with only 'supports' as a parameter, it will return a list
    of supports that haven't been breached.

    To filter the supports in the list without considering the 'is_breached'
    parameter, set the parameter 'ignore_is_breach' to 'True'. It is set to
    'False' by default.

    The 'testing' parameter when set to True will summarize each support object that
    was filtered out, display the conditions given to filter the support and display
    why it was filtered out.

    This function takes an arbitrary number of boolean conditions based on
    the 'num_touches', 'avg', 'time_period_int', 'days_since_last_tested', 
    'num_days_bw_tests' and 'status' parameters of a resistance/support
    to evaluate, using the tuple of positional arguments 'args'.

    The attribute names used in these conditions aren't case-sensitive

    In these conditions, these attributes can be referred to by other names.
    The list of these short forms is as follows:

    'num_touches'  :  'nums'
    'avg'  :  'average'
    'time_period_int'  :  'duration'
    'days_since_last_tested' : 'num_days_since'
    'num_days_bw_tests' : 'days_between'

    The '==' operator can also be replaced by '=' in these conditions.

    These boolean conditions can contain the logical operators 'and', 'or'
    and 'not' as well as all the relational operators '>', '<', '==', '!=',
    '>=', '<=' to compare values

    If any condition string uses the '>=', '<=', '!=' or '==' operators
    with an avg value, then a ValueError will be raised since float values
    like avg can not be compared properly using these operators.
    """
    filtered_supports: list[Support]
    filtered_supports = []

    conditions_list: list[condition_string_type]

    # processing the string conditions present in input
    # to make them evaluatable by the 'eval()' function
    # later in this code

    conditions_list = process_conditions(args, level_type='support')

    for support in supports:

        support: Support

        invalid = False

        # For each of the conditions below, if the support passes the condition,
        # the program does nothing but if it does not pass the condition, the
        # boolean variable 'invalid' is set to 'True' and the continue statement
        # is executed which means the program goes on to test the next support.

        if not ignore_is_breach:
            if support.is_breached == is_breached:
                pass
            else:
                reason_for_support_being_filtered_out = ("The 'is_breached' attribute "
                "of the support does not match the value of the 'is_breached' parameter "
                "of the filter function") 
                invalid = True

        conditions = conditions_list[:]

        if invalid:
            if testing:
                print('-' * 100 + '\n')
                print("The following support was filtered out: \n")
                support.summarize()
                print('-' * 100 + '\n')
                print('\n')
                print("The following conditions were provided to filter this support: ")
                print('-' * 100 + '\n')
                print(f'is_breached = {is_breached}')
                print(f'ignore_is_breach = {ignore_is_breach}')
                format_print(conditions_list, suppress_upper=True, suppress_lower=True)
                print('-' * 100 + '\n')
                print('\n')
                print("This support was filtered out because: ")
                print(reason_for_support_being_filtered_out)
                print('\n')

            continue
        
        while conditions:
            condition = conditions.pop()
            if eval(condition):
                pass
            else:
                invalid = True
                break

        if invalid:
            reason_for_support_being_filtered_out = ("The condition "
            + f"'{condition}' evaluated to 'False'")

            if testing:
                print('-' * 100 + '\n')
                print("The following support was filtered out: \n")
                support.summarize()
                print('-' * 100 + '\n')
                print('\n')
                print("The following conditions were provided to filter this support: ")
                print('-' * 100 + '\n')
                print(f'is_breached = {is_breached}')
                print(f'ignore_is_breach = {ignore_is_breach}')
                format_print(conditions_list, suppress_upper=True, suppress_lower=True)
                print('-' * 100 + '\n')
                print('\n')
                print("This support was filtered out because: ")
                print(reason_for_support_being_filtered_out)
                print('\n')

            continue

        if testing:
            print('-' * 100 + '\n')
            print("The following support passed all the conditions: \n")
            support.summarize()
            print('-' * 100 + '\n')
            print('\n')
            print("The following conditions were provided to filter this support: ")
            print('-' * 100 + '\n')
            print(f'is_breached = {is_breached}')
            print(f'ignore_is_breach = {ignore_is_breach}')
            format_print(conditions_list, suppress_upper=True, suppress_lower=True)
            print('-' * 100 + '\n')
            print('\n')

        filtered_supports.append(support)

    return filtered_supports


def find_resistances(table: DataFrame, series: str) -> dict[date_type, price_type]:
    """
    The 'table' attribute of this function takes a pandas DataFrame containing OHLC values as input.

    The 'series' attribute of this function takes a data series, either 'high' or 'close' as input.

    This function searches the series data for peaks that could represent possible resistance values
    and returns a dictionary containing dates and prices as key - value pairs.
    """
    cutoff = len(table) - 4

    possible_resistances: dict[date_type, price_type]
    possible_resistances = {}

    for i in range(cutoff):
        first: price_type = table.iloc[i][series]
        second: price_type = table.iloc[i + 1][series]
        third: price_type = table.iloc[i + 2][series]
        fourth: price_type = table.iloc[i + 3][series]
        fifth: price_type = table.iloc[i + 4][series]
        date: date_type = table.iloc[i + 2].date

        if first < second < third and third > fourth > fifth:
            possible_resistances[date] = third

    return possible_resistances


def is_resistance_valid(level: tuple[num_touches_type, dict[date_type, price_type]], table: DataFrame, 
                        testing: bool = False, invalid_data_truncated: bool = True) -> bool:
    """
    This function takes a tuple from an 'index_groups_final' object
    as input along with a date-values dataframe as input.

    If 'testing' is set to 'True', the invalid data that caused 
    this resistance to not be considered valid will be printed.

    If 'invalid_data_truncated' is set to False, the invalid data that caused
    this resistance to not be considered valid will be printed in its entirety.
    Otherwise, only the first and last 3 rows of this data will be printed.

    It returns a boolean 'is_valid' that mentions whether or not a
    resistance level is valid. The validity of a resistance level is checked
    by determining whether the stock price ever went above the resistance
    price by a value greater than tolerance for the time for which
    the calculated resistance existed.
    """
    dates: list[date_type]
    dates = sorted(level[1].keys(), reverse=True)

    most_recent_date = dates[0]
    least_recent_date = dates[-1]

    avg_price: float = mean(level[1].values())

    table.columns = ['date', 'price']
    tolerance: int = calculate_tolerance(table.price)

    invalid_data = table.loc[(table.price > (avg_price + tolerance)) & (table.date >= least_recent_date) & (table.date <= most_recent_date)]

    if invalid_data.empty:
        if testing:
            print('Resistance is valid')

        is_valid = True
    else:
        if testing:
            print('Resistance is not valid because of the following date - price data:\n')
            
            # Truncating the invalid data  if it is more than 6 rows long
            # unless explicitly stated otherwise, by displaying only the 
            # first 3 and last 3 rows

            if len(invalid_data) > 6:
                truncate_possible = True
            else:
                truncate_possible = False
            
            if invalid_data_truncated and truncate_possible:
                invalid_data_head_dict = dataframe_to_dict(invalid_data.head(3))
                invalid_data_tail_dict = dataframe_to_dict(invalid_data.tail(3))

                format_print(invalid_data_head_dict, suppress_lower=True)
                print('.' * 30 + '\n')
                format_print(invalid_data_tail_dict, suppress_upper=True)

            else:
                invalid_data_dict = dataframe_to_dict(invalid_data)
                format_print(invalid_data_dict)

        is_valid = False

    return is_valid


def is_resistance_broken(level: tuple[num_touches_type, dict[date_type, price_type]], table: DataFrame) -> tuple[bool, DataFrame]:
    """
    This function takes a tuple from an 'index_groups_final' object
    as input along with a date-values dataframe as input.

    It returns a boolean 'is_breached' that mentions whether or not a
    resistance level was breached after the last time it held. It also
    returns 'breach_data', a DataFrame that contains date-price data
    of when the resistance was breached.
    """
    dates: list[date_type]
    dates = sorted(level[1].keys(), reverse=True)

    most_recent_date = dates[0]

    avg_price: float = mean(level[1].values())

    table.columns = ['date', 'price']
    tolerance = calculate_tolerance(table.price)

    breach_data = table.loc[(table.price > (avg_price + tolerance)) & (table.date > most_recent_date)]

    if breach_data.empty:
        is_breached = False
    else:
        is_breached = True

    return is_breached, breach_data


def create_resistance_objects_list(group: list[tuple[num_touches_type, dict[date_type, price_type]]], table: DataFrame,
                                    most_recents: tuple[date_type, price_type], stock_name: str, testing: bool = False) -> list[Resistance]:
    """
    This function takes an 'index_groups_final' object along
    with a date-values dataframe as input.

    It also takes the parameter 'most_recents', which is a
    tuple containing the most recent date for which data 
    is available along with the closing price on that date, as input.

    The input parameter 'stock_name' contains the name of the stock
    as a string.

    It returns a list of objects of class 'Resistance'
    """
    list_of_resistance_objects: list[Resistance]
    list_of_resistance_objects = []

    for resistance in group:

        resistance: tuple[num_touches_type, dict[date_type, price_type]]

        if is_resistance_valid(level=resistance, table=table, testing=testing):

            is_breached, breach_data = is_resistance_broken(level=resistance, table=table)

            resistance_obj = Resistance(data_tuple=resistance, is_breached=is_breached, breach_data=breach_data, most_recents=most_recents, stock_name=stock_name)
            list_of_resistance_objects.append(resistance_obj)

    return list_of_resistance_objects


def calculate_resistances(table: DataFrame, stock_name: str, data_series: str = 'high', testing: bool = False) -> list[Resistance]:
    """
    This function takes an OHLC DataFrame as input along with the name of a
    'data_series' like 'high' or 'close' as input.

    It also takes a parameter 'stock_name' as input which contains the stock's
    name as a string. This parameter is then passed to the 'stock_name' 
    parameter of the 'create_resistance_objects_list()' function.

    It then returns a list of objects of class 'Resistance' which contain data on
    the calculated resistance levels.

    If the 'testing' attribute is set to True, then a breakdown of the different steps
    to calculate the final resistance levels will be displayed.
    """
    # Storing the most recent date for which data is available
    # as a string

    most_recent_date = time_stamp_to_string(table.date[len(table) - 1])
    most_recent_closing_price = table.close[len(table) - 1]

    most_recents = (most_recent_date, most_recent_closing_price)

    date_values_table = table[['date', data_series]]

    possible_resistances = find_resistances(table=date_values_table, series=data_series)

    index_groups_final = process_groups(series=table[data_series], possible_levels_values=possible_resistances)

    if testing:
        print(f'{stock_name}\n')

        print('Resistance\n')

        print('Possible resistances (Peaks in graph):')
        format_print(possible_resistances)

        process_groups(series=table[data_series], possible_levels_values=possible_resistances, testing_process=testing)

        print("\n\nIndex_groups_final (Redundant data representing the same support/resistance has been removed)\n"
              "This list may contain invalid resistance/support values that have been breached between their start "
              "and end dates.")
        format_print(index_groups_final)

    list_of_resistance_objects = create_resistance_objects_list(group=index_groups_final, table=date_values_table, most_recents=most_recents, stock_name=stock_name, testing=testing)

    return list_of_resistance_objects


def filter_resistances(resistances: list[Resistance], *args: str, is_breached: bool = False,
                       ignore_is_breach: bool = False, testing: bool = False) -> list[Resistance]:
    """
    This function takes a list of resistance objects as input and then
    returns a list of those resistances that satisfy all the conditions given.

    It first checks if each resistance object has the same value of 'is_breached' as
    this function's parameter.

    The 'is_breached' function parameter is set to 'False' by default so if this
    function is called with only 'resistances' as a parameter, it will return a list
    of resistances that haven't been breached.

    To filter the resistances in the list without considering the 'is_breached'
    parameter, set the parameter 'ignore_is_breach' to 'True'. It is set to
    'False' by default

    The 'testing' parameter when set to True will summarize each support object that
    was filtered out, display the conditions given to filter the support and display
    why it was filtered out.

    This function takes an arbitrary number of boolean conditions based on
    the 'num_touches', 'avg', 'time_period_int', 'days_since_last_tested', 
    'num_days_bw_tests' and 'status' parameters of a resistance/support
    to evaluate, using the tuple of positional arguments 'args'.

    The attribute names used in these conditions aren't case-sensitive

    In these conditions, these attributes can be referred to by other names.
    The list of these short forms is as follows:

    'num_touches'  :  'nums'
    'avg'  :  'average'
    'time_period_int'  :  'duration'
    'days_since_last_tested' : 'num_days_since'
    'num_days_bw_tests' : 'days_between'

    The '==' operator can also be replaced by '=' in these conditions.

    These boolean conditions can contain the logical operators 'and', 'or'
    and 'not' as well as all the relational operators '>', '<', '==', '!=',
    '>=', '<=' to compare values

    If any condition string uses the '>=', '<=', '!=' or '==' operators
    with an avg value, then a ValueError will be raised since float values
    like avg can not be compared properly using these operators.
    """
    filtered_resistances: list[Resistance]
    filtered_resistances = []

    conditions_list: list[condition_string_type]

    # processing the string conditions present in input
    # to make them evaluatable by the 'eval()' function
    # later in this code

    conditions_list = process_conditions(args, level_type='resistance')

    for resistance in resistances:

        resistance: Resistance

        invalid = False

        # For each of the conditions below, if the resistance passes the condition,
        # the program does nothing but if it does not pass the condition, the
        # boolean variable 'invalid' is set to 'True' and the continue statement
        # is executed which means the program goes on to test the next resistance.

        if not ignore_is_breach:
            if resistance.is_breached == is_breached:
                pass
            else:
                reason_for_resistance_being_filtered_out = ("The 'is_breached' attribute "
                "of the resistance does not match the value of the 'is_breached' parameter "
                "of the filter function") 
                invalid = True

        conditions = conditions_list[:]

        if invalid:
            if testing:
                print('-' * 100 + '\n')
                print("The following resistance was filtered out: \n")
                resistance.summarize()
                print('-' * 100 + '\n')
                print('\n')
                print("The following conditions were provided to filter this resistance: ")
                print('-' * 100 + '\n')
                print(f'is_breached = {is_breached}')
                print(f'ignore_is_breach = {ignore_is_breach}')
                format_print(conditions_list, suppress_upper=True, suppress_lower=True)
                print('-' * 100 + '\n')
                print('\n')
                print("This resistance was filtered out because: ")
                print(reason_for_resistance_being_filtered_out)
                print('\n')

            continue

        while conditions:
            condition = conditions.pop()
            if eval(condition):
                pass
            else:
                invalid = True
                break

        if invalid:
            reason_for_resistance_being_filtered_out = ("The condition "
            + f"'{condition}' evaluated to 'False'")

            if testing:
                print('-' * 100 + '\n')
                print("The following resistance was filtered out: \n")
                resistance.summarize()
                print('-' * 100 + '\n')
                print('\n')
                print("The following conditions were provided to filter this resistance: ")
                print('-' * 100 + '\n')
                print(f'is_breached = {is_breached}')
                print(f'ignore_is_breach = {ignore_is_breach}')
                format_print(conditions_list, suppress_upper=True, suppress_lower=True)
                print('-' * 100 + '\n')
                print('\n')
                print("This resistance was filtered out because: ")
                print(reason_for_resistance_being_filtered_out)
                print('\n')

            continue

        if testing:
            print('-' * 100 + '\n')
            print("The following resistance passed all the conditions: \n")
            resistance.summarize()
            print('-' * 100 + '\n')
            print('\n')
            print("The following conditions were provided to filter this resistance: ")
            print('-' * 100 + '\n')
            print(f'is_breached = {is_breached}')
            print(f'ignore_is_breach = {ignore_is_breach}')
            format_print(conditions_list, suppress_upper=True, suppress_lower=True)
            print('-' * 100 + '\n')
            print('\n')

        filtered_resistances.append(resistance)

    return filtered_resistances


def summarize_table(table: DataFrame, *args: str, stock_name: str, support_data_series: str = 'low',
                    resistance_data_series: str = 'high', testing: bool = False, 
                    ignore_is_breach: bool = False, pdf: bool = False) -> tuple[list[Support], list[Resistance]]:
    """
    This function takes an OHLC values DataFrame as input.

    It also takes the data series 'support_data_series' and 'resistance_data_series' as
    the values of the data_series parameters of the 'calculate_supports' and
    'calculate_resistances' functions.
    
    The parameter 'stock_name' will take the name of the stock as input.

    If the parameter 'testing' is set to 'True', the detailed process of support and
    resistance calculation will be shown.

    If the parameter 'pdf' is set to 'True', the summaries of support/resistance
    data will be outputted to the file 'pdf_text.txt' and summarize_data() will
    be called with pdf=True.

    By default, the filter functions will filter out the support/resistance levels that
    have been breached. To see all support/resistance levels regardless, set
    'ignore_is_breach' to 'True'.

    This function takes an arbitrary number of boolean conditions based on
    the 'num_touches', 'avg', 'time_period_int', 'days_since_last_tested', 
    'num_days_bw_tests' and 'status' parameters of a resistance/support
    to evaluate, using the tuple of positional arguments 'args'.

    Those supports and resistances which satisfy all of these conditions
    will have their summary data displayed.

    The attribute names used in these conditions aren't case-sensitive

    In these conditions, these attributes can be referred to by other names.
    The list of these aliases is as follows:

    'num_touches'  :  'nums'
    'avg'  :  'average'
    'time_period_int'  :  'duration'
    'days_since_last_tested' : 'num_days_since'
    'num_days_bw_tests' : 'days_between'

    The '==' operator can also be replaced by '=' in these conditions.

    These boolean conditions can contain the logical operators 'and', 'or'
    and 'not' as well as all the relational operators '>', '<', '==', '!=',
    '>=', '<=' to compare values

    If any condition string uses the '>=', '<=', '!=' or '==' operators
    with an avg value, then a ValueError will be raised since float values
    like avg can not be compared properly using these operators.
    """
    unfiltered_supports = calculate_supports(table, data_series=support_data_series, testing=testing, stock_name=stock_name)

    if testing:
        print('\nList of support objects:\n')
        print(unfiltered_supports)

        print("\nSummarising Support data\n")
        summarize_data(unfiltered_supports)
        print("End of support data summary\n")

    supports = filter_supports(unfiltered_supports, *args, ignore_is_breach=ignore_is_breach, testing=testing)

    if testing:
        print('filtered supports:')
        print(supports)

    summarize_data(supports, pdf=pdf)

    unfiltered_resistances = calculate_resistances(table, data_series=resistance_data_series, testing=testing, stock_name=stock_name)

    if testing:
        print('\nList of resistance objects:\n')
        print(unfiltered_resistances)

        print("\nSummarising Resistance data\n")
        summarize_data(unfiltered_resistances)
        print("End of resistance data summary\n")

    resistances = filter_resistances(unfiltered_resistances, *args, ignore_is_breach=ignore_is_breach, testing=testing)

    if testing:
        print('filtered resistances:')
        print(resistances)

    summarize_data(resistances, pdf=pdf)

    return supports, resistances


def summary_multiple(stock_names_list: list[str], *args: str, moving_average: tuple = tuple([]),
                    pdf: bool = False, levels: bool = True, relevant_regions: bool = False,
                    refresh: bool = False, testing: bool = False, volume: bool = False,
                    num_years: float = 1, dark_mode: bool = False, ignore_is_breach: bool = False,
                    support_data_series: str = 'low', resistance_data_series: str = 'high'):
    """
    This function summarizes the data of the support/resistance values of
    multiple stocks mentioned in the list passed to it.

    This function will call the summarize_table() method with its default
    arguments either directly or through summary_pdf(). Therefore
    all support/resistance levels that have been breached will be filtered out.

    The parameter 'stock_names_list' taken as input will contain a list
    of stock names.
    """
    stock_objects_list: list[Stock]
    stock_objects_list = []

    for stock_name in stock_names_list:
        if pdf:
            pass
        else:
            table = setup_table(stock_name=stock_name, volume=volume, num_years=num_years, refresh=refresh)

            supports, resistances = summarize_table(table, *args, stock_name=stock_name, testing=testing, 
                                                    support_data_series=support_data_series,
                                                    resistance_data_series=resistance_data_series,
                                                    ignore_is_breach=ignore_is_breach)
            
            stock_object = Stock(stock_name=stock_name, supports=supports, resistances=resistances)

            if testing:
                stock_object.summarize()

            stock_objects_list.append(stock_object)

            if levels:

                # If a stock is capable of range - bound trading, then only the
                # relevant regions of stock data will be plotted

                if relevant_regions and stock_object.is_range_bound:
                    plot_final(table=table, title=stock_name, supports=supports, resistances=resistances, relevant_regions=relevant_regions,
                                volume=volume, moving_average=moving_average, dark_mode=dark_mode)
                else:
                    plot_final(table=table, title=stock_name, supports=supports, resistances=resistances,
                                volume=volume, moving_average=moving_average, dark_mode=dark_mode)
            else:
                plot_final(table=table, title=stock_name, volume=volume, moving_average=moving_average, dark_mode=dark_mode)

    return stock_objects_list
