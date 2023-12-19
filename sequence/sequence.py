"""*Sequence*'s main API for constructing sequence-stratigraphic models."""
from collections.abc import Iterable
from typing import Any
from typing import Optional

import numpy as np
from landlab import Component
from landlab.layers import EventLayers
from numpy.typing import ArrayLike
from numpy.typing import NDArray
from tqdm import trange

from sequence._grid import SequenceModelGrid
from sequence.plot import plot_grid


class Sequence(Component):
    """*Landlab* component interface to the *Sequence* model."""

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

    def __init__(
        self,
        grid: SequenceModelGrid,
        time_step: float = 100.0,
        components: Optional[Iterable] = None,
    ):
        """Create a Sequence model.

        Parameters
        ----------
        grid : SequenceModelGrid
            A model grid.
        time_step : float, optional
            The time step at which the model will run each of its components.
        components : iterable, optional
            A list of components to run every time step.
        """
        self._components = () if components is None else tuple(components)
        # track = [] if track else track

        super().__init__(grid)

        self._time = 0.0
        self._time_step = time_step
        self._n_archived_layers = 0

        self.grid.at_layer_grid = EventLayers(1)
        self.grid.at_layer_row = EventLayers(grid.number_of_rows)

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

        if (initial_sediment_thickness[self.grid.node_at_cell] > 0.0).any():
            self.add_layer(initial_sediment_thickness[self.grid.node_at_cell])

        self.grid.at_node["topographic__elevation"][self.grid.node_at_cell] = (
            self.grid.at_node["bedrock_surface__elevation"][self.grid.node_at_cell]
            + self.grid.event_layers.thickness
        )
        self.grid.at_node["sediment_deposit__thickness"].fill(0.0)

    @property
    def time(self) -> float:
        """Return the current model time (in years)."""
        return self._time

    def update(self, dt: Optional[float] = None) -> None:
        """Update the model of a given time step.

        Parameters
        ----------
        dt : float, optional
            The length of time to run the model for. If not given,
            update the model a single time step.
        """
        dt = self._time_step if dt is None else dt

        for component in self._components:
            component.run_one_step(dt=dt)

        self._time += dt

        self.add_layer(
            self.grid.at_node["sediment_deposit__thickness"][self.grid.node_at_cell]
        )
        self.grid.at_node["topographic__elevation"][self.grid.node_at_cell] = (
            self.grid.at_node["bedrock_surface__elevation"][self.grid.node_at_cell]
            + self.grid.event_layers.thickness
        )
        self.grid.at_node["sediment_deposit__thickness"].fill(0.0)

    def run(
        self,
        until: Optional[float] = None,
        dt: Optional[float] = None,
        progress_bar: bool = True,
    ) -> None:
        """Run the model to a given time.

        Parameters
        ----------
        until : float, optional
            The time (in years) to run the model to. If not provided, run
            for a single time step.
        dt : float, optional
            Run using a time step other than what the component was initialized with.
        progress_bar : bool, optional
            If ``True`` display a progress bar while the model is running.
        """
        dt = self._time_step if dt is None else dt
        until = self._time + self._time_step if until is None else until

        n_steps = int((until - self.time) // dt)
        if (until - self.time) % dt > 0:
            n_steps += 1

        for _ in trange(n_steps, desc="🚀", disable=not progress_bar):
            self.update(dt=min(dt, until - self._time))

    def layer_properties(self) -> dict[str, ArrayLike]:
        """Return the properties being tracked at each layer.

        Returns
        -------
        properties : dict
            A dictionary of the tracked properties where the keys
            are the names of properties and the values are the
            property values at each column.
        """
        dz = self.grid.at_node["sediment_deposit__thickness"]
        water_depth = (
            self.grid.at_grid["sea_level__elevation"]
            - self.grid.at_node["topographic__elevation"]
        )

        properties = {
            "age": self.time,
            "water_depth": water_depth[self.grid.node_at_cell],
            "t0": dz[self.grid.node_at_cell].clip(0.0),
            "porosity": 0.5,
        }

        try:
            percent_sand = self.grid.at_node["delta_sediment_sand__volume_fraction"]
        except KeyError:
            pass
        else:
            properties["percent_sand"] = percent_sand[self.grid.node_at_cell]

        return properties

    def layer_reducers(self) -> dict[str, Any]:
        """Return layer-reducers for each property.

        Returns
        -------
        reducers : dict
            A dictionary of reducers where keys are property names and values
            are functions that act as layer reducers for those quantities.
        """
        reducers = {
            "age": np.max,
            "water_depth": np.mean,
            "t0": np.sum,
            "porosity": np.mean,
        }
        if "percent_sand" in self.grid.event_layers.tracking:
            reducers["percent_sand"] = np.mean

        return reducers

    def add_layer(self, dz_at_cell: NDArray[np.floating]) -> None:
        """Add a new layer to each cell.

        Properties
        ----------
        dz_at_cell : array-like
            Thickness of the new layers for each cell along the profile.
        """
        try:
            x_of_shore = self.grid.at_grid["x_of_shore"]
        except KeyError:
            x_of_shore = np.nan
        try:
            x_of_shelf_edge = self.grid.at_grid["x_of_shelf_edge"]
        except KeyError:
            x_of_shelf_edge = np.nan
        try:
            x_of_shores = self.grid.at_row["x_of_shore"]
        except KeyError:
            x_of_shores = np.full(self.grid.number_of_rows, np.nan)
        try:
            x_of_shelf_edges = self.grid.at_row["x_of_shelf_edge"]
        except KeyError:
            x_of_shelf_edges = np.full(self.grid.number_of_rows, np.nan)

        self.grid.at_node["topographic__elevation"][
            self.grid.node_at_cell
        ] += dz_at_cell

        self.grid.event_layers.add(dz_at_cell, **self.layer_properties())
        self.grid.at_layer_grid.add(
            1.0,
            age=self.time,
            sea_level=self.grid.at_grid["sea_level__elevation"],
            x_of_shore=x_of_shore,
            x_of_shelf_edge=x_of_shelf_edge,
        )
        self.grid.at_layer_row.add(
            1.0,
            age=self.time,
            sea_level=self.grid.at_grid["sea_level__elevation"],
            x_of_shore=x_of_shores,
            x_of_shelf_edge=x_of_shelf_edges,
        )

        if (
            self.grid.event_layers.number_of_layers - self._n_archived_layers
        ) % 20 == 0:
            self.grid.event_layers.reduce(
                self._n_archived_layers,
                self._n_archived_layers + 10,
                **self.layer_reducers(),
            )
            self._n_archived_layers += 1

    def plot(self) -> None:
        """Plot the grid."""
        plot_grid(self.grid)
