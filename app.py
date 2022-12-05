import dash
from dash import Dash, html, dcc, Input, Output, State, ctx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from copy import deepcopy
import os
import dash_bootstrap_components as dbc
from dash_bootstrap_components._components.Container import Container

# global variables
DATAFILE = "below.csv"
LATEST_UNIXTIME = 1668617520
ONE_YEAR = 31556952  # in sec
POINT_SIZE = 9

# pre-cleaning
# accessibility sw width df
# read data from excel
df_sw_widths = pd.read_excel('sidewalk_comparison.xlsx')
# make id col
df_sw_widths['id'] = df_sw_widths.index
df_sw_widths['Est. Error (ft)'] = df_sw_widths['Measured Width (ft)'] - \
    df_sw_widths['Sidewalk Inventory Width (ft)']


# set 311 df
df_311 = pd.read_csv(DATAFILE)
df_311['open_dt'] = pd.to_datetime(df_311['open_dt'])
df_311['closed_dt'] = pd.to_datetime(df_311['closed_dt'])

start_time = df_311["open_dt"].min()
df_311["time_since_start"] = [i.total_seconds()
                              for i in df_311["open_dt"] - start_time]

# bootstrap theme
# https://bootswatch.com/morph/
external_stylesheets = [dbc.themes.MORPH]

# Start app
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=external_stylesheets)

server = app.server

"""
Accessibility page callback code and supporting utility functions
"""


@app.callback(
    Output("sw_map", "figure"),
    Output('selected_thresh', 'children'),
    Input("sw_width_slider_input", "value"))
def display_map(sw_width):

    # read data from excel
    df = pd.read_excel("sidewalk_comparison.xlsx")

    # rename column to Inventory
    df = df.rename(
        columns={'Sidewalk Invetory Width (ft)': 'Sidewalk Inventory Width (ft)'})

    # make accessibility column
    df['Accessibility'] = 'Inaccessible'
    df.loc[df['Measured Width (ft)'] >=
           sw_width, 'Accessibility'] = 'Accessible'

    # get the difference
    df['Diff'] = df['Measured Width (ft)'] - \
        df['Sidewalk Inventory Width (ft)']
    df['id'] = df.index
    df["point_size"] = pd.Series([POINT_SIZE for i in range(len(df))])
    px.set_mapbox_access_token(
        'pk.eyJ1IjoicnVkbWFuayIsImEiOiJjbGFuMWI4Nngwa3A4NDFvMjRhZDB5ZTNiIn0.l5q-aaRLdzvqUBB11hkZqg')
    fig = px.scatter_mapbox(df, lat="Lat", lon="Lon", color="Accessibility",
                            hover_data={
                                "Sidewalk Segment": True,
                                "Accessibility": True,
                                'Measured Width (ft)': True,
                                "Sidewalk Inventory Width (ft)": True,
                                "Lat": False, "Lon": False, "point_size": False},
                            custom_data=["id"],
                            size="point_size",
                            color_discrete_map={
                                "Accessible": "orange", "Inaccessible": "blue"},
                            title='Mass Ave Map of Accessibility Assessment', zoom=14.5)
    # change default config
    fig.update_layout(
        uirevision="foo",
        mapbox=dict(
            accesstoken='pk.eyJ1IjoicnVkbWFuayIsImEiOiJjbGFuMWI4Nngwa3A4NDFvMjRhZDB5ZTNiIn0.l5q-aaRLdzvqUBB11hkZqg',
            bearing=45,
            center={'lon': -71.08016740807517, 'lat': 42.339358059717284},
            pitch=45,
            zoom=16
        ))

    return fig, f'Your criteria: Sidewalk must be at least {sw_width} feet wide.'

# callback for brushing and linking to measurement bar


@app.callback(
    Output('measurement_error_bar', 'figure'),

    Input('sw_map', 'selectedData'))
def display_selected_data(selectedData):
    # If there is no data selected, don't display anything
    if selectedData is None:
        fig = go.Figure()
        fig.add_annotation(text="Select map using box select tool to show compare measured vs. recorded sidewalk widths",
                           xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False)
        return fig

    sw_ids = [i["customdata"][0] for i in selectedData["points"]]
    # we only want to plot the ones that were selected
    df = df_sw_widths[df_sw_widths["id"].isin(sw_ids)]

    # create the figure
    fig = px.bar(df, x=['Measured Width (ft)', 'Sidewalk Inventory Width (ft)'],
                 y='Sidewalk Segment', hover_data=['Sidewalk Segment'], barmode="group", title='Sidewalk Measurement Error',
                 orientation='h')
    fig.update_layout(xaxis_title="Width (ft)")

    return fig


