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
from vars import *

####### INTITIALIZE THE APP & LOAD THE DATA #######

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
df=pd.read_csv('Excess_Mortality_Estimates.csv')

####### PRELIM FORMATTING AND FILTERING #######

# 1. map states to their abbreviations
df['State_Abbv']=df['State'].map(state_abbv_map)
df['Alarm']=df['Exceeds Threshold'].map({True:"X",False:None})
inverse_state_abbv_map={state_abbv_map[k]:k for k in state_abbv_map}

# 2. FORMAT & EXTRACT DATES
## https://pandas.pydata.org/docs/user_guide/timeseries.html
df['Week Ending Date'] = pd.to_datetime(df['Week Ending Date'])
df=df.sort_values("Week Ending Date")
daterange=list(pd.unique(df['Week Ending Date']))

# 3. PRELIM filtering
## Have to choose this because the unweighted counts only exist for all-cause mortality, not for all-cause-excluding-covid
df=df[df['Type']=='Predicted (weighted)']

#4. Categorical Selectors (to be used in radio options below)
outcomes=pd.unique(df['Outcome'])

####### APP PAGE LAYOUT #######

## We use Dash Bootstrap Components below.
## Documentation: https://dash-bootstrap-components.opensource.faculty.ai/docs/components/layout/

## The controls get to be a bit much in the main layout (below), so I've broken them out.
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
			style = {"alignItems": "center", "justifyContent": "center"}
		),
		html.Div(
			[
			dcc.RadioItems(
				outcomes,
				outcomes[0],
				inline=False,
				id='outcomes_radio',
				inputStyle={"marginLeft": "10px","marginRight":"3px"}
			),
			html.Hr()
			],
			style = {"alignItems": "center", "justifyContent": "center"}
		),
		html.Div(
			[
				html.P("",id="para",style={"margin":"10px"})
			]
		)
	]
)

## Main app layout
app.layout = dbc.Container(
	[
		dbc.Row(
			[	
				dbc.Col(
					html.A(
						"An adaptation of the CDC's COVID-19 excess mortality dashboard.",
						href="https://www.cdc.gov/nchs/nvss/vsrr/covid19/excess_deaths.htm",
						style={"margin":"10px"}
					)
				),
			],
		),
		dbc.Row(
			[
				dbc.Col(
					html.Div(
						[controls]
					),
					width=12,xs=12,sm=12,md=12,lg=6
				),
				dbc.Col(
					html.Div(
						[dcc.Graph(id="choropleth_map")]
					),
					width=12,xs=12,sm=12,md=12,lg=6
				)
			]
		),
		dbc.Row(
			html.Div(
				[
					dcc.Graph(id="graph")
				],
			)
		)
	]
)

####### CALLBACKS (Robust Interactivity) #######

# Update the scatter plot and the explanatory text when:
## The date picker is used
## The radio buttons are used
## The map selections are used

@app.callback(
    Output('graph', 'figure'),
    Output('para','children'),
	Input('daterangepicker', 'start_date'),
	Input('daterangepicker', 'end_date'),
	Input('choropleth_map', 'selectedData'),
	Input('outcomes_radio','value')
)
def line_graph(start_date,end_date,selectedData,outcome):
	
	## FILTER ON OUTCOME & DATES
	filtered=df[df['Outcome']==outcome]
	filtered=filtered[filtered['Week Ending Date']>=start_date]
	filtered=filtered[filtered['Week Ending Date']<=end_date]
	
	## SELECTED STATES
	### handle one or multiple states, or US
	### build some insertion text for the app
	if selectedData is not None:
		selectedstates=[inverse_state_abbv_map[p['location']] for p in selectedData['points']]
	else:
		selectedstates=["United States"]
	
	if selectedstates==["United States"]:
		selectedstates_string="the United States"
	else:
		# a nice list to comma-separated text converter, with "and" but without oxford comma https://stackoverflow.com/a/19839338
		selectedstates_string=", ".join(selectedstates[:-2] + [" and ".join(selectedstates[-2:])])
	
	### filter on the basis of the selected states
	df2=filtered[filtered['State'].isin(selectedstates)]
	df2=df2[df2['Outcome']==outcome]
	
	### & calculate the total excess
	#### Note: CDC's total excess column in this sheet is lower than this -- they may be accidentally counting the negatives?
	total_excess=int(df2["Excess Estimate"].sum())
	
	## COUNT UP ALARMS
	### but you can't simply add up the alarms across states
	### as that would require re-running the Farrington algo
	### so that has to be disabled on multi-state select
	if len(selectedstates)>1:
		df2=df2.groupby("Week Ending Date").sum()
		alarmlabels=[]
		excess_alarms_text=""
	else:
		alarmlabels=df2["Alarm"]
		excessweekscount=df2["Exceeds Threshold"].sum()
		total_weeks=len(alarmlabels)
		excess_alarms_text="%s of %s weeks in this time period exceeded the 95 percent CI upper bound for predicted mortality." %(str(excessweekscount),str(total_weeks))
		excess_alarms_text = excess_alarms_text

	## "Week Ending Date" is the index because we've grouped by it
	## So push it back into a proper column we can call
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
	
	## Final text formatting
	
	start_date_str=re.search("[0-9]+-[0-9]+-[0-9]+",str(start_date)).group(0)
	end_date_str=re.search("[0-9]+-[0-9]+-[0-9]+",str(end_date)).group(0)
	start_year=start_date_str[0:4]
	end_year=end_date_str[0:4]
	
	excess_mortality_text="Between %s and %s, %s more people died (%s) than would have been expected in %s, based on historical averages." %(start_date_str,end_date_str,f"{total_excess:,}",outcome.lower(),selectedstates_string)
	
	output_text = ' '.join([excess_mortality_text,excess_alarms_text])
	
	return(fig,output_text)

# Update the map when:
## The radio buttons are used: selecting covid only or all causes
## The date picker is used: selecting different date ranges
# Both of the above behaviors change the heatmap
## Which shows percentage of weeks in that range that rise above 95% CI upper bound
@app.callback(
		Output('choropleth_map', 'figure'),
		Input('daterangepicker', 'start_date'),
		Input('daterangepicker', 'end_date'),
		Input('outcomes_radio','value')
)
def update_output(start_date,end_date,outcome):	
	
	## FILTER ON OUTCOME & DATES
	filtered=df[df['Outcome']==outcome]
	filtered=filtered[filtered['Week Ending Date']>=start_date]
	filtered=filtered[filtered['Week Ending Date']<=end_date]
	numberofweeks=len(pd.unique(filtered['Week Ending Date']))

	## GROUPING DEPENDENT ON THE ABOVE FILTERS
	### first the state-by-state summaries
	grouped=filtered.groupby('State_Abbv').agg(
		{
			'Total Excess Estimate': 'max',
			'Exceeds Threshold': 'sum'
		}
	)
	grouped=grouped.rename(columns={'Exceeds Threshold':'Weeks Exceeding Threshold'})
	grouped['Percent Weeks Exceeding Threshold']=100*grouped['Weeks Exceeding Threshold']/numberofweeks
	
	## VARIABLE-DEPENDENT GRAPH STYLING
	### documentation: https://plotly.github.io/plotly.py-docs/generated/plotly.graph_objects.Choropleth.html
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
		# turned off z auto so that when the levels change dramatically, it shows
		# above all, between all deaths / all deaths excluding covid
		zauto=False,
		zmin=0,
		zmax=100
	)
	
	fig.update_layout(clickmode='event+select')
	
	return fig

if __name__ == '__main__':
	app.run_server(debug=False)