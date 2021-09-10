import os
import time
import datetime
import webbrowser
from pandas import DataFrame
import pandas as pd
from mytools import list_of_dicts_to_csv
from kiteconnect import KiteConnect


def login() -> None:
    """
    This function automates the initial login process and outputs the access token 
    of the day to the 'access_token.txt' file.

    You generally only need to call this function once a day.
    """
    # api key and api secret are always constant and they are given
    # on the zerodha kite connect account web page

    # The real api_key, api_secret value has been removed

    api_key = '0000000'
    api_secret = '00000'

    # Opening the api login endpoint.
    # When the web page opens, enter your login information and login
    # When redirected to the redirect URL, copy the request token in the URL
    # Paste this request token in the 'request_token.txt' text file
    # in this folder

    # Note: This method was used because the input() statement doesn't work
    # in the 'Output' section that is enabled with the Code Runner Extension.
    # So, in order to input something in the program, you would need to go
    # to Settings and change Code Runner settings to run code in Terminal 
    # and then you would have to change it back after this function executes.

    webbrowser.open(fr'https://kite.zerodha.com/connect/login?v=3&api_key={api_key}')

    # Pausing program execution for 25 seconds to give time
    # to get the request token and paste it in the text file

    time.sleep(25)

    # Reading the request token from the text file
    
    with open('request_token.txt') as txt_file:
        request_token = txt_file.read().strip()

    # Getting the access token which can be used for multiple logins till 
    # 5:30 am the next day

    kite = KiteConnect(api_key=api_key)
    data = kite.generate_session(request_token=request_token, api_secret=api_secret)
    access_token = data['access_token']

    # Outputting the access token to a text file so it can be read
    # automatically by the 'setup_kite()' function instead of being 
    # copied and pasted

    with open('access_token.txt', 'w') as txt_file:
        txt_file.write(access_token)


def setup_kite() -> KiteConnect:
    """
    This function is used to initiate a Kite session by creating 
    and returning a KiteConnect object with access token set.

    Make sure you only call this function after the access token
    for the day has been generated and saved to a text file by the 
    'login()' function. 
    """
    
    # Reading the access token from the text file 'access_token.txt'

    with open('access_token.txt') as txt_file:
        access_token = txt_file.read().strip()
    
    # api key is always constant and it is given
    # on the zerodha kite connect account web page

    # The real api_key value has been removed

    api_key = '00000'

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token=access_token)

    return kite


def refresh_instrument_data(kite_object: KiteConnect, file_name: str = 'instruments', exchange: str = 'NSE') -> None:
    """
    This function refreshes the basic data (including instrument token)
    about all the financial instruments available with Kite
    and stores it in a csv file with the name 'file_name'.
    The default file name is 'instruments.csv'

    If a file with the name 'file_name' already exists, it will be deleted
    and replaced with a new file.

    Generally, this function is only called once in a few days.

    The 'kite_object' parameter contains the value of the kite object
    that needs to be passed to this function in order for it to work.

    The 'exchange' parameter holds the value of the stock exchange for
    which data is returned.
    """
    if not file_name.endswith('.csv'):
        file_name = f'{file_name}.csv'

    if os.path.exists(file_name):
        os.remove(file_name)

    # Generating a list of dictionaries that contain data about all
    # available financial instruments.

    instrument_data: list[dict]
    instrument_data = kite_object.instruments(exchange=exchange)

    # Creating a csv containing the instrument data under the
    # name 'file_name'.

    list_of_dicts_to_csv(list_of_dicts=instrument_data, file_name='instruments')   

    
def return_instrument_token(trading_symbol: str, file_name: str = 'instruments') -> int:
    """
    This function takes a trading symbol ('trading_symbol') as input along with 
    the name of the csv file containing data for all financial instruments. 
    
    It then returns the instrument token for the financial instrument 
    whose trading symbol was given as input.
    """
    if not file_name.endswith('.csv'):
        file_name = f'{file_name}.csv'

    df = pd.read_csv(file_name)

    for index, instrument in df.iterrows():
        if instrument['tradingsymbol'] == trading_symbol:
            return instrument['instrument_token']


def return_historical_data(stock_name: str, num_years: float = 1, interval: str = 'day') -> DataFrame:
    """
    This function takes a stock symbol ('stock_name') as
    input and returns a DataFrame containing its OHLC data.

    The 'num_years' attribute sets the number of years of historical data
    to return. By default, 'num_years' is set to 1.

    The 'interval' attribute sets the time interval for OHLC data.
    By default, it is set to 'day' which means that this function returns
    day-by-day data.
    """
    kite_object = setup_kite()

    instrument_token = return_instrument_token(trading_symbol=stock_name)

    # Forcing program to stop execution temporarily so as not 
    # to exceed API rate limit

    time.sleep(0.5)

    # Creating datetime objects for the start date and end date of the
    # historical data

    today = datetime.datetime.now()
    years = datetime.timedelta(days=round(365 * num_years))
    years_ago = today - years

    hist_data: list[dict]
    hist_data = kite_object.historical_data(instrument_token=instrument_token, from_date=years_ago, to_date=today, interval=interval)

    df = pd.DataFrame(hist_data)

    return df