import os


def setup():
    """
    This function creates the 'saved_csv_data' folder that will hold the
    csv data of the stocks processed so far. This folder also contains
    'list_of_stocks_with_csv_data.txt', a text file which contains the
    list of stocks whose data has been processed in the past.

    In addition, this function creates the 'request_token.txt' and 'access_token.txt'
    text files which contain the request token and access token for automated
    read and write access.
    """
    current_path = os.getcwd()

    saved_csv_data_folder_path = os.path.join(current_path, 'saved_csv_data')

    if not os.path.exists(saved_csv_data_folder_path):
        os.makedirs('saved_csv_data')

    os.chdir(saved_csv_data_folder_path)

    if not os.path.exists('list_of_stocks_with_csv_data.txt'):
        with open('list_of_stocks_with_csv_data.txt', 'w') as txt_file:
            pass

    os.chdir(current_path)

    if not os.path.exists('access_token.txt'):
        with open('access_token.txt', 'w') as txt_file:
            pass

    if not os.path.exists('request_token.txt'):
        with open('request_token.txt', 'w') as txt_file:
            pass

