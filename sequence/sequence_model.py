#! /usr/bin/env python
import warnings
from collections import OrderedDict, defaultdict
from collections.abc import Hashable, Iterable
from typing import Optional

import numpy as np
from compaction.landlab import Compact
from landlab import FieldError
from landlab.bmi.bmi_bridge import TimeStepper

from .bathymetry import BathymetryReader
from .fluvial import Fluvial
from .grid import SequenceModelGrid
from .output_writer import OutputWriter
from .sea_level import SeaLevelTimeSeries, SinusoidalSeaLevel
from .sediment_flexure import SedimentFlexure
from .shoreline import ShorelineFinder
from .submarine import SubmarineDiffuser
from .subsidence import SubsidenceTimeSeries


class SequenceModel:

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
        grid,
        clock: Optional[dict] = None,
        processes: Optional[dict] = None,
        output: Optional[dict] = None,
    ):
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

    @staticmethod
    def load_grid(params: dict, bathymetry: Optional[dict] = None):
        grid = SequenceModelGrid.from_dict(params)

        if bathymetry is not None:
            BathymetryReader(grid, **bathymetry).run_one_step()

            z = grid.at_node["topographic__elevation"]
            grid.add_field("bedrock_surface__elevation", z - 100.0, at="node")

        return grid

    @staticmethod
    def load_processes(
        grid, processes: Iterable[str], context: dict[str, dict]
    ) -> dict:
        """Instantiate processes.

        Parameters
        ----------
        grid : :class:`~sequence.grid.SequenceModelGrid`
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
        params = defaultdict(dict)
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
    def grid(self):
        """Return the model's grid."""
        return self._grid

    @property
    def clock(self):
        """Return the model's clock."""
        return self._clock

    @property
    def components(self):
        """Return the name of enabled components."""
        return tuple(self._components)

    def set_params(self, params: dict[str, dict]):
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

    def run_one_step(self, dt: Optional[float] = None):
        """Run each component for one time step."""
        dt = dt or self.clock.step
        self.clock.dt = dt
        self.clock.advance()

        self.advance_components(dt)

    def run(self):
        """Run the model until complete."""
        try:
            while 1:
                self.run_one_step()
        except StopIteration:
            pass

    def advance_components(self, dt: float):
        for component in self._components.values():
            component.run_one_step(dt)

        dz = self.grid.at_node["sediment_deposit__thickness"]
        # percent_sand = self.grid.at_node["delta_sediment_sand__volume_fraction"]
        water_depth = (
            self.grid.at_grid["sea_level__elevation"]
            - self.grid.at_node["topographic__elevation"]
        )

        layer_properties = dict(
            age=self.clock.time,
            water_depth=water_depth[self.grid.node_at_cell],
            t0=dz[self.grid.node_at_cell].clip(0.0),
            # percent_sand=percent_sand[self.grid.node_at_cell],
        )
        if "compaction" in self._components:
            layer_properties["porosity"] = self._components["compaction"].porosity_max
        try:
            percent_sand = self.grid.at_node["delta_sediment_sand__volume_fraction"]
        except FieldError:
            pass
        else:
            layer_properties["percent_sand"] = percent_sand[self.grid.node_at_cell]

        self.grid.event_layers.add(dz[self.grid.node_at_cell], **layer_properties)

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
                age=np.max,
                percent_sand=np.mean,
                porosity=np.mean,
                t0=np.sum,
                water_depth=np.mean,
            )
            self._n_archived_layers += 1


def _match_values(d1: dict, d2: dict, keys: Iterable[Hashable]):
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
