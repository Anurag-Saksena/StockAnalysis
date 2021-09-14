# StockAnalysis

This program analyses the data of multiple stocks to generate and subsequently filter support and resistance levels for those stocks.

# Introduction:

The main objective in stock trading is to buy a stock at as low a price as possible and sell it at as high a price as possible. But, since stock prices fluctuate a lot over both the short term and the long term, it's hard to determine when to buy or sell.

This is where support and resistance levels come in. Over a long term (6 months or more), stock price movements follow certain patterns. Support levels are price levels to which a stock's price fell only to rebound and increase again. Similarly, resistance levels are price levels to which a stock's price rose only to rebound and decrease again. The more times a stock's price hits a support or resistance level and rebounds, the more reliable that support/resistance level is, as a price barrier.

Ideally, you should try to buy a stock when it hits a support level and sell it before it reaches a resistance level.

# What this program does:

This program takes a list of stock names as input in the 'main.py' file and for each of these stocks, it imports their historical data using the Zerodha Kite Connect Python API.

It then finds the support and resistance levels for each of these stocks. These levels can further be filtered on the basis of price at support/resistance, the number of times the support/resistance level held, the number of days between each rebound etc. 

After calculating the support/resistance levels for each stock, this program plots a Candlestick chart for the stock data where these levels are visible.

# Info:

Since this program connects to the Zerodha Python API which is connected to a Bank account, the values of the 'api_key' and 'api_secret' in the code have been removed. However sample inputs and outputs are present in the 'Sample inputs and outputs.pdf' file.


