from pymavlink import mavutil
from dash import Dash, html, dcc, Input, Output, State
import time
import math
import pandas as pd
import plotly.graph_objects as go

latitude = 42.062220
longitude = -87.678361

positions = pd.DataFrame(
    {'lat': [latitude], 'lon': [longitude], 'name': ['Plane'], 'time': [0]}
)

fig = go.Figure(
    go.Scattermap(
        lat=positions['lat'],
        lon=positions['lon'],
        mode='markers',
        text=positions['name'],
        marker=go.scattermap.Marker(size=14),
    )
)

fig.update_layout(map_style="open-street-map")
fig.update_layout(map_zoom=16)
fig.update_layout(map_center={"lat": latitude, "lon": longitude})
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig.update_layout(uirevision='same')

app = Dash()
app.layout = [
    html.Div(children='Location'),
    dcc.Graph(id='live-graph', figure=fig),
    dcc.Interval(id='interval', interval=1000),
]


@app.callback(
    Output('live-graph', 'figure'),
    Input('interval', 'n_intervals'),
    State('live-graph', 'figure'),
)
def update_graph(n, figure):
    global latitude
    global longitude
    print(figure["layout"])
    latitude = latitude + 0.00001 * math.cos(0.1 * n)
    longitude = longitude + 0.00001 * math.sin(0.1 * n)

    positions = pd.DataFrame(
        {'lat': [latitude], 'lon': [longitude], 'name': ['Plane'], 'time': [0]}
    )

    fig = go.Figure(
        go.Scattermap(
            lat=positions['lat'],
            lon=positions['lon'],
            mode='markers',
            text=positions['name'],
            marker=go.scattermap.Marker(size=14),
        )
    )
    fig.update_layout(map_style="open-street-map")
    fig.update_layout(map_zoom=16)
    fig.update_layout(map_center=figure['layout']['map']['center'])
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_layout(uirevision='same')
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)

# # Set up connection to vehicle
# master = mavutil.mavlink_connection('udp:localhost:14445')

# # Wait for the heartbeat message to ensure connection
# master.wait_heartbeat()

# while 1:
#     msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=False)
#     if msg is not None:
#         print(msg.lat)
#     time.sleep(0.01)
