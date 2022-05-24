# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
import plotly.express as px
import plotly.graph_objects as go 
from dash.dependencies import Input, Output, State
import os
from zipfile import ZipFile
import urllib.parse
from flask import Flask, send_from_directory, request

import pandas as pd
import requests
import uuid
import werkzeug

import numpy as np
from tqdm import tqdm
import urllib
import json

from collections import defaultdict
import uuid

from flask_caching import Cache
import tasks

from app import app



dash_app = dash.Dash(
    name="dashinterface",
    server=app,
    url_base_pathname="/microbemasst/",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

dash_app.title = 'MASST+'

cache = Cache(dash_app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'temp/flask-cache',
    'CACHE_DEFAULT_TIMEOUT': 0,
    'CACHE_THRESHOLD': 1000000
})

NAVBAR = dbc.Navbar(
    children=[
        dbc.NavbarBrand(
            html.Img(src="https://gnps-cytoscape.ucsd.edu/static/img/GNPS_logo.png", width="120px"),
            href="https://gnps.ucsd.edu"
        ),
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink("MicrobeMASST Dashboard - Version 0.1", href="/microbemasst")),
            ],
        navbar=True)
    ],
    color="light",
    dark=False,
    sticky="top",
)

DATASELECTION_CARD = [
    dbc.CardHeader(html.H5("Data Selection")),
    dbc.CardBody(
        [   
            html.H5(children='GNPS Data Selection'),
            dbc.InputGroup(
                [
                    dbc.InputGroupText("Spectrum USI"),
                    dbc.Input(id='usi1', placeholder="Enter GNPS USI", value=""),
                ],
                className="mb-3",
            ),
        ]
    )
]

LEFT_DASHBOARD = [
    html.Div(
        [
            html.Div(DATASELECTION_CARD),
        ]
    )
]

MIDDLE_DASHBOARD = [
    dbc.CardHeader(html.H5("Data Exploration")),
    dbc.CardBody(
        [
            dcc.Loading(
                id="output",
                children=[html.Div([html.Div(id="loading-output-23")])],
                type="default",
            ),
            html.Br(),
            html.Hr(),
            html.Br(),
            dcc.Loading(
                id="spectrummirror",
                children=[html.Div([html.Div(id="loading-output-24")])],
                type="default",
            ),

        ]
    )
]

CONTRIBUTORS_DASHBOARD = [
    dbc.CardHeader(html.H5("Contributors")),
    dbc.CardBody(
        [
            "Mingxun Wang PhD - UC San Diego",
            html.Br(),
            "Robin Schmid PhD - UC San Diego",
            html.Br(),
            # html.H5("Citation"),
            # html.A('Mingxun Wang, Jeremy J. Carver, Vanessa V. Phelan, Laura M. Sanchez, Neha Garg, Yao Peng, Don Duy Nguyen et al. "Sharing and community curation of mass spectrometry data with Global Natural Products Social Molecular Networking." Nature biotechnology 34, no. 8 (2016): 828. PMID: 27504778', 
            #         href="https://www.nature.com/articles/nbt.3597")
        ]
    )
]

EXAMPLES_DASHBOARD = [
    dbc.CardHeader(html.H5("Examples")),
    dbc.CardBody(
        [
            html.A('Stenothricin', 
                    href="/microbemasst?usi1=mzspec:GNPS:GNPS-LIBRARY:accession:CCMSLIB00005436027"),
            
        ]
    )
]

BODY = dbc.Container(
    [
        dcc.Location(id='url', refresh=False),
        dbc.Row([
            dbc.Col(
                dbc.Card(LEFT_DASHBOARD),
                className="col-6"
            ),
            dbc.Col(
                [
                    dbc.Card(CONTRIBUTORS_DASHBOARD),
                    # html.Br(),
                    # dbc.Card(EXAMPLES_DASHBOARD)
                ],
                className="col-6"
            ),
        ], style={"marginTop": 30}),
        html.Br(),
        dbc.Row([
            dbc.Card(MIDDLE_DASHBOARD)
        ])
    ],
    fluid=True,
    className="",
)

