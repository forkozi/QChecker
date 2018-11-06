# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import geopandas as gpd
import numpy as np
import json
from io import open
from pyproj import Proj, transform
import fiona
from fiona.crs import from_epsg
from toolz import groupby, compose, pluck
from dotenv import load_dotenv
import os
from csv import DictReader


#dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
#load_dotenv(dotenv_path)


def generate_table(dataframe, max_rows=10):
    return html.Table(style={
        'overflow': 'auto',
        }, children=
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
                    'border-bottom':'blue',
                    'white-space': 'nowrap',                    
                    })  # TODO: not what I wanted, but I like it! (fix)
            for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


def make_bathy_hist_data():
	mu, sigma = 0, 0.1 # mean and standard deviation
	s = np.random.normal(mu, sigma, 1000)
	hist, bin_edges = np.histogram(s, bins=100)
	return (hist, bin_edges)



map_colors = {
    'tiles': {
        'Outside AOI and no Bathy': 'rgb(67, 67, 67)',
        'Project Area/Found Bathy': 'rgb(0, 119, 224)',
        'automated ground run only/no review': 'rgb(32, 140, 37)',
        },
    'check_result': {
        'TRUE': 'rgb(101,255,0)',
        'FALSE': 'rgb(255,0,0)',
        },
    }


def get_qaqc_map(check_name, check_label, map_style, contract_tile_csv, qaqc_results_csv):
	# groupby returns a dictionary mapping the values of the first field 
	# 'classification' onto a list of record dictionaries with that 
	# classification value.
	listpluck = compose(list, pluck)

	selected_contract_field = 'Notes'
	contract_tiles = groupby(selected_contract_field, contract_tile_csv)

	selected_qaqc_field = check_label
	qaqc_results = groupby(selected_qaqc_field, qaqc_results_csv)

	contract_tiles = [
				{
					"type": "scattermapbox",
					"lat": listpluck("centroid_y", tile),
					"lon": listpluck("centroid_x", tile),
					"mode": "markers",
					"name": field,
					"marker": {
						"size": 4,
						"opacity": 1,
                        "color": map_colors['tiles'][field],
					},
                    "text": listpluck("Las_Name", tile),
					'hoverinfo': "name+text",
				}
				for field, tile in contract_tiles.items()
			]

	qaqc_tiles = [
				{
					"type": "scattermapbox",
					"lat": listpluck("centroid_y", tile),
					"lon": listpluck("centroid_x", tile),
					"mode": "markers",
					"name": '{} ({})'.format(field, check_name),
					"marker": {
						"size": 8,
						"opacity": 0.7,
                        "color": map_colors['check_result'][field],
					},
					'hoverinfo': "name",
				}
				for field, tile in qaqc_results.items()
				]

	return {
		"data":  qaqc_tiles + contract_tiles,
		"layout": {
			'legend': dict(
					x=0,
					y=0,
					traceorder='normal',
					font=dict(
						family='sans-serif',
						size=12,
						color=colors['text']
					),
					bgcolor='rgba(26,26,26,1)',
				),
			'margin': {'l': 0, 'r': 0, 't': 0, 'b':0},
			'showlegend': True,
			"autosize": True,
			"hovermode": "closest",
			"mapbox": {
				'layers': [{
					'sourcetype': 'geojson',
					'source': get_tile_geojson_file(),
					'type': 'line',
					'color': '#0946BF',
					'line': {'width':0.5},
                    'opacity': 2
                }],
                "accesstoken": MAPBOX_KEY,
                "bearing": 0,
                "center": {
                    "lat": 41.35,
                    "lon": -70.2
                },
                "pitch": 0,
                "zoom": 10,
                "style": map_style,
            }
        }
    }


def get_tile_geojson_file():
	qaqc_dir = r'C:\QAQC_contract\nantucket'
	las_tiles_geojson = os.path.join(qaqc_dir, 'tiles.json')
	with open(las_tiles_geojson, encoding='utf-8') as f:
		geojson_data = json.load(f)

	return geojson_data


def get_contract_tile_csv():
    fin = open(r'C:\QAQC_contract\nantucket\tiles_centroids.csv', 'r')
    reader = DictReader(fin)
    tile_centroids = [line for line in reader]
    fin.close()

    return tile_centroids

