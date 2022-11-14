"""Build a `SequenceModelGrid` model from collection of components."""
import logging
import os
import time
import warnings
from collections import OrderedDict, defaultdict
from collections.abc import Hashable, Iterable
from typing import Any, Dict, Optional

import numpy as np
import tomlkit
from compaction.landlab import Compact
from landlab.bmi.bmi_bridge import TimeStepper
from numpy.typing import ArrayLike

from ._grid import SequenceModelGrid
from .bathymetry import BathymetryReader
from .fluvial import Fluvial
from .output_writer import OutputWriter
from .sea_level import SeaLevelTimeSeries, SinusoidalSeaLevel
from .sediment_flexure import SedimentFlexure
from .shoreline import ShorelineFinder
from .submarine import SubmarineDiffuser
from .subsidence import SubsidenceTimeSeries

logger = logging.getLogger("sequence")


class SequenceModel:
    """Orchestrate a set of components that operate on a `SequenceModelGrid`."""

    ALL_PROCESSES = (
        "sea_level",
        "subsidence",
        "compaction",
        "submarine_diffusion",
        "fluvial",
        "flexure",
    )
    DEFAULT_PARAMS = {
        "grid": {"n_cols": 100, "spacing": 1000.0},
        "clock": {"start": 0.0, "stop": 600000.0, "step": 100.0},
        "output": {
            "interval": 10,
            "filepath": "sequence.nc",
            "clobber": True,
            "rows": [1],
            "fields": ["sediment_deposit__thickness", "bedrock_surface__elevation"],
        },
        "submarine_diffusion": {
            "plain_slope": 0.0008,
            "wave_base": 60.0,
            "shoreface_height": 15.0,
            "alpha": 0.0005,
            "shelf_slope": 0.001,
            "sediment_load": 3.0,
            "load_sealevel": 0.0,
            "basin_width": 500000.0,
        },
        "sea_level": {
            "amplitude": 10.0,
            "wave_length": 200000.0,
            "phase": 0.0,
            "linear": 0.0,
        },
        "subsidence": {"filepath": "subsidence.csv"},
        "flexure": {"method": "flexure", "rho_mantle": 3300.0, "isostasytime": 0},
        "sediments": {
            "layers": 2,
            "sand": 1.0,
            "mud": 0.006,
            "sand_density": 2650.0,
            "mud_density": 2720.0,
            "sand_frac": 0.5,
            "hemipelagic": 0.0,
        },
        "bathymetry": {"filepath": "bathymetry.csv", "kind": "linear"},
        "compaction": {
            "c": 5.0e-08,
            "porosity_max": 0.5,
            "porosity_min": 0.01,
            "rho_grain": 2650.0,
            "rho_void": 1000.0,
        },
    }

    LONG_NAME = {"z": "topographic__elevation", "z0": "bedrock_surface__elevation"}

    def __init__(
        self,
        grid: SequenceModelGrid,
        clock: Optional[dict] = None,
        processes: Optional[dict] = None,
        output: Optional[dict] = None,
    ):
        """Create a model on a `SequenceModelGrid`.

        Parameters
        ----------
        grid : SequenceModelGrid
            The grid on which the model is run.
        clock : dict
            Parameters for the model's clock.
        processes : iterable of components
            A list of the components to run as part of the model.
        output : component
            A component used to write output files.
        """
        if processes is None:
            processes = {}

        self._grid = grid
        self._clock = TimeStepper(**clock)
        self._components = OrderedDict(processes)
        if output is not None:
            self._components["output"] = OutputWriter(self._grid, **output)

        self.grid.at_grid["x_of_shore"] = np.nan
        self.grid.at_grid["x_of_shelf_edge"] = np.nan
        self.grid.at_grid["sea_level__elevation"] = 0.0
        self._n_archived_layers = 0

        z0 = grid.at_node["bedrock_surface__elevation"]

        self.grid.event_layers.add(
            100.0,
            age=self.clock.start,
            water_depth=-z0[self.grid.core_nodes],
            t0=10.0,
            percent_sand=0.5,
            porosity=0.5,
        )

        try:
            self._components["sea_level"].time = self.clock.time
        except KeyError:
            pass

        self.timer: dict[str, float] = defaultdict(float)

    @staticmethod
    def load_grid(params: dict, bathymetry: Optional[dict] = None) -> SequenceModelGrid:
        """Load a `SequenceModelGrid`.

        Parameters
        ----------
        params : dict
            Parameters used to create the grid.
        bathymetry : dict, optional
            Parameters used to set the initial bathymetry of the grid.
        """
        grid = SequenceModelGrid.from_dict(params)

        if bathymetry is not None:
            BathymetryReader(grid, **bathymetry).run_one_step()

            z = grid.at_node["topographic__elevation"]
            grid.add_field("bedrock_surface__elevation", z - 100.0, at="node")

        return grid

    @staticmethod
    def load_processes(
        grid: SequenceModelGrid, processes: Iterable[str], context: dict[str, dict]
    ) -> dict:
        """Instantiate processes.

        Parameters
        ----------
        grid : SequenceModelGrid
            A Sequence grid.
        processes : Iterable[str], optional
            List of the names of the processes to create.
        context : dict
            A context from which to draw parameters to create the
            processes.
        """
        if "fluvial" not in processes:
            processes = list(processes) + ["fluvial"]
        if "shoreline" not in processes:
            processes = list(processes) + ["shoreline"]
        params: Dict[str, dict] = defaultdict(dict)
        params.update(
            {process: context.get(process, {}).copy() for process in processes}
        )

        _match_values(
            params["fluvial"],
            params["submarine_diffusion"],
            ["sediment_load", "plain_slope"],
        )
        _match_values(params["fluvial"], context["sediments"].copy(), ["hemipelagic"])
        _match_values(params["shoreline"], params["submarine_diffusion"], ["alpha"])

        for name, values in params.items():
            logger.debug(
                os.linesep.join(
                    [
                        f"reading configuration: {name}",
                        tomlkit.dumps({"sequence": {name: values}}),
                    ]
                )
            )

        process_class = {
            "subsidence": SubsidenceTimeSeries,
            "compaction": Compact,
            "submarine_diffusion": SubmarineDiffuser,
            "fluvial": Fluvial,
            "flexure": SedimentFlexure,
            "shoreline": ShorelineFinder,
        }
        try:
            params["sea_level"]["filepath"]
        except KeyError:
            process_class["sea_level"] = SinusoidalSeaLevel
        else:
            process_class["sea_level"] = SeaLevelTimeSeries
        processes = OrderedDict(
            [(name, process_class[name](grid, **params[name])) for name in processes]
        )

        return processes

    @property
    def grid(self) -> SequenceModelGrid:
        """Return the model's grid."""
        return self._grid

    @property
    def clock(self) -> TimeStepper:
        """Return the model's clock."""
        return self._clock

    @property
    def components(self) -> tuple:
        """Return the name of enabled components."""
        return tuple(self._components)

    def set_params(self, params: dict[str, dict]) -> None:
        """Update the parameters for the model's processes.

        Parameters
        ----------
        params : dict
            The new parameters for the processes.
        """
        for component, values in params.items():
            c = self._components[component]
            for param, value in values.items():
                setattr(c, param, value)

    def run_one_step(self, dt: Optional[float] = None) -> None:
        """Run each component for one time step."""
        dt = dt or self.clock.step
        self.clock.dt = dt
        self.clock.advance()

        self.advance_components(dt)

    def run(self) -> None:
        """Run the model until complete."""
        try:
            while 1:
                self.run_one_step()
        except StopIteration:
            pass

    def advance_components(self, dt: float) -> None:
        """Update each of the components by a time step.

        Parameters
        ----------
        dt : float
            The time step to advance the components.
        """
        self.grid.at_node["sediment_deposit__thickness"].fill(0.0)

        for name, component in self._components.items():
            time_before = time.time()
            component.run_one_step(dt)
            self.timer[name] += time.time() - time_before

        self._update_fields()

        self.grid.event_layers.add(
            self.grid.at_node["sediment_deposit__thickness"][self.grid.node_at_cell],
            **self.layer_properties(),
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
            "age": self.clock.time,
            "water_depth": water_depth[self.grid.node_at_cell],
            "t0": dz[self.grid.node_at_cell].clip(0.0),
            "porosity": 0.5,
        }

        if "compaction" in self._components:
            properties["porosity"] = self._components["compaction"].porosity_max

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

    def _update_fields(self) -> None:
        """Update fields that depend on other fields."""
        if "sediment__total_of_loading" in self.grid.at_node:
            new_load = SedimentFlexure._calc_loading(
                self.grid.get_profile("sediment_deposit__thickness"),
                self.grid.get_profile("topographic__elevation")
                - self.grid.at_grid["sea_level__elevation"],
                0.5,
                SedimentFlexure._calc_density(
                    self.grid.get_profile("delta_sediment_sand__volume_fraction"),
                    2650.0,
                    2720.0,
                ),
                1030.0,
            )
            self.grid.get_profile("sediment__total_of_loading")[:] += new_load

        if "bedrock_surface__increment_of_elevation" in self.grid.at_node:
            self.grid.at_node["bedrock_surface__elevation"] += self.grid.at_node[
                "bedrock_surface__increment_of_elevation"
            ]
            self.grid.at_node["bedrock_surface__increment_of_elevation"][:] = 0.0

        self.grid.at_node["topographic__elevation"][self.grid.node_at_cell] = (
            self.grid.at_node["bedrock_surface__elevation"][self.grid.node_at_cell]
            + self.grid.event_layers.thickness
        )