dash_app.layout = html.Div(children=[NAVBAR, BODY])

def _get_url_param(param_dict, key, default):
    return param_dict.get(key, [default])[0]

@dash_app.callback([
                Output('usi1', 'value'), 
              ],
              [
                  Input('url', 'search')
              ])
def determine_task(search):
    
    try:
        query_dict = urllib.parse.parse_qs(search[1:])
    except:
        query_dict = {}

    usi1 = _get_url_param(query_dict, "usi1", 'mzspec:GNPS:GNPS-LIBRARY:accession:CCMSLIB00000085687')

    return [usi1]




@dash_app.callback([
                Output('output', 'children')
              ],
              [
                  Input('usi1', 'value'),
            ])
def draw_output(usi1):
    # For MicrobeMASST code from robin
    # import sys
    # sys.path.insert(0, "microbe_masst/code/")
    # import microbe_masst

    # # Doing MicrobeMASST here
    # microbe_masst.run_microbe_masst(usi1, 0.05, 0.02, 0.7,
    #         # tree generation
    #         in_html="./microbe_masst/code/collapsible_tree_v3.html", 
    #         in_ontology="./microbe_masst/data/ncbi.json", 
    #         metadata_file="./microbe_masst/data/microbe_masst_table.csv",
    #         out_counts_file="./temp/microbemasst/counts.tsv",
    #         out_json_tree="./temp/microbemasst/tree.json", format_out_json=True, 
    #         out_html="./temp/microbemasst/oneindex.html", compress_out_html=True,
    #         node_key="NCBI", data_key="ncbi")

    import uuid
    mangling = str(uuid.uuid4())
    output_temp = os.path.join("temp", "microbemasst", mangling)
    os.makedirs(output_temp, exist_ok=True)

    output_html = "../../{}/oneindex.html".format(output_temp)
    output_tree = "../../{}/tree.json".format(output_temp)
    output_counts = "../../{}/counts.tsv".format(output_temp)

    cmd = 'cd microbe_masst/code/ && python microbe_masst.py \
    --usi_or_lib_id "{}" \
    --out_html "{}" \
    --out_tree "{}" \
    --out_counts_file "{}"'.format(usi1, output_html, output_tree, output_counts)
    import sys
    print(cmd, file=sys.stderr, flush=True)
    os.system(cmd)
    
    return [html.Iframe(src="/microbemasst/results?task={}".format(mangling), width="100%", height="900px")]

@dash_app.callback([
                Output('spectrummirror', 'children')
              ],
              [
                  Input('usi1', 'value'),
                  Input('table', 'derived_virtual_data'),
                  Input('table', 'derived_virtual_selected_rows'),
              ]
)
def draw_spectrum(usi1, table_data, table_selected):
    try:
        selected_row = table_data[table_selected[0]]
    except:
        return ["Choose Match to Show Mirror Plot"]

    dataset_accession = selected_row["Accession"]
    dataset_scan = selected_row["DB Scan"]

    database_usi = "mzspec:MSV000084314:{}:scan:{}".format("updates/2020-11-18_mwang87_d115210a/other/MGF/{}.mgf".format(dataset_accession), dataset_scan)

    url_params_dict = {}
    url_params_dict["usi1"] = usi1
    url_params_dict["usi2"] = database_usi

    url_params = urllib.parse.urlencode(url_params_dict)

    link_url = "https://metabolomics-usi.ucsd.edu/dashinterface"
    link = html.A("View Spectrum Mirror Plot in Metabolomics Resolver", href=link_url + "?" + url_params, target="_blank")
    svg_url = "https://metabolomics-usi.ucsd.edu/svg/mirror/?{}".format(url_params)

    image_obj = html.Img(src=svg_url)

    return [[link, html.Br(), image_obj]]

# API
@app.route("/microbemasst/results")
def results():
    task = request.args.get("task")
    output_folder = os.path.join("temp", "microbemasst", os.path.basename(task))

    return send_from_directory(output_folder, "oneindex.html")

if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")