from dash import Dash, html, dcc, Input, Output, State
import time
import math
import pandas as pd
import plotly.graph_objects as go
import threading


class pdm:

    def __init__(self):
        self.mapCenterLat = 42.062220
        self.mapCenterLon = -87.678361
        self.positions = pd.DataFrame({'id': [], 'lat': [], 'lon': [], 'alt': [], 'time': []})
        fig = self.buildFigure(self.positions)

        self.app = Dash()
        self.app.layout = [
            html.Div(children='Location'),
            dcc.Graph(id='live-graph', figure=fig),
            dcc.Interval(id='interval', interval=1000),
        ]
        self.setupCallbacks()

        self.plotThread = threading.Thread(target=self.appRunner)
        # self.app.run(debug=True)
        self.plotThread.start()

    def appRunner(self):
        self.app.run(debug=True)

    def updatePositions(self, row):
        # update existing row
        if row["id"] in self.positions["id"].values:
            self.positions.loc[self.positions["id"] == row["id"], :] = row
        # append row if new detection
        else:
            self.positions = self.positions[len(self.positions)] = row

        # latitude = self.positions.loc[self.positions['name'] == 'Plane', 'lat']
        # longitude = self.positions.loc[self.positions['name'] == 'Plane', 'lon']
        # latitude = latitude + 0.0001 * math.cos(0.1 * n)
        # longitude = longitude + 0.0001 * math.sin(0.1 * n)
        # self.positions.loc[self.positions['name'] == 'Plane', 'lat'] = latitude
        # self.positions.loc[self.positions['name'] == 'Plane', 'lon'] = longitude

    def setupCallbacks(self):
        @self.app.callback(
            Output('live-graph', 'figure'),
            Input('interval', 'n_intervals'),
            State('live-graph', 'figure'),
        )
        def update_graph(n, figure):
            fig = self.buildFigure(self.positions)
            fig.update_layout(map_center=figure['layout']['map']['center'])
            return fig

    def buildFigure(self, positions):
        fig = go.Figure(
            go.Scattermap(
                lat=positions['lat'],
                lon=positions['lon'],
                mode='markers',
                text=positions['id'],
                marker=go.scattermap.Marker(size=14),
            )
        )

        fig.update_layout(map_style="open-street-map")
        fig.update_layout(map_zoom=16)
        fig.update_layout(map_center={"lat": self.mapCenterLat, "lon": self.mapCenterLon})
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig.update_layout(uirevision='same')
        return fig


if __name__ == '__main__':
    myPdm = pdm()