def get_tiles_df():
    df = pd.read_csv(r'C:\QAQC_contract\nantucket\tiles_centroids.csv')
    return df

def get_qaqc_results_csv():
    fin = open(r'C:\QAQC_contract\nantucket\qaqc_tile_collection_results.csv', 'r')
    reader = DictReader(fin)
    qaqc_results = [line for line in reader]
    fin.close()

    return qaqc_results




MAPBOX_KEY = "pk.eyJ1Ijoibmlja2ZvcmZpbnNraSIsImEiOiJjam51cTNxY2wwMTJ2M2xrZ21wbXZrN2F1In0.RooxCuqsNotDzEP2EeuJng"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


colors = {
	'background': '#373D42',
	'text': '#B1C4D2',
    'header': '#0968AA',
    'button_background': '#75777a',
}

map_button_style = {
    'color': colors['text'],
    'border-color': colors['text'],
    'background-color': colors['button_background'],
    'border-radius': '50px',
    'padding': '0px',
    'line-height': '1px',
}

map_control_label_style = {
    'color': colors['text'],
    'margin-top': '1em',
    }

checks_to_do = {
	'naming_convention': False,
	'version': False,
	'pdrf': False,
	'gps_time': False,
	'hor_datum': False,
	'ver_datum': False,
	'point_source_ids': False,
    'create_dz': True,
    'create_hillshade': False,
}

check_labels = {
    'naming_convention': 'Naming Convention',
	'version': 'Version',
	'pdrf': 'Record Type (PDRF)',
	'gps_time': 'GPS Time Type',
	'hor_datum': 'Horizontal Datum',
	'ver_datum': 'Vertical Datum',
	'point_source_ids': 'Point Source IDs',
    'create_dz': 'Dz Ortho Created',
    'create_hillshade': 'Hillshade Ortho Created',
    }

check_result_names = {
    'naming_convention': 'naming_convention_passed',
	'version': 'version_passed',
	'pdrf': 'pdrf_passed',
	'gps_time': 'gps_time_passed',
	'hor_datum': 'hor_datum_passed',
	'ver_datum': '',
	'point_source_ids': '',
    'create_dz': '',
    'create_hillshade': '',
    }

tabs_styles = {
    'height': '44px',
}

tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold',
    'color': '#373D42',
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}


def get_check_layer_options():
    options = []
    for check in checks_to_do.keys():
        options.append({'label': check_labels[check], 'value': check})

    return options


def get_qaqc_settings_tab():
    return html.Div(
		        style={
		            'textAlign': 'Left',
		            'color': colors['header']
                },
                children=[
                    html.P(style={'margin': 0}, children=r'{:20s}: {:30s}'.format('Project ID', 'MA1601_TB_C')),
                    html.P(style={'margin': 0}, children=r'{:20s}: {:30s}'.format('Contractor',  'Dewberry')),
                    html.P(style={'margin': 0}, children=r'{:20s}: {:30s}'.format('UTM Zone',  '16'))
            ]),


def get_tile_overview_tab():
    return html.Div(style={}, children=[
                html.Div(style={}, children=[

                    html.H6(
                        style={'color': colors['text'], 'margin':0}, 
                        children='Las Tests'),    
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

                    html.H6(
                        style={'color': colors['text'], 'margin':0}, 
                        children='Class Counts'),
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

                    html.H6(
                        style={'color': colors['text'], 'margin':0}, 
                        children='Bathymetry Histogram'),
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

		        ], className='three columns'),

                html.Div([
                    dcc.Graph(
					    id='qaqc_map',
					    style={'height': '90vh'}
				    ),  
                ], className='seven columns'),

                html.Div(style={'margin-left': '1em'}, children=[

					    html.P(
						    style=map_control_label_style, 
						    children='Test Result:'),

                        dcc.Dropdown(
                            style=map_button_style,
					        id='CheckResultLayers',                             
                            options=get_check_layer_options(),
                            placeholder='Select a Layer',
                            value='version'),

                        html.P(
                            style=map_control_label_style, 
                            children='Map Style:'),

                        dcc.Dropdown(
                            style=map_button_style,
                            id='MapStyleSelector', 
                            options=[
                                {'label': 'streets', 'value': 'streets'},
                                {'label': 'dark', 'value': 'dark'},
                                {'label': 'satellite', 'value': 'satellite'},
                            ],
                            placeholder='Select a Layer',
                            value='dark'),

                        html.P(
                            style=map_control_label_style, 
                            children='Choose Layers to Display:'),

                        dcc.Checklist(style={
                            'color': colors['text'],
                            },
                            options=[
                                {'label': 'Contractor tiles', 'value': 'tiles'},
                                {'label': 'Las Data Extents', 'value': 'las_extents'},
                                {'label': 'Trajectory', 'value': 'trajectory'}
                            ],
                            values=['trajectory']
                        )

                ], className='two columns'),

        ], className='row')


