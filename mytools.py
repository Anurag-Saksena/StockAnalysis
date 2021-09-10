from pandas import DataFrame, Timestamp, Int64Index
import pandas as pd
import time
import os
import sys
from fpdf import FPDF
from typing import Any, Iterable, Sequence
import pickle
import csv
import shutil


date_string = str # String representation of a date


def index_object_to_int(index_object: Int64Index) -> int:
    """
    This function takes a pandas 'Int64Index' object as input
    and it returns the row index extracted from the string 
    representation of the 'Int64Index' object. 

    The string representation of an 'Int64Index'
    object looks like this: 'Int64Index([94], dtype='int64')'.
    From here, this function extracts the row index 94.
    """
    index_string = str(index_object)
    start_index = index_string.find('[')
    end_index = index_string.find(']')
    index = int(index_string[(start_index+1) : end_index])
    return index


def is_increasing(input_list: Sequence):
    """
    This function returns 'True' if all the elements of
    a sequence are in increasing order. Otherwise,
    it returns 'False'.
    """
    current_item = input_list[0]
    for i in range(1, len(input_list)):
        next_item = input_list[i]
        if current_item > next_item:
            return False
        current_item = input_list[i]
    return True


def is_decreasing(input_list: Sequence):
    """
    This function returns 'True' if all the elements of
    a sequence are in decreasing order. Otherwise,
    it returns 'False'.
    """
    current_item = input_list[0]
    for i in range(1, len(input_list)):
        next_item = input_list[i]
        if current_item < next_item:
            return False
        current_item = input_list[i]
    return True


def find_all(substring: str, string: str, lasts: bool = False):
    """
    This function takes a substring 'substring' and  a string 'string' as
    input along with the parameter 'lasts'.

    If 'lasts' is set to 'False' (which it is by default), 
    a list containing the first indices of each occurrence of 
    the substring in the string is returned.

    If 'lasts' is set to 'True' ,a list containing the last indices
     of each occurrence of the substring in the string is returned.
    """
    length_substring = len(substring)
    length_string = len(string)
    if not lasts:
        first_index = []
        for index in range(length_string - length_substring):
            if string[index : index + length_substring] == substring:
                first_index.append(index)
        return first_index
    else:
        last_index = []
        for index in range(length_string - length_substring):
            if string[index : index + length_substring] == substring:
                last_index.append(index + length_substring - 1)
        return last_index


def series_range(items: Iterable) -> float:
    """
    Calculates range of values in any iterable
    """
    return max(items) - min(items)


def time_stamp_to_string(time_stamp: Timestamp) -> date_string:
    """
    This function converts a TimeStamp object into a date string.
    Eg. 2021-07-28 00:00:00 -> 'Jul 28, 2021'
    """
    num_to_month = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun', '07': 'Jul',
                    '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'}
    # Accessing date as a string from string representation of TimeStamp object.
    # The string representation of a TimeStamp object looks like this: '2021-07-28 00:00:00'
    date_str = str(time_stamp)[:10]

    year = date_str[:4]

    month_num = date_str[5:7]
    month = num_to_month[month_num]

    day = date_str[-2:]

    time_stamp_string = f'{month} {day}, {year}'

    return time_stamp_string


def clean_output(func_input, suppress_lower: bool = False, suppress_upper: bool = False):
    """
    If the parameter 'suppress_lower' is set to 'True', the line made up of 100 '-' characters
    at the bottom of the formatted list/tuple/dict output will not be printed.

    If the parameter 'suppress_upper' is set to 'True', the line made up of 100 '-' characters
    at the top of the formatted list/tuple/dict output will not be printed.

    Returns clean output:

    1. If the input is a dictionary, its items get printed as f'{key} = {value}' strings line by line

    2. If the input is a List or Tuple, its items get printed as strings line by line

    3. If the input is a float and it has an equivalent integer value, then that value is printed. Else, the original
    value is printed rounded to  2 decimal places
    """
    if type(func_input) == dict:  # Clean printing dict items as f'{key} = {value}' strings line by line
        if not func_input:
            return ''

        clean_string = ''

        if not suppress_upper:
            clean_string += '-' * 100 + '\n'

        type_of_dict_keys = type(list(func_input.keys())[0])
        type_of_dict_values = type(list(func_input.values())[0])

        # Converting dictionary keys that are Timestamp objects to date strings before printing

        if type_of_dict_keys == Timestamp:
            func_input = {time_stamp_to_string(key) : value for key, value in func_input.items()}

        # Converting dictionary keys that are Timestamp objects to date strings before printing,
        # if each value in the 'func_input' dictionary is itself a dictionary with its keys
        # being Timestamp objects.

        # The below code is basically used for clean printing the tolerance groups generated by
        # the 'create_tolerance_group()' function in the 'finance_tools' module.
        # tolerance_groups: dict[float, dict[Timestamp, float]]

        if type_of_dict_values == dict and type(list(list(func_input.values())[0].keys())[0]) == Timestamp:
            func_input_modified = {}
            for key, value_dict in func_input.items():
                value_dict_modified = {time_stamp_to_string(inner_key) : inner_value for inner_key, inner_value in value_dict.items()}
                func_input_modified[key] = value_dict_modified
            func_input = func_input_modified

        clean_string += '\n\n'.join([f'{key}   =   {value}' for key, value in func_input.items()]) + '\n'

        if not suppress_lower:
            clean_string += '-' * 100 + '\n'

        return clean_string

    elif type(func_input) in [list, tuple]:  # Clean printing Sequence items as strings line by line

        if not func_input:
            return ''
        
        clean_string = ''
        
        if not suppress_upper:
            clean_string += '-' * 100 + '\n'
        
        if type(func_input[0]) == str:
            clean_string += '\n\n'.join(func_input) + '\n'
        elif type(func_input[0]) == tuple:

            # The below code is basically used for clean printing the index groups generated by and in
            # the 'manipulate_groups()' function in the 'finance_tools' module.
            # index_groups: list[tuple[int, dict[Timestamp, float]]]

            if type(func_input[0][1]) == dict and type(list(func_input[0][1].keys())[0]) == Timestamp:
                func_input_modified = []
                for tuple_value in func_input:
                    dict_value = tuple_value[1]
                    dict_value_modified = {time_stamp_to_string(inner_key) : inner_value for inner_key, inner_value in dict_value.items()}
                    modified_tuple_value = (tuple_value[0], dict_value_modified)
                    func_input_modified.append(modified_tuple_value)
                func_input = func_input_modified


            clean_string += '\n\n'.join([str(item) for item in func_input]) + '\n'
        
        if not suppress_lower:
            clean_string += '-' * 100 + '\n'
        
        return clean_string
    
    elif type(func_input) == float:
        # Clean printing float values that are integers as integers.
        # Otherwise they are rounded to the second decimal place.
        if func_input.is_integer():
            clean_string = int(func_input)
            return clean_string
    
        else:
            clean_string = str(round(func_input, 2))
            return clean_string
    
    else:
        return func_input


