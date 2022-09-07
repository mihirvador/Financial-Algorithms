import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

asset = input("Select an Asset to Trade: ")
datestart = input("Start date of backtest: ")

if asset == "" or datestart == "":
    asset = 'MSFT' # The asset to trade, currently it is Amazon
    datestart = '2020-01-01' # How long ago the back test should occur

stop_loss = -0.5 # If a 50% loss occurs, the program issues a sell call, and then exits the program to stop further loss.
notify_loss = -0.2 # If a 20% loss occurs, the program issues a sell call, and then conducts no trades for the next "waitdays" trading days
waitdays = 5 # The number of days to halt trading after a 30% loss, currently 5 trading days or 1 week.

df = yf.download(asset, start=datestart) # Getting backtesting data

df.loc[:, 'SMA'] = df.Close.rolling(window=20).mean() # Get the 20 day simple moving average

df.loc[:, 'stddev'] = df.Close.rolling(window=20).std() # Get the 20 day standard deviation

df.loc[:, 'Upper'] = df.SMA + 2*df.stddev # Calculate the upper bound of the Bollinger Band
df.loc[:, 'Lower'] = df.SMA - 2*df.stddev # Calculate the lower bound of the Bollinger Band

df.loc[:, 'Buy_Signal'] = np.where(df.Lower > df.Close, True, False) # Buy if the closing price goes below the lower bound
df.loc[:, 'Sell_Signal'] = np.where(df.Upper < df.Close, True, False) # Sell if the closing price goes above the upper bound
df.loc[:, 'Holding'] = 0
df.loc[:, 'Bought'] = 0
df.loc[:, 'Sold'] = 0
df.loc[:, 'Buy_Price'] = 0.0
df.loc[:, 'Curr_Profit'] = 0.0
df.loc[:, 'Circuitbreaker'] = False
df = df.dropna()

# plt.figure(figsize=(12,6))
# plt.plot(df[['Close', 'SMA', 'Upper', 'Lower']])
# plt.scatter(df.index[df.Buy_Signal], df[df.Buy_Signal].Close, marker = '^', color='g')
# plt.scatter(df.index[df.Sell_Signal], df[df.Sell_Signal].Close, marker = 'v', color='r')
# plt.fill_between(df.index, df.Upper, df.Lower, color='grey', alpha=0.3)
# plt.legend(['Close', 'SMA', 'Upper', 'Lower'])
# plt.show()

open_pos = False
Buy_Price = 0.0
circuitbreaker = 0
# Conducting Backtest
for i in df.index:
    if circuitbreaker != 0: # Checking for stopped testing days
        df.at[i, 'Circuitbreaker'] = True
        circuitbreaker = circuitbreaker - 1
        continue
    if open_pos: # Checking if currently holding
        df.at[i, 'Holding'] = 1
        if Buy_Price == 0.0:
            Buy_Price = df.loc[i, 'Open']
            df.at[i, 'Buy_Price'] = Buy_Price
        elif Buy_Price != 0.0:
            df.at[i, 'Buy_Price'] = Buy_Price
        df.at[i, 'Curr_Profit'] = (df.at[i, 'Open'] - Buy_Price)/Buy_Price # Calculating Profit
    elif open_pos == False:
        df.at[i, 'Holding'] = 0
        Buy_Price = 0.0
    if open_pos:
        if df.Upper[i] < df.Close[i]:  # If conditions are met then sell
            df.at[i, 'Sold'] = 1
            open_pos = False
        if df.loc[i, 'Curr_Profit'] < stop_loss: # Checking for stop loss, aka 50% loss
            df.at[i, 'Sold'] = 1
            open_pos = False
            break
        if df.loc[i, 'Curr_Profit'] < notify_loss: # Checking for "waitdays", aka 20% loss
            df.at[i, 'Sold'] = 1
            open_pos = False
            circuitbreaker = waitdays
    elif open_pos == False:
        if df.Lower[i] > df.Close[i]: # If conditions are met then buy 
            df.at[i, 'Bought'] = 1
            open_pos = True


df['Bought'] = df['Bought'].shift(1, fill_value=0)
df['Sold'] = df['Sold'].shift(1, fill_value=0)
#print(df)

plt.figure(figsize=(12,6))
plt.plot(df[['Close', 'SMA', 'Upper', 'Lower']])
plt.scatter(df[df['Bought'] == 1].index, df[df['Bought'] == 1].Open, marker = '^', color='g')
plt.scatter(df[df['Sold'] == 1].index, df[df['Sold'] == 1].Open, marker = 'v', color='r')
plt.fill_between(df.index, df.Upper, df.Lower, color='grey', alpha=0.3)
plt.legend(['Close', 'SMA', 'Upper', 'Lower'])
plt.show() # Display bought as green arrow, and sold as red arrow

merged = pd.concat([df[df['Bought'] == 1].Open, df[df['Sold'] == 1].Open, df[df['Circuitbreaker'] == True].Circuitbreaker], axis=1)
merged.columns = ['Buys', 'Sells', 'Circuitbreaker']
print(merged) # Show all buys and sells along with non-trading days

# Calculate total profit
totalprofit = merged.shift(-1).Sells - merged.Buys
relprofit = (merged.shift(-1).Sells - merged.Buys)/merged.Buys
relprofit = relprofit.dropna()
totalrelprofit = 1
for i in relprofit:
    totalrelprofit = totalrelprofit * (1+i)
print("Total profit is: " + str(totalrelprofit*100-100) + "%") # Show total profit