def get_tile_point_cloud_tab():
    return html.Div([
                    generate_table(get_tiles_df())
                ], className='row'),


def get_qaqc_result_table_tab():
    return html.Div([
                    generate_table(get_tiles_df())
                ], className='row'),


def get_qaqc_log_tab():
    return html.Div([
                    generate_table(get_tiles_df())
                ], className='row'),


app.config['suppress_callback_exceptions']=True
app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.Div(style={'backgroundColor':'#00ADEF'}, children=[
        html.Div(style={}, children=[
            html.P(
		        children='QAQC: Nantucket Islands and Martha\'s Vinyard', 
		        style={
                    'textAlign': 'center',
		            'color': colors['header'],
                    'font-size': 16,
                    'font-weight': 'bold',
                    'vertical-align': 'middle',
                    'line-height': '5vh',
                    'margin': 0,
                    'padding': 0
                }),
        ], className='three columns'),

        html.Div(style={'margin-left': 0}, children=[

            dcc.Tabs(
                id="tabs-header", 
                value='tab-1', 
                style=tabs_styles,
                children=[
                    
                    dcc.Tab(
                        style=tab_style, 
                        selected_style=tab_selected_style,
                        label='QAQC Settings',
                        value='qaqc_settings-tab'),

                    dcc.Tab(
                        style=tab_style, 
                        selected_style=tab_selected_style,
                        label='Tile Overview',
                        value='tile-overview-tab'),
                    
                    dcc.Tab(
                        style=tab_style, 
                        selected_style=tab_selected_style,
                        label='Tile Point Cloud',
                        value='tile-point-cloud-tab'),

                    dcc.Tab(
                        style=tab_style, 
                        selected_style=tab_selected_style,
                        label='QAQC Results Table',
                        value='qaqd-results-table-tab'),

                    dcc.Tab(
                        style=tab_style, 
                        selected_style=tab_selected_style,
                        label='QAQC Log',
                        value='qaqc-log-tab'),

                ], className='twelve columns'),

        ], className='nine columns'),

    ], className='row'),

    html.Div(id='tabs-content')

], className='no gutters')


@app.callback(dash.dependencies.Output('tabs-content', 'children'),
              [dash.dependencies.Input('tabs-header', 'value')])
def render_content(tab):
    if tab == 'qaqc_settings-tab':
        return get_qaqc_settings_tab()
    elif tab == 'tile-overview-tab':
        return get_tile_overview_tab()
    elif tab == 'tile-point-cloud-tab':
        return get_tile_point_cloud_tab()
    elif tab == 'qaqd-results-table-tab':
        return get_qaqc_result_table_tab()
    elif tab == 'qaqc-log-tab':
        return get_qaqc_log_tab()


@app.callback(
    dash.dependencies.Output('qaqc_map', 'figure'),
    [dash.dependencies.Input('CheckResultLayers', 'value'),
     dash.dependencies.Input('MapStyleSelector', 'value')])
def update_map_layer(input1, input2):
	print(input1)
	print(input2)
	
	figure=get_qaqc_map(check_labels[input1], 
						check_result_names[input1],
						input2,
						get_contract_tile_csv(),
						get_qaqc_results_csv())

	return figure


if __name__ == '__main__':
	
	app.run_server(debug=True)

