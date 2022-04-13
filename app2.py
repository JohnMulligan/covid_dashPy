import dash
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
import numpy as np
import pandas as pd
import json
import re
import time
from vars import *


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

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
## Have to choose this because the unweighted counts only exist for all-cause mortality, not for all-cause-excluding-covid
df=df[df['Type']=='Predicted (weighted)']

#4. Categorical Select
outcomes=pd.unique(df['Outcome'])

controls=dbc.Card(
	[
		html.Div(
			dcc.DatePickerRange(
				id='daterangepicker',
				min_date_allowed=pd.Timestamp(min(daterange)),
				max_date_allowed=pd.Timestamp(max(daterange)),
				start_date=pd.Timestamp(np.datetime64('2020-01-01')),
				end_date=pd.Timestamp(max(daterange))
			),
			style = {"width": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center"}
		),
		html.Div(
			dcc.RadioItems(
				outcomes,
				outcomes[0],
				inline=False,
				id='outcomes_radio',
				inputStyle={"marginLeft": "10px","marginRight":"3px"}
			),
			style = {"width": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center"}
		),
		html.Hr(),
		html.P("",id="para")
	],
	body=True
)

app.layout = dbc.Container(
	
	[	
		dcc.Store(id="selected_states"),
		dbc.Row(
			[	
				html.A("An adaptation of the CDC's COVID-19 excess mortality dashboard.",href="https://www.cdc.gov/nchs/nvss/vsrr/covid19/excess_deaths.htm")
			],
			style={"height": "3vh"}
		),
		dbc.Row(
			[
				dbc.Col(controls,md=4),
				dbc.Col(dcc.Graph(id="choropleth_map"),md=8)
			],
			align="center",
			style={"height": "43vh"}
		),
		dbc.Row(
			[
				dbc.Col(dcc.Graph(id="graph"),md=12)
			],
			align="center",
			style={"height": "43vh"}
		)
	]
)


#store the data on
##which states are selected
##and the appropriately-formatted text to display based on that
@app.callback(
	Output('selected_states','data'),
	Input('choropleth_map', 'selectedData')
	)
def select_states(clickData):
	
	output_data={'raw_selection_data':clickData}
	
	print("????",clickData)
	
	if clickData is not None:
		selectedstates=[inverse_state_abbv_map[p['location']] for p in clickData['points']]
	else:
		selectedstates=["United States"]
	
	output_data['selected_states']=selectedstates
	
	if selectedstates==["United States"]:
		selectedstates_string="the United States"
	else:
		#bingo! https://stackoverflow.com/a/19839338
		selectedstates_string=", ".join(selectedstates[:-2] + [" and ".join(selectedstates[-2:])])
	
	output_data['selectedstates_string']=selectedstates_string
	
	return output_data

@app.callback(
	Output('graph', 'figure'),
	Output('para','children'),
	Input('daterangepicker', 'start_date'),
	Input('daterangepicker', 'end_date'),
	Input('selected_states', 'data'),
	Input('outcomes_radio','value')
	)
def line_graph(start_date,end_date,selected_states_data,outcome):
	
	filtered=df[df['Outcome']==outcome]
	filtered=filtered[filtered['Week Ending Date']>=start_date]
	filtered=filtered[filtered['Week Ending Date']<=end_date]
	
	selectedstates=selected_states_data['selected_states']
	selectedstates_string=selected_states_data['selectedstates_string']
	
	df2=filtered[filtered['State'].isin(selectedstates)]
	df2=df2[df2['Outcome']==outcome]
	
	total_excess=int(df2["Excess Estimate"].sum())
	
	#CDC's total excess column in this sheet is lower than this -- they may be accidentally counting the negatives?
	
	if len(selectedstates)>1:
		#can't simply add up the alarms across states
		df2=df2.groupby("Week Ending Date").sum()
		alarmlabels=[]
		excess_alarms_text=""

	else:
		alarmlabels=df2["Alarm"]
		excessweekscount=df2["Exceeds Threshold"].sum()
		total_weeks=len(alarmlabels)
		excess_alarms_text="%s of %s weeks in this time period exceeded the 95 percent CI upper bound for predicted mortality." %(str(excessweekscount),str(total_weeks))
		excess_alarms_text = excess_alarms_text
		
	df2.reset_index(inplace=True)	
	
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
		text=alarmlabels,
		textposition="top center"
	))
	
	fig.update_layout(title="Weekly Excess Mortality (%s) in %s" %(outcome,selectedstates_string))
	
	start_date_str=re.search("[0-9]+-[0-9]+-[0-9]+",str(start_date)).group(0)
	end_date_str=re.search("[0-9]+-[0-9]+-[0-9]+",str(end_date)).group(0)
	start_year=start_date_str[0:4]
	end_year=end_date_str[0:4]
	
	excess_mortality_text="Between %s and %s, %s more people died than would have been expected in %s, based on historical averages." %(start_date_str,end_date_str,f"{total_excess:,}",selectedstates_string)
	
	output_text = ' '.join([excess_mortality_text,excess_alarms_text])
	
	return(fig,output_text)

@app.callback(
		Output('choropleth_map', 'figure'),
		Input('daterangepicker', 'start_date'),
		Input('daterangepicker', 'end_date'),
		Input('selected_states', 'data'),
		Input('outcomes_radio','value')
	)
def update_output(start_date,end_date,selected_states_data,outcome):	
	
	
	
	try:
		selectedData=[p['pointIndex'] for p in  selected_states_data['raw_selection_data']['points']]
	except:
		selectedData=None
	
	print("--->",selectedData)
	
	#B. SELECTING
	filtered=df[df['Outcome']==outcome]
	filtered=filtered[filtered['Week Ending Date']>=start_date]
	filtered=filtered[filtered['Week Ending Date']<=end_date]

	numberofweeks=len(pd.unique(filtered['Week Ending Date']))

	#https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.core.groupby.DataFrameGroupBy.aggregate.html?highlight=aggregate#pandas.core.groupby.DataFrameGroupBy.aggregate

	#C. GROUPING

	#first the state-by-state summaries
	grouped=filtered.groupby('State_Abbv').agg(
			{
				'Total Excess Estimate': 'max',
				'Exceeds Threshold': 'sum'
			}
		)

	grouped=grouped.rename(columns={'Exceeds Threshold':'Weeks Exceeding Threshold'})

	grouped['Percent Weeks Exceeding Threshold']=100*grouped['Weeks Exceeding Threshold']/numberofweeks
	
	#styling: https://plotly.github.io/plotly.py-docs/generated/plotly.graph_objects.Choropleth.html

	fig = go.Figure(data=go.Choropleth(
		locations=grouped.index,
		z = grouped['Percent Weeks Exceeding Threshold'],
		locationmode = 'USA-states',
		colorscale="Reds",
		customdata=[grouped.index,grouped['Percent Weeks Exceeding Threshold']]
	))

	fig.update_layout(
		title_text = 'Percent of weeks exceeding 95% CI upper bound threshold',
		geo_scope='usa',
		dragmode=False
	)

	fig.update_traces(
		colorbar=dict(
		ticktext = ["20","40","60","80"],
		tickvals = [20,40,60,80],
		tickmode="array"
		),
		zauto=False,
		zmin=0,
		zmax=100,
		selectedpoints=selectedData
	)
	
	fig.update_layout(clickmode='event+select')
	
	return fig


if __name__ == '__main__':
	app.run_server(debug=True)