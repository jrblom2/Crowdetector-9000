import logging

import plotly.graph_objects as go
import yaml
from dash import Dash, Input, Output, State, dcc, html


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
        with open("config.yaml", "r") as f:
            self.config = yaml.safe_load(f)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        self.mapCenterLat = self.config['map']['centerLat']
        self.mapCenterLon = self.config['map']['centerLon']
        scatter = self.buildScatter(self.analyzer.positions, self.analyzer.hullSets)
        density = self.buildDensity(self.analyzer.positions)

        self.app = Dash()
        self.app.layout = [
            dcc.Graph(id='scatter-graph', figure=scatter),
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
            density = self.buildDensity(self.analyzer.positionsLong)
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
            map_zoom=17,
            map_center={"lat": self.mapCenterLat, "lon": self.mapCenterLon},
            map_layers=layers,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            uirevision='scatter',
        )

        return fig

    def buildDensity(self, positions):
        fig = go.Figure()
        for i, type in enumerate(self.config['analyze']['detections']):
            filter = positions[positions['type'] == type]
            fig.add_trace(
                go.Densitymap(
                    lat=filter['lat'],
                    lon=filter['lon'],
                    radius=10,
                    colorscale=self.config['analyze']['colors'][i],
                    reversescale=True,
                    showlegend=False,
                    showscale=False,
                )
            )

        fig.update_layout(
            map_style="satellite-streets",
            map_zoom=15.8,
            map_center={"lat": self.mapCenterLat, "lon": self.mapCenterLon},
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            uirevision='density',
        )

        return fig