"""
311 request callback code and supporting utility functions
"""


def unixTimeMillis(dt):
    ''' Convert datetime to unix timestamp '''
    return int(time.mktime(pd.to_datetime(dt).timetuple()))


def unixToDatetime(unix):
    ''' Convert unix timestamp to datetime. '''
    return pd.to_datetime(unix, unit='s')


def getMarks(start, end, Nth=100):
    ''' Returns the marks for labeling.
        Every Nth value will be used.
    '''
    daterange = pd.date_range(start, end, 8)
    marks_df = pd.DataFrame(daterange)
    result = {}
    for date in marks_df[0]:
        result[unixTimeMillis(date)] = str(date.strftime('%Y-%m-%d'))
    return result


def display_selected_data(selectedData):
    # If there is no data selected, don't display anything
    if selectedData is None or len(selectedData["points"]) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Select map using lasso tool to show summary statistics",
                           xref="paper", yref="paper",
                           x=0.5, y=0.4, showarrow=False)
        fig.add_annotation(text="OR",
                           xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False)
        fig.add_annotation(text="Click a point on the map to show more details",
                           xref="paper", yref="paper",
                           x=0.5, y=0.58, showarrow=False)
        return fig

    case_ids = [i["customdata"][0] for i in selectedData["points"]]

    dff = df_311[df_311["case_enquiry_id"].isin(case_ids)]

    fig = px.histogram(dff, x="open_dt", color="case_status",
                       color_discrete_map={"Open": "blue", "Closed": "red"},
                       title="Selected 311 Requests by Open Date")
    fig.update_layout(
        xaxis_title="Open date",
        yaxis_title="Number of requests")

    fig.update_layout(bargap=0.2)

    return fig

# callback for direct 311 map interactivity


@app.callback(
    Output('static_subplot', 'figure'),
    Output("graph-div", "style"),
    Output("req-details-div", "style"),
    Output("req-details-case-title", "children"),
    Output("req-details-submittedphoto", "src"),
    Output("req-details-open-date", "children"),
    Output("req-details-status", "children"),
    Output("req-details-closed-date", "children"),
    Output("req-details-closed-reason", "children"),
    Output("req-details-closed-photo", "src"),
    Input('311_map', 'selectedData'),
    Input("311_map", "clickData"))
def select_or_click(selectedData, clickData):
    if ctx.triggered_prop_ids == {} or "311_map.selectedData" == list(ctx.triggered_prop_ids.keys())[0]:
        fig = display_selected_data(selectedData)
        return fig, {"display": "block"}, {"display": "None"}, "", None, "", "", "", "", None
    else:
        # We're displaying clickdata; make this the default graph
        fig = display_selected_data(None)
        style_graph = {"display": "None"}
        style_req = {"display": "block"}
        req_id = clickData["points"][0]["customdata"][0]
        row = df_311.loc[df_311['case_enquiry_id'] == req_id]
        row = {i: row[i][list(row.index)[0]] for i in row.columns}
        # Start making subfunctions lol
        case_title = get_case_title(row)
        open_photo = get_open_photo(row)
        open_date = get_open_date(row)
        case_status = get_case_status(row)
        closed_date, closed_reason, closed_photo = get_closed_data(row)
        return fig, {"display": "None"}, {"display": "Block"}, case_title, open_photo, open_date, case_status, closed_date, closed_reason, closed_photo


def get_case_title(row):
    return "Reason: {}".format(row["case_title"])


def get_open_photo(row):
    entry = row["submittedphoto"]
    if isinstance(entry, float):
        return None
    return entry


def get_open_date(row):
    return "Request open date: {}".format(str(row["open_dt"].strftime('%Y-%m-%d')))


def get_case_status(row):
    return "Request status: {}".format(row["case_status"])