def format_print(func_input, suppress_lower: bool = False, suppress_upper: bool = False, file=None) -> None:
    """
       If the parameter 'suppress_lower' is set to 'True', the line made up of 100 '-' characters
       at the bottom of the formatted list/tuple/dict output will not be printed.

       If the parameter 'suppress_upper' is set to 'True', the line made up of 100 '-' characters
       at the top of the formatted list/tuple/dict output will not be printed.

       If the parameter 'file' is not 'None', then the output of this function
       is written to the file associated with the file object specified in the
       'file' attribute.

       Prints formatted output:

       1. If the input is a dictionary, its items get printed as f'{key} = {value}' strings line by line

       2. If the input is a List or Tuple, its items get printed as strings line by line

       3. If the input is a float and it has an equivalent integer value, then that value is printed. Else, the original
       value is printed rounded to  2 decimal places
       """
    format_print_obj = clean_output(func_input, suppress_lower, suppress_upper)
    if file is not None:
        print(format_print_obj, file=file)
    else:
        print(format_print_obj)


def print_full(df: DataFrame, num: int = 2, truncated: bool = True, true_date: bool = False) -> None:
    """
    Prints truncated pandas dataframe with all columns displayed

    The parameter 'num' with default value '2' sets the number of decimal
    places to which float values in the dataframe will be rounded

    The parameter 'truncated' when set to 'False' will cause the
    function to print the entire dataframe with all rows and columns displayed

    The parameter 'true_date' when set to 'True' will cause the function to
    display the dates in the DataFrame as Timestamp objects. Otherwise, 
    they will be displayed as date strings with the format f'{month} {day}, {year}'.
    Eg. 'Aug 24, 2020'
    """
    if not truncated:
        pd.set_option('display.max_rows', None)

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 2000)
    pd.set_option('display.float_format', f'{{:20,.{num}f}}'.format)
    pd.set_option('display.max_colwidth', None)

    # Creating a deep copy of the dataframe so that when we convert
    # the Timestamps in the 'date' column to date strings, these
    # changes aren't reflected in the original DataFrame

    df_copy = df.copy(deep=True)

    # Converting Timestamps in the 'date' column to date strings

    if not true_date:
        df_copy.date = df_copy.date.apply(time_stamp_to_string) 

    print(df_copy)

    if not truncated:
        pd.reset_option('display.max_rows')

    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.float_format')
    pd.reset_option('display.max_colwidth')


def text_file_to_pdf(text_file: str, pdf_name: str):
    """
    This function takes a text file as input, converts it into 
    a PDF and deletes the original text file.

    The parameters 'text_file' and 'pdf_name' take the 
    text file name and pdf_name as inputs respectively.
    """
    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", size=15)

    if not text_file.endswith('.txt'):
        text_file += '.txt'

    with open(text_file) as text_file_object:
        for line in text_file_object:
            pdf.cell(200, 10, txt=line, ln=1)
    
    os.remove(text_file)
    pdf.output(pdf_name)


def list_of_dicts_to_csv(list_of_dicts: list[dict], file_name: str):
    """
    This function takes a list of dictionaries as input and converts it
    into a csv file with the name 'file_name'.

    The 'file_name' can be provided with or without the '.csv' file
    extension.
    """
    if not file_name.endswith('.csv'):
        file_name = f'{file_name}.csv'

    with open(file_name, 'w', encoding='utf8', newline='') as output_file:
        # Gets fieldnames from the first dictionary in the list 
        
        dw = csv.DictWriter(output_file, fieldnames=list_of_dicts[0].keys())

        dw.writeheader()
        dw.writerows(list_of_dicts)


def dataframe_to_dict(table: DataFrame) -> dict:
    """
    This function converts a DataFrame with 2 columns to 
    a dictionary with key - value pairs from the first
    and second columns respectively.
    """
    values_dict = {}
    columns = table.columns
    column1_name = columns[0]
    column2_name = columns[1]
    
    for index, row in table.iterrows():
        values_dict[row[column1_name]] = row[column2_name]
    return values_dict
