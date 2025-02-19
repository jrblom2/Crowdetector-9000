from dash import Dash, html, dcc, Input, Output, State
import time
import math
import pandas as pd
import plotly.graph_objects as go
import threading
import logging


class dataVisualizer:

    def __init__(self, analyzer):

        self.analyzer = analyzer
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.mapCenterLat = 42.062220
        self.mapCenterLon = -87.678361
        fig = self.buildFigure(self.analyzer.positions)

        self.app = Dash()
        self.app.layout = [
            html.Div(children='Location'),
            dcc.Graph(id='live-graph', figure=fig),
            dcc.Interval(id='interval', interval=100),
        ]
        self.setupCallbacks()
        self.app.run()

    def setupCallbacks(self):
        @self.app.callback(
            Output('live-graph', 'figure'),
            Input('interval', 'n_intervals'),
            State('live-graph', 'figure'),
        )
        def update_graph(n, figure):
            fig = self.buildFigure(self.analyzer.positions)
            fig.update_layout(map_center=figure['layout']['map']['center'])
            return fig

    def buildFigure(self, positions):
        fig = go.Figure(
            go.Scattermap(
                lat=positions['lat'],
                lon=positions['lon'],
                mode='markers',
                text=positions['id'],
                marker=go.scattermap.Marker(size=10, color=positions['color']),
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