def get_closed_data(row):
    if row["case_status"] == "Open":
        return "", "", None
    closed = "Request closed date: {}".format(
        str(row["closed_dt"].strftime('%Y-%m-%d')))
    closed_reason = "Request closure reason: {}".format(row["closure_reason"])
    photo2 = row["closedphoto"]
    if not photo2:
        photo2 = None
    return closed, closed_reason, photo2

# callback for linking slider to 311 map


@app.callback(
    Output("311_map", "figure"),
    Output("Date-instructions", "children"),
    Input("date-slider", "value"),
    Input("show-all-button", "n_clicks_timestamp"),
    Input("filter-by-date-button", "n_clicks_timestamp")
)
def display_slided_map(value, sab_ts, fbdb_ts):
    if "show-all-button" == ctx.triggered_id:
        dff = df_311
        start_date_unix = unixToDatetime(1000)
        end_date_unix = unixToDatetime(1001)
    else:
        start_date_unix = unixToDatetime(value[0])
        end_date_unix = unixToDatetime(value[1])
        dff = df_311[(df_311['open_dt'] > start_date_unix)
                     & (df_311["open_dt"] < end_date_unix)]

    px.set_mapbox_access_token(
        'pk.eyJ1IjoicnVkbWFuayIsImEiOiJjbGFuMWI4Nngwa3A4NDFvMjRhZDB5ZTNiIn0.l5q-aaRLdzvqUBB11hkZqg')
    fig = px.scatter_mapbox(dff, lat="latitude", lon="longitude", color="case_status",
                            hover_data={
                                'case_title': True, "case_status": True, "latitude": False, "longitude": False},
                            custom_data=["case_enquiry_id"],
                            color_discrete_map={
                                "Open": "blue", "Closed": "red"},
                            title='311 Requests Pertaining to the Sidewalk', zoom=11)

    return fig, "Selected dates: From {} to {}".format(
        start_date_unix.strftime('%Y-%m-%d'), end_date_unix.strftime("%Y-%m-%d"))

# callback for BOTH SHOW-ALL BUTTON AND filter-by-date button


@app.callback(
    Output("div-sd-sa", "style"),
    Output("div-fbd", "style"),
    Output("Slider-div", "style"),
    Input("show-all-button", "n_clicks"),
    Input('filter-by-date-button', 'n_clicks')
)
def date_filter_div_button_clicked(show_all, filter_by_date):
    if "show-all-button" == ctx.triggered_id:
        return {"display": "None"}, {"display": "block"}, {"display": "None"}
    return {"display": "block"}, {"display": "None"}, {"display": "block"}


# MOTIVATION PAGE
children_motivation = [
    html.Br(),
    html.H1(children=dcc.Markdown('**Group 15: Compatible City**')),
    html.H2(children='Joshua Peirce, Rachel Utama, Kyle Rudman'),
    html.Br(),

    # image of accessible spot
    html.Img(src='assets/Tremont to Shawmut.jpg', alt='image', style={
        "width": "80%",
        "max-width": "240px",
        "height": "80%",
        "max-height": "300",
        "textAlign": "center"}),

    html.Div([
        # motivation
        html.H2(children='Motivation'),
        html.P(children="""Our project, “Compatible City”, aims to identify and address common issues that pedestrians face commuting along the sidewalks of Mass Ave. The Mass Ave neighborhood is home to many people and businesses, and improved accessibility can yield a large social benefit. We explore the question: Is Mass Ave accessible– both in terms of meeting the city’s regulations, and in reality? We also highlight segments of sidewalk that are in most need of improvement and celebrate the walking areas that are safe and accessible. In our project’s visualization, we allow the user to interact with a street-view map of Mass Ave to better understand the accessibility issues pedestrians face in everyday life.
                            The Mass Ave coalition is a Boston-based nonprofit organization seeking to advance the public health, transportation, and streetscape surrounding Mass Ave. They collaborate with a variety of stakeholders in the community to create actionable improvements regarding areas of need in the Mass Ave neighborhood. As students of Northeastern University, our contributions through our project can have a direct impact on the community we share.
                            """),
    ], style={'textAlign': 'center', 'marginBottom': 50, 'marginTop': 25, 'marginLeft': 200, 'marginRight': 200}),
]

