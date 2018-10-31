# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np

from toolz import groupby, compose, pluck
from dotenv import load_dotenv
import os
from csv import DictReader

#dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
#load_dotenv(dotenv_path)

MAPBOX_KEY = "pk.eyJ1Ijoibmlja2ZvcmZpbnNraSIsImEiOiJjam51cTNxY2wwMTJ2M2xrZ21wbXZrN2F1In0.RooxCuqsNotDzEP2EeuJng"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

fin = open(r'Z:\QAQC_checks\QAQC_checks\data\bfro_reports_geocoded.csv', 'r')
reader = DictReader(fin)
tile_centroids = [
    line for line in reader
]
fin.close()


df = pd.read_csv(r'Z:\QAQC_checks\QAQC_checks\data\bfro_reports_geocoded.csv')


def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col, 
                style={
                    'textAlign': 'center', 
                    'color': colors['text'], 
                    'padding-top':'1px', 
                    'padding-bottom':'1px', 
                    'text-align':'left'}
            ) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(
                dataframe.iloc[i][col], 
                style={
                    'textAlign': 'center', 
                    'color': colors['text'], 
                    'padding-top':'1px', 
                    'padding-bottom':'1px', 
                    'text-align':'left',
                    'border-bottom':'blue'})  # TODO: not what I wanted, but I like it! (fix)
            for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


listpluck = compose(list, pluck)


def make_bathy_hist_data():
    mu, sigma = 0, 0.1 # mean and standard deviation
    s = np.random.normal(mu, sigma, 1000)
    hist, bin_edges = np.histogram(s, bins=100)
    return (hist, bin_edges)


def bigfoot_map(sightings):
    # groupby returns a dictionary mapping the values of the first field 
    # 'classification' onto a list of record dictionaries with that 
    # classification value.
    classifications = groupby('classification', sightings)
    return {
        "data": [
                {
                    "type": "scattermapbox",
                    "lat": listpluck("latitude", class_sightings),
                    "lon": listpluck("longitude", class_sightings),
                    "mode": "markers",
                    "name": classification,
                    "marker": {
                        "size": 3,
                        "opacity": 1.0
                    }
                }
                for classification, class_sightings in classifications.items()
            ],
        "layout": {
            'margin': {'l': 0, 'r': 0, 't': 0, 'b':0},
            'showlegend': False,
            "autosize": True,
            "hovermode": "closest",
            "mapbox": {
                "accesstoken": MAPBOX_KEY,
                "bearing": 0,
                "center": {
                    "lat": 41.35,
                    "lon": -70.4
                },
                "pitch": 0,
                "zoom": 9,
                "style": "dark"
            }
        }
    }


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
	'background': '#373D42',
	'text': '#B1C4D2',
    'header': '#0968AA'
}

map_button_style = {
    'color': colors['text'],
    'border-color': colors['text'],
    'background-color': colors['background'],
    'border-radius': '50px'}

checks_to_do = {
	'naming_convention': False,
	'version': False,
	'pdrf': False,
	'gps_time': False,
	'hor_datum': False,
	'ver_datum': False,
	'point_source_ids': False,
    'create_dz': True,
    'create_dz': False,
}


