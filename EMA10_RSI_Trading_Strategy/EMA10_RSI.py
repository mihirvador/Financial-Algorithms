import yfinance as yf
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import talib
import numpy as np
import matplotlib.pyplot as plt

asset = input("Select an Asset to Trade: ")
datestart = input("Start date of backtest: ")

if asset == "":
    asset = 'TSLA' # The asset to trade, currently it is Tesla
    datestart = '2020-01-01' # How long ago the back test should occur

stop_loss = -0.7 # If a 70% loss occurs, the program issues a sell call, and then exits the program to stop further loss.
notify_loss = -0.3 # If a 30% loss occurs, the program issues a sell call, and then conducts no trades for the next "waitdays" trading days
waitdays = 5 # The number of days to halt trading after a 30% loss, currently 5 trading days or 1 week.
    

frames = yf.download(asset, start=datestart) # Getting backtesting data
# for i in datesframe.index:
#     temp = yf.download(asset, start=i, end=i + dt.timedelta(days=1))
#     temp = pd.DataFrame(temp)
#     temp = temp[:-1]
#     frames.append(temp)

# frames = pd.concat(frames)

# frames.head()
frames.loc[:, 'EMA10'] = frames['Close'].ewm(span=10, adjust=False).mean() # Calculating the 10 day moving exponential average

frames.loc[:, "RSI"] = talib.RSI(frames.Close, 14) # Calculating the 2 week RSI Exponential
frames = frames.iloc[14:]
#print(frames)
df = frames

# Issuing a buy signal whenever the closing price is less than the 10 day EMA and if the 2 week RSI is greater than 30 but less than 70
df.loc[:, 'Buy_Signal'] = np.where((df.Close <= df.EMA10) & (df.RSI <= 30), True, False) 
# Issuing a sell signal whenever the closing price is greater than the 10 day EMA and if the 2 week RSI is greater than 70
df.loc[:, 'Sell_Signal'] = np.where((df.Close >= df.EMA10) & (df.RSI >= 70), True, False)


df.loc[:, 'Holding'] = 0
df.loc[:, 'Bought'] = 0
df.loc[:, 'Sold'] = 0
df.loc[:, 'Buy_Price'] = 0.0
df.loc[:, 'Curr_Profit'] = 0.0
df.loc[:, 'Circuitbreaker'] = False
df = df.dropna()

open_pos = False
Buy_Price = 0.0
circuitbreaker = 0
# Conducting Backtest
for i in df.index:
    if circuitbreaker != 0: # Checking for stopped testing days
        df.loc[i, 'Circuitbreaker'] = True
        circuitbreaker = circuitbreaker - 1
        continue
    if open_pos: # Checking if currently holding
        df.loc[i, 'Holding'] = 1
        if Buy_Price == 0.0:
            Buy_Price = df.loc[i, 'Open']
            df.loc[i, 'Buy_Price'] = Buy_Price
        elif Buy_Price != 0.0:
            df.loc[i, 'Buy_Price'] = Buy_Price
        df.loc[i, 'Curr_Profit'] = (df.loc[i, 'Open'] - Buy_Price)/Buy_Price # Calculating Profit
    elif open_pos == False:
        df.loc[i, 'Holding'] = 0
        Buy_Price = 0.0
    if open_pos:
        if ((df.Close[i] >= df.EMA10[i]) & (df.RSI[i] >= 70)): # If conditions are met then sell 
            df.loc[i, 'Sold'] = 1
            open_pos = False
        if df.loc[i, 'Curr_Profit'] < stop_loss: # Checking for stop loss, aka 70% loss
            df.loc[i, 'Sold'] = 1
            open_pos = False
            break
        if df.loc[i, 'Curr_Profit'] < notify_loss: # Checking for "waitdays", aka 30% loss
            df.loc[i, 'Sold'] = 1
            open_pos = False
            circuitbreaker = waitdays
    elif open_pos == False:
        if ((df.Close[i] <= df.EMA10[i]) & (df.RSI[i] <= 30)): # If conditions are met then buy 
            df.loc[i, 'Bought'] = 1
            open_pos = True


df.loc[:, 'Bought'] = df.loc[:, 'Bought'].shift(1, fill_value=0)
df.loc[:, 'Sold'] = df.loc[:, 'Sold'].shift(1, fill_value=0)
#print(df) 

plt.figure(figsize=(12,6))
plt.plot(df[['Close', 'EMA10']])
plt.scatter(df[df['Bought'] == 1].index, df[df['Bought'] == 1].Open, marker = '^', color='g')
plt.scatter(df[df['Sold'] == 1].index, df[df['Sold'] == 1].Open, marker = 'v', color='r')
plt.legend(['Close', 'EMA10'])
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