# DATA PAGE
children_data = [
    html.Br(),
    html.H1(children=dcc.Markdown('**Group 15: Compatible City**')),
    html.H2(children='Joshua Peirce, Rachel Utama, Kyle Rudman'),
    html.Br(),
    html.Div([
        html.H2(children='Data'),
        html.P(children="""Our webpage features multiple visualizations that are interlinked between three unique datasets. Our first source of data comes from manually-collected data which features coordinate values of Mass Ave sidewalk segments (defined as the stretch of the sidewalk between intersecting streets) along with an average width measurement. We collected this data by walking Mass Ave with a tape measure and recording all characteristics into an organized Excel spreadsheet. The widths and coordinates are both quantitative, while the street names and accessibility evaluations (marked as accessible if greater than 8 ft) are categorical data.
                        Our second dataset comes from Analyze Boston’s sidewalk inventory dataset. Provided by the city of Boston, the sidewalk inventory features a geojson rendering of all of the mapped sidewalks in the Boston city limits. Each segment also features corresponding quantitative and categorical metadata, such as sidewalk widths, material, curb type, etc. We were curious to find out whether our measurements matched the reported widths. The downside of this dataset is that the .csv format does not conserve the latitude and longitude values.
                        We also use the City of Boston’s 311 service requests dataset, which consist of pedestrian and citizen reports of maintenance/repair as well as safety complaints all culminating in a repository of filterable data that can be used to draw inferences on areas for improvement around Mass Ave. The type of complaint and location is qualitative data, but the counts of the number of complaints and other aggregated data are numerical. Given the project’s goal of gauging the accessibility of the Mass Ave neighborhood, we are focused on displaying attributes of the requests related to sidewalks, snow removals, and other road safety.
                        """),
    ], style={'textAlign': 'center', 'marginBottom': 50, 'marginTop': 25, 'marginLeft': 200, 'marginRight': 200}),
]

# TASK PAGE
children_task_analysis = [
    html.Br(),
    html.H1(children=dcc.Markdown('**Group 15: Compatible City**')),
    html.H2(children='Joshua Peirce, Rachel Utama, Kyle Rudman'),
    html.Br(),
    html.Div([

        # task analysis
        html.H2(children='Task Analysis'),
        html.P(children="""The interview with Carol from the Mass Ave Coalition helped shed some light on the current issues that she sees regarding accessibility and compatibility. We asked about sidewalks on Mass Ave, and whether there were any current initiatives regarding improving them. Although she did not know of any active Mass Ave Coalition projects, she suggested looking into city initiatives. She said that most of the sidewalks were built to meet the city’s requirements, but those sidewalks still resulted in a width of 3 to 5 feet that was not wide enough to support public spaces and keep people from walking in two directions without having to compromise personal space. Another great point that she made was the issue with water drainage and snow removal. Whenever there is big snow removal, the snow gets pushed into areas where there aren’t any cars, which can block the sidewalk access. She also brought up the human element that is often missing when city planners are designing sidewalks: the multiple uses of the sidewalks as a space for community building. Oftentimes, these sidewalks are playing a double or triple role, as a bus stop, or a place where neighbors might want to stop and chat or teach their kids to ride a bike. It’s super important to consider these uses beyond commuting when we’re dealing with data about where the sidewalks are located. Overall, since Mass Ave has yet to work on projects regarding accessibility, our project is a sort of test pilot for checking out the data that already exists, and presenting our findings to give the coalition a clear starting point for how they might be able to contribute to this area. This made identifying tasks a bit tricky, but after a discussion with Professor Borkin, we were able to identify the task of evaluating the accessibility of Mass Ave based on the current state of the sidewalks. Our main focuses for task analysis are evaluating the accuracy and quality of the current data on sidewalk accessibility in Boston, identifying areas in Mass Ave that are relatively accessible or inaccessible, and looking for trends with 311 service requests regarding sidewalks and snow removal.
                        """),
        html.Br(),
        html.H2(children='Task Analysis Table'),
        html.P(children="Task Number | Task Description | Low Level Query | Mid Level Query | High Level Query "),
        html.P(children="Task 1: Identify areas that are lacking in accessibility | Filter | Explore, Discover, Present"),
        html.P(children="Task 2: Highlight certain issues and locations with supplemental data/visualizations | Retrieve Value, Find Anomalies, Find Extremum | Lookup | Annotate, Derive, Enjoy"),
        html.P(children="Task 3: Charts “landmarks” of accessibility and/or inaccessibility along Mass Ave | Characterize distribution | Browse | Record, Present"),
        html.P(children="Task 4: Evaluate the current data’s ability to assess accessibility by comparing it to anecdotal data |  Find anomalies | Explore | Discover and Present"),
        html.P(children="Task 5: Identify most problematic areas following snow clearing | Find anomalies | Explore | Discover and Present"),
        html.Br(),
    ], style={'textAlign': 'center', 'marginBottom': 50, 'marginTop': 25, 'marginLeft': 200, 'marginRight': 200}),
]