def _match_values(d1: dict, d2: dict, keys: Iterable[Hashable]) -> None:
    """Match values between two dictionaries.

    Parameters
    ----------
    d1 : dict
        The first dictionary.
    d2 : dict
        The second dictionary.
    keys : iterable
        The keys to match between dictionaries.

    Examples
    --------
    >>> a, b = {"foo": 0, "bar": 1}, {"baz": 2}
    >>> _match_values(a, b, ["bar"])
    >>> sorted(b.items())
    [('bar', 1), ('baz', 2)]

    >>> a, b = {"foo": 0, "bar": 1}, {"baz": 2}
    >>> _match_values(a, b, ["foo", "baz"])
    >>> sorted(a.items())
    [('bar', 1), ('baz', 2), ('foo', 0)]
    >>> sorted(b.items())
    [('baz', 2), ('foo', 0)]

    >>> a, b = {"bar": 1}, {"bar": 2}
    >>> _match_values(a, b, ["bar"])
    >>> sorted(a.items())
    [('bar', 1)]
    >>> sorted(b.items())
    [('bar', 2)]

    >>> a, b = {"bar": 1}, {"bar": 2}
    >>> _match_values(a, b, ["foo"])
    >>> sorted(a.items())
    [('bar', 1)]
    >>> sorted(b.items())
    [('bar', 2)]

    """
    for key in keys:
        try:
            d1.setdefault(key, d2[key])
        except KeyError:
            pass
        try:
            d2.setdefault(key, d1[key])
        except KeyError:
            pass

    mismatch = []
    for key in keys:
        try:
            if d1[key] != d2[key]:
                mismatch.append(repr(key))
        except KeyError:
            pass
    if mismatch:
        warnings.warn(
            f"both dictionaries contain the key {', '.join(mismatch)} but their values do not match"
        )
