from dash import Dash, html, dcc, Input, Output
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
import numpy as np
import pandas as pd
import json
from vars import *

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

df=pd.read_csv('Excess_Mortality_Estimates.csv')
#EASY DATATABLE
#app.layout = dash_table.DataTable(df.to_dict('records'), [{"name": i, "id": i} for i in df.columns])

#A. FORMATTING

#1. map states to their abbreviations
df['State_Abbv']=df['State'].map(state_abbv_map)
df['Alarm']=df['Exceeds Threshold'].map({True:"X",False:None})

inverse_state_abbv_map={state_abbv_map[k]:k for k in state_abbv_map}

#2. format & extract dates
#https://pandas.pydata.org/docs/user_guide/timeseries.html
df['Week Ending Date'] = pd.to_datetime(df['Week Ending Date'])

df=df.sort_values("Week Ending Date")

daterange=list(pd.unique(df['Week Ending Date']))

#3. PRELIM filtering
count_type='Predicted (weighted)'
df=df[df['Type']==count_type]

jurisdictions=["TX"]
outcome='All causes'
#alval="All causes, excluding COVID-19"

df2=df[df['State_Abbv'].isin(jurisdictions)]
print(df2)
df2=df2[df2['Outcome']==outcome]
print(df2)


fig=go.Figure()


fig.add_trace(go.Scatter(
	x=df2["Week Ending Date"],
	y=df2["Average Expected Count"],
	name="Average Expected Count",
	mode="lines",
	stackgroup="one",
	line_shape="spline"
))

fig.add_trace(go.Scatter(
	x=df2["Week Ending Date"],
	y=df2["Excess Estimate"],
	name="Excess Estimate",
	mode="lines+text",
	stackgroup="one",
	line_shape="spline",
	text=df2["Alarm"],
	textposition="top center"
))


fig.show()