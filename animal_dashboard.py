
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_leaflet as dl
import plotly.express as px
import base64
import pandas as pd
from AnimalShelter import AnimalShelter
import dash_bootstrap_components as dbc 

# Instantiate Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Connect to MongoDB using AnimalShelter CRUD class
db = AnimalShelter()
df = pd.DataFrame.from_records(db.read({}))
df.drop(columns=['_id'], inplace=True)

# Load logo image from assets folder
try:
    image_filename = 'assets/grazioso_logo.png'
    encoded_image = base64.b64encode(open(image_filename, 'rb').read()).decode()
except FileNotFoundError:
    encoded_image = None
    print("Logo image not found. Please ensure 'grazioso_logo.png' is in the 'assets' folder.") 
    

# Define app layout
app.layout = html.Div([
    html.Img(src='data:image/png;base64,{}'.format(encoded_image), style={'height': '100px'}) if encoded_image else html.div(),
    html.A("Visit SNHU", href="https://www.snhu.edu", target="_blank"),
    html.H5("Umar Asif - SNHU ID: 3139069", style={'textAlign': 'center'}),
    html.Center(html.B(html.H1('CS-340 Animal Shelter Dashboard'))),
    html.Hr(),
# Filter options for rescue types
html.Div([
    dcc.RadioItems(
        id='filter-type',
        options=[
            {'label': 'Water Rescue', 'value': 'water'},
            {'label': 'Mountain or Wilderness Rescue', 'value': 'mountain'},
            {'label': 'Disaster or Individual Tracking', 'value': 'disaster'},
            {'label': 'Reset', 'value': 'reset'}
        ],
        value='reset',
        labelStyle={'display': 'inline-block', 'margin-right': '15px'}
    ),
    dcc.Dropdown(
        id='breed-filter',
        options=[{'label': b, 'value': b} for b in df['breed'].unique()],
        multi=True,
        placeholder="Filter by breeds...",
        style={'margin-top': '10px'}
    )
]),

html.Hr(),
#Data table to display animal records
    dash_table.DataTable(
        id='datatable-id',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        page_size=10,
        style_table={'overflowX': 'auto'},
        row_selectable='single',
        selected_rows=[0],
        sort_action='native',
        filter_action='native',
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
    ),

    html.Br(),
    html.Hr(),
#visualization components
    html.Div(className='row', style={'display': 'flex'}, children=[
        html.Div(id='graph-id', className='col s12 m6'),
        html.Div(id='map-id', className='col s12 m6')
    ]),
#Notification component    
    dcc.Store(id='notification-store'),
    html.Div(id='notification', style={'position': 'fixed', 'top': '10px', 'right': '10px'})

])
# Initialize callbacks
@app.callback(
    [Output('datatable-id', 'data'),
     Output('notification', 'children')],
    [Input('filter-type', 'value'),
     Input('breed-filter', 'value')]
)
def update_data(filter_type, selected_breeds):
    query = {}
    
    # Base filters
    if filter_type == 'water':
        query = {
            "breed": {"$in": ["Labrador Retriever Mix", "Chesapeake Bay Retriever", "Newfoundland"]},
            "sex_upon_outcome": "Intact Female",
            "age_upon_outcome_in_weeks": {"$gte": 26, "$lte": 156}
        }
    elif filter_type == 'mountain':
        query = {
            "breed": {"$in": ["German Shepherd", "Alaskan Malamute", "Old English Sheepdog", "Siberian Husky", "Rottweiler"]},
            "sex_upon_outcome": "Intact Male",
            "age_upon_outcome_in_weeks": {"$gte": 26, "$lte": 156}
        }
    elif filter_type == 'disaster':
        query = {
            "breed": {"$in": ["Doberman Pinscher", "German Shepherd", "Golden Retriever", "Bloodhound", "Rottweiler"]},
            "sex_upon_outcome": "Intact Male",
            "age_upon_outcome_in_weeks": {"$gte": 20, "$lte": 300}
        }
    
    # Additional breed filter
    if selected_breeds:
        if 'breed' in query:
            query['breed']['$in'] = list(set(query['breed']['$in']) & set(selected_breeds))
        else:
            query['breed'] = {'$in': selected_breeds}
    
    try:
        results = pd.DataFrame.from_records(db.read(query))
        results.drop(columns=['_id'], inplace=True)
        
        if results.empty:
            return results.to_dict('records'), dbc.Alert("No results found!", color="warning", dismissable=True)
        return results.to_dict('records'), ""
        
    except Exception as e:
        return [], dbc.Alert(f"Error: {str(e)}", color="danger", dismissable=True)


# Update graphs 
@app.callback(
    Output('graph-id', "children"),
    Input('datatable-id', "derived_virtual_data")
)
def update_graphs(viewData):
    if viewData is None or len(viewData) == 0:
        return html.Div("No data to display", style={'textAlign': 'center'})
    
    dff = pd.DataFrame(viewData)
    if 'breed' not in dff.columns:
        return html.Div("No breed data available", style={'textAlign': 'center'})
    
    fig = px.pie(dff, names='breed', title='Rescue Dog Breed Distribution')
    return [dcc.Graph(figure=fig)]

# Update styles 
@app.callback(
    Output('datatable-id', 'style_data_conditional'),
    Input('datatable-id', 'selected_columns')
)
def update_styles(selected_columns):
    return [{
        'if': {'column_id': i},
        'background_color': '#D2F3FF'
    } for i in selected_columns] if selected_columns else []

# Update map 
@app.callback(
    Output('map-id', "children"),
    [Input('datatable-id', "derived_virtual_data"),
     Input('datatable-id', "derived_virtual_selected_rows")]
)
def update_map(viewData, index):
    if not viewData or not index:
        return dl.Map(center=[30.75, -97.48], zoom=10, style={'width': '1000px', 'height': '500px'})
    
    dff = pd.DataFrame(viewData)
    row = index[0]

    # Safe field access
    lat = dff.iloc[row].get('location_lat', 30.75)
    lon = dff.iloc[row].get('location_long', -97.48)
    name = dff.iloc[row].get('name', 'Unknown')
    animal_type = dff.iloc[row].get('animal_type', 'Unknown')
    
    return [
        dl.Map(
            center=[lat, lon],
            zoom=10,
            style={'width': '1000px', 'height': '500px'},
            children=[
                dl.TileLayer(),
                dl.Marker(
                    position=[lat, lon], 
                    children=[
                    dl.Tooltip(dff.iloc[row, 4]),
                    dl.Popup([
                        html.H4("Animal Details"),
                        html.P(f"Name: {name}"),
                        html.P(f"Type: {animal_type}"),
                        html.P(f"Breed: {dff.iloc[row].get('breed', 'Unknown')}")
                ])
            ])
        ])
    ]

if __name__ == '__main__':
    app.run(debug=True)