# data analysis PAGE
children_data_analysis = [
    html.Br(),
    html.H1(children=dcc.Markdown('**Group 15: Compatible City**')),
    html.H2(children='Joshua Peirce, Rachel Utama, Kyle Rudman'),
    html.Br(),

    html.Div([
        # data analysis
        html.H2(children='Data Analysis'),
        html.P(children="""Our initial attempts at data analysis directed our attention to the greater underlying issue of a lack of quality data that can answer the question of evaluating sidewalk accessibility. The data we were given was built off of sewer locations and was useful for mapping where sidewalk spaces have been allocated but are not sufficient to reflect a pedestrian’s point of view on accessibility. Additionally, through collecting a small portion of anecdotal data measuring sidewalk widths, we found that the data available from the city’s sidewalk inventory is not entirely representative of the reality of the situation, and can overstate sidewalk widths and/or overlook areas where the sidewalk width is significantly compromised by obstructions (trees, lamp posts, power blocks, etc.). The sidewalk centerline data accurately maps sewer locations based on sidewalk centerlines but does not reflect areas where the “sidewalk” is merely an extension of a driveway or any other safety hazards. While walking along our portion of Mass Ave, we found a sidewalk portion that was the driveway of a commonly used gas station — all going to show that the data can only show what the data shows, and we were inhibited from fully answering our initial question. Our data visualization seeks to establish the baseline — Mass Ave needs data on the sidewalks that accurately record the sidewalk widths. Another insight came from our data visualization of the 311 service requests — the response time to a service request pertaining to sidewalks in this area is very fast. Over 75% of the time, the city responds within 5 days, and over half the time in less than one, but on average there are fewer requests per resident in Roxbury than in Boston as a whole—we interpret this as a possible indicator that the Roxbury has fewer outstanding accessibility issues than the rest of Boston.
                            Our anecdotal data on sidewalk accessibility demonstrates that most of Mass Ave can be deemed relatively accessible if the guideline is that the sidewalk must be at least 8 ft. There were many points at which the sidewalk is only 4 ft because of trees or other obstructions. However, we agree that there isn’t much that the city can do about changing that without compromising the space for the roads. Many common red flags for accessibility were bumps in the sidewalk brick that could potentially be dangerous for any disabled persons or pedestrians walking over it and a couple of narrower sidewalk areas below 8ft which we had to walk in a single file to avoid bumping into people walking the opposite way. With these factors that should be considered from an accessibility standpoint, we hope our project can spearhead any future data collection on the conditions of the sidewalks.
                            """),
    ], style={'textAlign': 'center', 'marginBottom': 50, 'marginTop': 25, 'marginLeft': 200, 'marginRight': 200}),
]

