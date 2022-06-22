import numpy as np

from landlab import Component
from landlab.layers import EventLayers


class Sequence(Component):
    _name = "Sequence"
    _unit_agnostic = True
    _info = {
        "topographic__elevation": {
            "dtype": "float",
            "intent": "inout",
            "optional": False,
            "units": "m",
            "mapping": "node",
            "doc": "land and ocean bottom elevation, positive up",
        },
        "bedrock_surface__elevation": {
            "dtype": "float",
            "intent": "inout",
            "optional": True,
            "units": "m",
            "mapping": "node",
            "doc": "New bedrock elevation following subsidence",
        },
        "sea_level__elevation": {
            "dtype": "float",
            "intent": "inout",
            "optional": False,
            "units": "m",
            "mapping": "grid",
            "doc": "Sea level elevation",
        },
        "sediment_deposit__thickness": {
            "dtype": "float",
            "intent": "in",
            "optional": False,
            "units": "m",
            "mapping": "node",
            "doc": "Thickness of deposited or eroded sediment",
        },
    }

    def __init__(self, grid, time_step=100.0, components=None, track=None):
        self._components = () if components is None else tuple(components)
        track = [] if track else track

        super().__init__(grid)

        self._time = 0.0
        self._time_step = time_step

        self.grid.at_layer_grid = EventLayers(1)
        self.grid.at_layer_grid.add(
            1.0, age=0.0, sea_level=0.0, x_of_shore=0, x_of_shelf_edge=0
        )

        if "bedrock_surface__elevation" not in self.grid.at_node:
            self.grid.add_field(
                "bedrock_surface__elevation",
                self.grid.at_node["topographic__elevation"] - 100,
                at="node",
            )
        initial_sediment_thickness = (
            self.grid.at_node["topographic__elevation"]
            - self.grid.at_node["bedrock_surface__elevation"]
        )

        self.add_layer(initial_sediment_thickness[self.grid.node_at_cell])

    @property
    def time(self):
        return self._time

    def update(self, dt=None):
        dt = self._time_step if dt is None else dt

        for component in self._components:
            component.run_one_step(dt=dt)

        self.add_layer(
            self.grid.at_node["sediment_deposit__thickness"][self.grid.node_at_cell]
        )

        self._time += dt

    def layer_properties(self):
        dz = self.grid.at_node["sediment_deposit__thickness"]
        water_depth = (
            self.grid.at_grid["sea_level__elevation"]
            - self.grid.at_node["topographic__elevation"]
        )

        properties = {
            "age": self.time,
            "water_depth": water_depth[self.grid.node_at_cell],
            "t0": dz[self.grid.node_at_cell].clip(0.0),
        }

        try:
            percent_sand = self.grid.at_node["delta_sediment_sand__volume_fraction"]
        except KeyError:
            pass
        else:
            properties["percent_sand"] = percent_sand[self.grid.node_at_cell]

        return properties

    def layer_reducers(self):
        reducers = {
            "age": np.max,
            "water_depth": np.mean,
            "t0": np.sum,
        }
        if "percent_sand" in self.grid.event_layers.tracking:
            reducers["percent_sand"] = np.mean
        # porosity = np.mean
        return reducers

    def add_layer(self, dz_at_cell):
        self.grid.event_layers.add(dz_at_cell, **self.layer_properties())
        self.grid.at_layer_grid.add(
            1.0,
            age=self.time,
            sea_level=self.grid.at_grid["sea_level__elevation"],
            x_of_shore=self.grid.at_grid["x_of_shore"],
            x_of_shelf_edge=self.grid.at_grid["x_of_shelf_edge"],
        )

        try:
            self._n_archived_layers
        except AttributeError:
            self._n_archived_layers = 0

        if (
            self.grid.event_layers.number_of_layers - self._n_archived_layers
        ) % 20 == 0:
            self.grid.event_layers.reduce(
                self._n_archived_layers,
                self._n_archived_layers + 10,
                **self.layer_reducers(),
            )
            self._n_archived_layers += 1