from dash import Dash, html, dcc, Input, Output, State
import plotly.graph_objects as go
import logging
import numpy as np


def buildGroups(hullSets):
    layers = []
    for hull in hullSets:
        layer = dict(
            sourcetype='geojson',
            source={"type": "Feature", "geometry": {"type": "MultiLineString", "coordinates": hull}},
            color='red',
            type='line',
            line=dict(width=1.5),
        )
        layers.append(layer)
    return layers


class dataVisualizer:

    def __init__(self, analyzer):

        self.analyzer = analyzer
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.mapCenterLat = 42.062220
        self.mapCenterLon = -87.678361
        scatter = self.buildScatter(self.analyzer.positions, self.analyzer.hullSets)
        density = self.buildDensity(self.analyzer.positions)

        self.app = Dash()
        self.app.layout = [
            html.Div(children='Crowds'),
            dcc.Graph(id='scatter-graph', figure=scatter),
            html.Div(children='Density'),
            dcc.Graph(id='density-graph', figure=density),
            dcc.Interval(id='interval', interval=100),
        ]
        self.setupCallbacks()
        self.app.run()

    def setupCallbacks(self):
        @self.app.callback(
            Output('scatter-graph', 'figure'),
            Input('interval', 'n_intervals'),
            State('scatter-graph', 'figure'),
        )
        def update_scatter(n, figure):
            scatter = self.buildScatter(self.analyzer.positions, self.analyzer.hullSets)
            scatter.update_layout(map_center=figure['layout']['map']['center'])
            return scatter

        @self.app.callback(
            Output('density-graph', 'figure'),
            Input('interval', 'n_intervals'),
            State('density-graph', 'figure'),
        )
        def update_density(n, figure):
            density = self.buildDensity(self.analyzer.positions)
            density.update_layout(map_center=figure['layout']['map']['center'])
            return density

    def buildScatter(self, positions, hulls):
        fig = go.Figure(
            go.Scattermap(
                lat=positions['lat'],
                lon=positions['lon'],
                mode='markers',
                text=positions['id'],
                marker=go.scattermap.Marker(size=10, color=positions['color']),
            )
        )

        layers = buildGroups(hulls)

        fig.update_layout(
            map_style="open-street-map",
            map_zoom=16,
            map_center={"lat": self.mapCenterLat, "lon": self.mapCenterLon},
            map_layers=layers,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            uirevision='scatter',
        )

        return fig

    def buildDensity(self, positions):
        positions = positions[positions['type'] == 'car']
        fig = go.Figure(
            go.Densitymap(
                lat=positions['lat'],
                lon=positions['lon'],
                # z=positions['color'],  # You can choose a variable to represent intensity (e.g., 'color')
                radius=10,  # You can adjust the radius of influence for each point
                colorscale='Viridis',  # You can customize the color scale
                # colorbar=dict(title="Density"),  # Add a color bar if desired
            )
        )

        fig.update_layout(
            map_style="open-street-map",
            map_zoom=16,
            map_center={"lat": self.mapCenterLat, "lon": self.mapCenterLon},
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            uirevision='density',
        )

        return fig
