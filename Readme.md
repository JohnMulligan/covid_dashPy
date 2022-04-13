# Adaptation of CDC's All-Cause Excess Mortality Dashboard

This repo uses CDC data on excess mortality (generated to estimate the impacts of COVID-19) as an exercise in quickly building and deploying interactive data visualizations to the web, because these are the cornerstone of exploratory data analysis.

csv from: https://data.cdc.gov/api/views/xkkf-xrst/rows.csv?accessType=DOWNLOAD&bom=true&format=true%20target=

## Core technologies

The following frameworks and services are used:

* Free, curated data from the CDC
* Python
* Pandas
* Plotly (Dash)
* Heroku

## Setting up your environment (Python)

In order to run through this exercise, you will need Python 3 installed, and specific packages for it. It's best to set up a virtual environment so that you can record the specifics of your installation, in order for a web server to rebuild that later on.

1. Open a terminal

*navigate to this folder*, and initialize a Python virtual environment.

	python3 -m venv venv

This command invokes the python module "venv"
	
2. Initialize the virtual environment

Its source files live in the folder you created with the above command (the second "venv")

	source venv/bin/activate
	
3. Install the packages

These are listed in requirements.txt

	pip3 install -r requirements.txt

4. You're good to go! Try running an app.

	python app.py

## Running the applications in this repo

These applications are single-page apps rendered in React on top of Flask. Plotly is truly excellent when you want to quickly make a dataset visually interactive. The curve is a steep one as you ask for more functionality, FYI.

There are two apps in this repo. Each can be run simply by invoking the file in python (from within the virtual environment), like:

	python app.py
	python scatter.py

### What do the apps do?

1. scatter.py: this application shows
	1. For the weeks since January 1, 2020:
	1. The number of people who
		1. were expected to die in Texas, week by week
		1. actually died in excess of that number
	1. These numbers are stacked up to show the excess mortality
	1. For weeks where the death rate was exceptionally high (above the 95% CI upper bound as determined by a Farrington outbreak detection algorithm), an "x" has been tagged to the top of the week
1. app.py: this application shows
	1. for the weeks since January 1, 2020:
	1. A multi-select geographic heatmap ("choropleth")
		1. of the United States
		1. showing the percentage of weeks that rose above the 95% CI upper bound predicted mortality for that state based on historical data
	1. The number of people who
		1. Were expected to die in any state or combination of states
		1. As selected in the choropleth
		1. And, if only one state or the entire US is selected, it flags the exceptionally high weeks with an "x"

## Deploying to heroku

If you make changes, you'll want to test, perhaps alter your app's structure or its required packages or its underlying data, etc. That is beyond the scope of this exercise but have fun!

### First

1. Get a Heroku account (free)
1. Log in via the command line

### Then

	heroku create my-dash-app # change my-dash-app to a unique name
	git push heroku main # deploy code to heroku
	heroku ps:scale web=1  # run the app with a 1 heroku "dyno"

(from https://dash.plotly.com/deployment)
