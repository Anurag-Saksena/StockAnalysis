import os
from finance_tools import summary_multiple

os.chdir(r'c:\Users\anura\VSCodeProjects')

stock_names_list = ['TATAMOTORS', 'AARTIIND', 'TATACOFFEE', 'HDFC', 'HDFCBANK']

summary_multiple(stock_names_list, volume=True, relevant_regions=True, dark_mode=True)