# design process PAGE
children_design_process = [
    html.Br(),
    html.H1(children=dcc.Markdown('**Group 15: Compatible City**')),
    html.H2(children='Joshua Peirce, Rachel Utama, Kyle Rudman'),
    html.Br(),

    html.Div([

        # Design Process
        html.H2(children='Design Process'),
        html.P(children="""We chose to prioritize identifying areas that are low and high accessibility with our visualization, which we do in a handful of ways. We have the “accessibility” as one metric in the panel off to the side, and translates to the color shown on the map. We also point out all the 311 requests and problematic spots we identified as a group on the map as clickable infographic popups. Lastly, these clickable annotations to the graph bring up a side panel that gives more details about what each annotation is about. By the concentration of icons as well as the color of the map, the areas in need of attention stick out from the rest.
                            We wanted to express the values of the widths and the subjective accessibility scores according to the user’s options using the color and width of the line. Our visual encodings were designed to arrange the data spatially and enable the user to separate regions deemed inaccessible versus those deemed accessible. As our geospatial data only lends itself to being represented on a map. As for the other details we wanted to show - the 311 service requests and the pictures we took touring Mass Ave - those lent themselves to clickable icons, as each had too much data attached to it to show all at once. Therefore, we chose to make infographics on the side that appear when these icons are clicked.

                            """),

        # Conclusion
        html.H2(children='Conclusion'),
        html.P(children="""The Compatible City project lays the foundation for exploring accessibility along Massachusetts Ave, exploring an overarching question of “Are Mass Ave’s sidewalks accessible—both in terms of meeting city regulations, and in reality?”. The main roadblocks we encountered, including a lack of reliable and helpful data, were indicators that the situation is in great need of attention and increased awareness among the public. Our project resulted in an interactive dashboard with two interactive visualizations—sidewalk inaccessibility and 311 service requests. The former demonstrates that based on our measurements, select sidewalk sections of Mass Ave are not wide enough to meet the city’s regulations, despite being officially recorded as such. We suggest that the city update and evaluate the current data to have a more accurate reflection of the pedestrian experience. The second visualization allows users to grasp a better visual and geospatial understanding of where common sidewalks complaints reside, and how different requests are being handled in each area. The 311 service requests map demonstrates that there are still many sidewalk-related requests that go unresolved. Our city still has some ways to go. Future work would involve more data collection on sidewalks, ramps, and crosswalks along Mass Ave from a pedestrian’s perspective. We would also like to locate where T stops, puddles, trees, and lamposts may be causing safety issues for pedestrians. Our recommendation to Mass Ave Coalition would be to request a more thorough and updated evaluation of sidewalk compatibility and safety.
                            """),
    ], style={'textAlign': 'center', 'marginBottom': 50, 'marginTop': 25, 'marginLeft': 200, 'marginRight': 200}),
]


# ACCESSIBILITY PAGE
children_accessibility = [
    html.Div([
        html.H2(dcc.Markdown(
            "**City's Recorded Sidewalk Widths: Not Completely Accurate?**")),
        html.Br(),
        html.H4("Comparing City's Recorded Sidewalk Widths vs. Our Measurements"),

        html.P(dcc.Markdown('''
                        The state of Massachusetts defines a publicly-accessible sidewalk to be at least **8 feet wide**. However, survey research has shown that an even wider sidewalk is a common solution to improve pedestrian safety and allow for a better flow of foot traffic. [For more information check out walkability guide] (https://www.mass.gov/files/documents/2018/09/17/MunicipalResourcesGuideForWalkability_2018-08-24.pdf).
        ''')),

        html.P('Depending on your own definition of an accessible sidewalk width, adjust the slider below to see what segments of Mass Ave are accessible.'),


        # slider
        dcc.Slider(4, 10, 0.1,
                   marks={
                       4: '4 ft',
                       5: '5 ft',
                       6: '6 ft',
                       7: '7 ft',
                       8: '8 ft',
                       9: '9 ft',
                       10: '10 ft'
                   },
                   value=8,
                   id='sw_width_slider_input'
                   ),
        html.H4(id='selected_thresh'),

        # map of Mass Ave
        dcc.Graph(id="sw_map"),

        # bar plot for lass data
        dcc.Graph(id="measurement_error_bar"),

    ], style={'textAlign': 'center', 'marginBottom': 50, 'marginTop': 50, 'marginLeft': 200, 'marginRight': 200}),
    html.Br(),
    html.Div(),
    html.P(dcc.Markdown('''
                        This visualization is generated from manually-collected data which features coordinate values of Mass Ave sidewalk segments (defined as the stretch of the sidewalk between intersecting streets) along with an average width measurement.
                        
        ''')),

]

