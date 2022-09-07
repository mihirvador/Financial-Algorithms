import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import matplotlib
from sklearn.preprocessing import MinMaxScaler
from keras.layers import LSTM, Dense, Dropout
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib. dates as mandates
from sklearn.preprocessing import MinMaxScaler
from sklearn import linear_model
from keras.models import Sequential
from keras.layers import Dense
import keras.backend as K
from keras.callbacks import EarlyStopping
from keras.models import load_model
from keras.layers import LSTM
from keras.utils.vis_utils import plot_model
from pandas_datareader import data as pdr
import yfinance as yf

asset = input("Select an Asset to Trade: ")

if asset == "":
    asset = 'GOOG' # The asset to trade, currently it is Google
datestart = '2020-01-01' # How long ago the back test should occur

datesframe = yf.download(asset, start=datestart, end='2022-03-11')
df = datesframe

#Print the shape of Dataframe  and Check for Null Values
print("Dataframe Shape: ", df.shape)
print("Null Value Present: ", df.isnull().values.any())

df1=df.reset_index()['Close']

#Plot the True Adj Close Value
df = df1
# plt.plot(df)
# plt.show()

scaler=MinMaxScaler(feature_range=(0,1))
df1=scaler.fit_transform(np.array(df1).reshape(-1,1))

training_size=int(len(df1)*0.65)
test_size=len(df1)-training_size
train_data,test_data=df1[0:training_size,:],df1[training_size:len(df1),:1]

def create_dataset(dataset, time_step=1):
        dataX, dataY = [], []
        for i in range(len(dataset)-time_step-1):
                a = dataset[i:(i+time_step), 0]
                dataX.append(a)
                dataY.append(dataset[i + time_step, 0])
        return np.array(dataX), np.array(dataY)
time_step = 100
X_train, y_train = create_dataset(train_data, time_step)
X_test, ytest = create_dataset(test_data, time_step)

X_train =X_train.reshape(X_train.shape[0],X_train.shape[1] , 1)
X_test = X_test.reshape(X_test.shape[0],X_test.shape[1] , 1)

#Building the LSTM Model
model=Sequential()
model.add(LSTM(50,return_sequences=True,input_shape=(100,1)))
model.add(LSTM(50,return_sequences=True))
model.add(LSTM(50))
model.add(Dense(1))
model.compile(loss='mean_squared_error',optimizer='adam')

#Model Training
history=model.fit(X_train, y_train, epochs=100, batch_size=8, verbose=1, shuffle=False)
model.save("Google/model.h5")

#LSTM Prediction
train_predict=model.predict(X_train)
test_predict=model.predict(X_test)
train_predict=scaler.inverse_transform(train_predict)
test_predict=scaler.inverse_transform(test_predict)

math.sqrt(mean_squared_error(y_train,train_predict))

#Predicted vs True Adj Close Value – LSTM
x_data = range(552)
plt.plot(x_data[:], df)
plt.plot(x_data[98:355], train_predict, label='Train Value')
plt.plot(x_data[456:549], test_predict, label='Predict Value')

plt.title("Prediction by LSTM")
plt.xlabel('Time Scale')
plt.ylabel('USD')
plt.legend()
plt.show()