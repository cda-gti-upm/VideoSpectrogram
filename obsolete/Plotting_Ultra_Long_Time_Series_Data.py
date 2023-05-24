# https://towardsdatascience.com/6-visualization-tricks-to-handle-ultra-long-time-series-data-57dad97e0fc2

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# Read the CSV file
df = pd.read_csv('dly532.csv')
df['date'] = pd.to_datetime(df['date'])
print(df.tail())

#Explore data
df.info()

# Prepare data
start = pd.Timestamp('1990-01-01')
end = pd.Timestamp('2021-12-31')
df_temp = df[(df['date']>=start)&(df['date']<=end)][['date','maxtp','mintp']]
df_temp.reset_index(drop=True, inplace=True)

#create an average temperature column
df_temp['meantp'] = [(i+j)/2 for i,j in zip(df_temp.maxtp, df_temp.mintp)]
print(df_temp.head())

df_temp['month'] = pd.DatetimeIndex(df_temp['date']).month
df_temp['year'] = pd.DatetimeIndex(df_temp['date']).year
df_temp['month_year'] = [str(i)+'-'+str(j) for i,j in zip(df_temp.year, df_temp.month)]
print(df_temp.head())

# Plot the time-series plot
plt.figure(figsize=(16,9))
sns.set_style('darkgrid')
sns.lineplot(data=df_temp, y='meantp', x ='date')
plt.show()

# Trick #1: Zoom in and zoom out
fig = px.line(df_temp, x='date', y='meantp')
fig.show()