# 311 PAGE
children_311 = [
    html.Br(),
    html.H2(dcc.Markdown('**Locating Hotspots for Sidewalk Service Requests**')),
    html.Div([  # Bottom half - 311 map
        html.Div([  # (Select-date AND Show-all) OR Filter-by-date
            html.Div([  # Select-date AND Show-all
                html.H4('Select date', id="Date-instructions",
                        style={"display": "inline-block"}),
                html.Button("Show all", id="show-all-button",
                            style={"display": "inline-block"})
            ], id="div-sd-sa",
                style={"display": "block", "padding": "20 20"}),
            html.Div([  # Filter-by-date
                html.Button("Filter by date",
                            id="filter-by-date-button")
            ], id="div-fbd", style={"display": "None"}),
            html.P('Boston’s 311 service requests consist of pedestrian and citizen reports of maintenance/repair as well as safety complaints. Displayed on the map below are all requests pertaining to sidewalk improvements: snow removal, sidewalk repairs, unsafe curbs, etc. We have allowed you to filter the data by a timeline as well as select portions of the map to see the counts of open/closed cases at various times. Based on its functionality, this visualization can be helpful in illustrating the persistent sidewalk accessibility issues and areas needing improvement around Mass Ave.'),
        ], style={'marginLeft': '4em', 'marginRight': '4em', 'marginBottom': 50, 'marginTop': 25, }),


        html.Div([  # Left panel
            html.Div([  # Slider div
                dcc.RangeSlider(
                    id='date-slider',
                    min=unixTimeMillis(df_311["open_dt"].min()),
                    max=unixTimeMillis(df_311["open_dt"].max()),
                    value=[unixTimeMillis(df_311["open_dt"].max(
                    )) - ONE_YEAR, unixTimeMillis(df_311["open_dt"].max())],
                    marks=getMarks(df_311["open_dt"].min(),
                                   df_311["open_dt"].max(), Nth=2000))
            ], id="Slider-div", style={'textAlign': 'center'}),
            dcc.Graph(id='311_map'),
        ],
            style={"width": "50%", "padding": "0 20", "display": "inline-block", 'textAlign': 'center'}),
        html.Div([  # Right panel
            html.Div([  # Graph - shown when area selected, hidden by default
                dcc.Graph(id="static_subplot")], id="graph-div"),
            html.Div(  # Request details - shown when point clicked
                [
                    html.H4(id="req-details-case-title"),  # Case title
                    # Picture
                    html.Img(id="req-details-submittedphoto", style={
                        "width": "100%",
                        "max-width": "480px",
                        "height": "100%",
                        "max-height": "270px",
                        'textAlign': 'center'
                    }),
                    html.H5(id="req-details-open-date"),  # Open date
                    html.H5(id="req-details-status"),  # Status
                    # Closed date
                    html.H5(id="req-details-closed-date"),
                    # Closure reason
                    html.H5(id="req-details-closed-reason"),
                    # Closure picture
                    html.Img(id="req-details-closed-photo", style={
                        "width": "100%",
                        "max-width": "480px",
                        "height": "100%",
                        "max-height": "270px",
                        'textAlign': 'center'
                    })
                ],
                id="req-details-div",
                style={"display": "none"})],
            style={"width": "50%", "padding": "0 20", "display": "inline-block"})
    ], style={'textAlign': 'center', 'marginBottom': 50, 'marginTop': 25})]


# LAYOUT
app.layout = html.Div([
    dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src='assets/logo.png',
                                    alt='image', height="60px")),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="https://www.khoury.northeastern.edu/",
                    style={"textDecoration": "none"},
                ),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            ]
        ),
        color="darkblue",
        dark=True,
    ),
    html.Div([
        dcc.Tabs([
            dcc.Tab(label="Motivation",
                    id="tab-motivation", children=children_motivation,
                    style={'padding': '0 20', "display": "block"}),

            dcc.Tab(label="Data", id="tab-data",
                    children=children_data,
                    style={'padding': '0 20', "display": "block"}),

            dcc.Tab(label="Task Analysis", id="tab-ta", children=children_task_analysis,
                    style={'padding': '0 20', "display": "block"}),  # 'display': 'inline-block',

            dcc.Tab(label="Data Analysis",
                    id="tab-da", children=children_data_analysis,
                    style={'padding': '0 20', "display": "block"}),

            dcc.Tab(label="Design Process", id="tab-dp",
                    children=children_design_process,
                    style={'padding': '0 20', "display": "block"}),

            dcc.Tab(label="Sidewalk Accessibility Map", id="tab-accessibility",
                    children=children_accessibility,
                    style={'padding': '0 20', "display": "block"}),

            dcc.Tab(label="311 Sidewalk Service Requests", id="tab-311", children=children_311,
                    style={'padding': '0 20', "display": "block"})  # 'display': 'inline-block',
        ])], style={'textAlign': 'center'})


], style={'textAlign': 'center', 'marginBottom': 50})

if __name__ == '__main__':
    app.run_server(debug=False)