app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.Div(style={'backgroundColor':'#00ADEF'}, children=[
        html.Div([
            html.H6(
                children='QAQC Dashboard',
		        style={
			        'textAlign': 'center',
			        'color': colors['header']
		        }),
            html.H6(
		        children='Nantucket Islands and Martha\'s Vinyard', 
		        style={
		            'textAlign': 'center',
		            'color': colors['header']
                }),
        ], className='four columns'),

        html.Div(style={}, children=[

            html.Div(
		        style={
		            'textAlign': 'Left',
		            'color': colors['header']
                },
                children=[
                    html.P(style={'margin': 0}, children=r'{:20s}: {:30s}'.format('Project ID', 'MA1601_TB_C')),
                    html.P(style={'margin': 0}, children=r'{:20s}: {:30s}'.format('Contractor',  'Dewberry')),
                    html.P(style={'margin': 0}, children=r'{:20s}: {:30s}'.format('UTM Zone',  '16'))
            ]),
        ], className='eight columns'),
    ], className='row'),

    html.Div([


        html.Div(style={}, children=[

            html.H6(style={'color': colors['text'], 'margin':0}, children='Las Tests'),    
            dcc.Graph(
                style={'height': '25vh', 'padding': 0},
		        id='pre-check-results',
		        figure={
			        'data': [
				        {
                            'x': [340] * 8,
                            'y': range(1,9), 
	                        'type': 'bar', 'name': 'PASSED', 'orientation': 'h'
                        },
				        {
                            'x': [11] * 8, 
                            'y': range(1,9),
                            'type': 'bar', 'name': 'FAILED', 'orientation': 'h'
                        },
			        ],
					'layout': {
                        'margin': {'l': 150, 'r': 5, 't':0},
						'xaxis': {
							'title': 'Number of LAS Files'
							},
						'yaxis': {
							'title': None,
							'titlefont':{
								'family': 'Courier New, monospace',
								'size': 20,
								'color': colors['text']},
                            'tickvals': range(1, len(checks_to_do.keys())+1),
                            'ticktext': checks_to_do.keys()
						},
						'legend': {'orientation': 'h',
									'x': 0,
									'y': 1.25},
						'barmode': 'stack',
						'plot_bgcolor': colors['background'],
						'paper_bgcolor': colors['background'],
						'font': {
							'color': colors['text']
						},
					}
				}
			),

            html.H6(style={'color': colors['text'], 'margin':0}, children='Class Counts'),
            dcc.Graph(
                style={'height': '20vh'},
				id='class-code-hist',
				figure={
					'data': [
						{
                            'values': [2,5,12,43,54,7789,3434,34,343,1],
                            'labels': ['{}:{}'.format(c, v) for c, v in 
                                        zip([01,02,03,04,25,26,27,44,56,66], 
                                            [2,5,12,43,54,7789,3434,34,343,1])],
                            'textinfo': 'none',
                            'hoverinfo': 'label+percent+value',
                            'type': 'pie', 
                            'name': 'SF'},
					],
					'layout': {
						'title': None,
                        'margin': {'l': 150, 'r': 25, 't': 0, 'b':25},
                        'plot_bgcolor': colors['background'],
						'paper_bgcolor': colors['background'],
						'font': {
							'color': colors['text']
						},
                        'legend': {
							'x': -25.0,
							'y': 1.15},
					}
				}
			),

            html.H6(style={'color': colors['text'], 'margin':0}, children='Bathymetry Histogram'),
			dcc.Graph(
                style={'height': '25vh'},
				id='depth-hist',
				figure={
					'data': [
						{'x': make_bathy_hist_data()[1], 
                        'y': make_bathy_hist_data()[0], 'type': 'bar', 'name': 'SF'},
					],
					'layout': {
						'title': None,
                        'margin': {'l': 150, 'r': 25, 't': 5, 'b':50},
                        'plot_bgcolor': colors['background'],
						'paper_bgcolor': colors['background'],
						'font': {
							'color': colors['text']
						},
                        'xaxis': {
							'title': 'Depth (m)',
							'titlefont':{
								'family': 'Calibri',
								'size': 20,
								'color': colors['text']},
						},
                        'yaxis': {
							'title': 'Frquency',
							'titlefont':{
								'family': 'Calibri',
								'size': 20,
								'color': colors['text']},
						},
					}
				}
			)

		], className='four columns'),

		html.Div(style={}, children=[

			html.Div([
				dcc.Dropdown(
                    style=map_button_style,
					id='MapLayers',                             
                    options=[
                        {'label': 'New York City', 'value': 'NYC'},
                        {'label': 'Montréal', 'value': 'MTL'},
                        {'label': 'San Francisco', 'value': 'SF'}
                    ],
                    placeholder='Select a Layer',
                    value='MTL',
                    className='two columns'
                ),

                    dcc.Dropdown(
                    style=map_button_style,
                    options=[
                        {'label': 'streets', 'value': 'streets'},
                        {'label': 'satellite', 'value': 'satellite'},
                    ],
                    placeholder='Select a Layer',
                    value='MTL',
                    className='two columns'
                ),
            ], className='row'),

            dcc.Graph(
                id='bigfoot-map',
                style={'height': '65vh'}
            ),

            html.Div([
                html.Div([
                    generate_table(df)
                ], className='twelve columns'),
            ]),

        ], className='eight columns'),

    ], className='row')

], className='no gutters')

@app.callback(
    dash.dependencies.Output('bigfoot-map', 'figure'),
    [dash.dependencies.Input('MapLayers', 'value')])
def update_map_layer(selector):

    if 'MTL' in selector:
        figure=bigfoot_map(tile_centroids)

    return figure


if __name__ == '__main__':
	app.run_server(debug=True)
