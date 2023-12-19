"""Build a `SequenceModelGrid` model from collection of components."""
import logging
import os
import time
from collections import defaultdict
from collections import OrderedDict
from collections.abc import Hashable
from collections.abc import Iterable
from contextlib import suppress
from typing import Any
from typing import Dict
from typing import Optional

import numpy as np
import tomlkit
from compaction.landlab import Compact
from landlab.bmi.bmi_bridge import TimeStepper
from numpy.typing import ArrayLike

from sequence._grid import SequenceModelGrid
from sequence.bathymetry import BathymetryReader
from sequence.errors import ParameterMismatchError
from sequence.fluvial import Fluvial
from sequence.output_writer import OutputWriter
from sequence.sea_level import SeaLevelTimeSeries
from sequence.sea_level import SinusoidalSeaLevel
from sequence.sediment_flexure import SedimentFlexure
from sequence.sediment_flexure import WaterFlexure
from sequence.shoreline import ShorelineFinder
from sequence.submarine import SubmarineDiffuser
from sequence.subsidence import SubsidenceTimeSeries

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
        "grid": {"shape": (1, 100), "spacing": (1.0, 1000.0)},
        "clock": {"start": 0.0, "stop": 600000.0, "step": 100.0},
        "output": {
            "interval": 10,
            "filepath": "sequence.nc",
            "clobber": True,
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

        self.grid.at_row["x_of_shore"][:] = np.nan
        self.grid.at_row["x_of_shelf_edge"][:] = np.nan
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

        with suppress(KeyError):
            self._components["sea_level"].time = self.clock.time

        if "water__total_of_loading" in self.grid.at_node:
            water_load = WaterFlexure.calc_water_loading(
                self.grid.get_profile("topographic__elevation")
                - self.grid.at_grid["sea_level__elevation"],
                1030.0,
            )
            self.grid.get_profile("water__total_of_loading")[:] = water_load

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

        params_to_match = [
            ("fluvial", "submarine_diffusion", ["sediment_load", "plain_slope"]),
            ("fluvial", "sediments", ["hemipelagic"]),
            ("shoreline", "submarine_diffusion", ["alpha"]),
            ("water_flexure", "flexure", ["isostasytime", "eet"]),
        ]
        for d1, d2, keys in params_to_match:
            try:
                matched_values = _match_values(params[d1], params[d2], keys)
            except ParameterMismatchError as error:
                msg = os.linesep.join(
                    [
                        tomlkit.dumps(
                            {"sequence": {d1: {k: params[d1][k] for k in error.keys}}}
                        ),
                        tomlkit.dumps(
                            {"sequence": {d2: {k: params[d2][k] for k in error.keys}}}
                        ),
                    ]
                )
                logger.warning(os.linesep.join([str(error), msg]))
            else:
                msg = os.linesep.join(
                    [
                        tomlkit.dumps({"sequence": {d1: matched_values}}),
                        tomlkit.dumps({"sequence": {d2: matched_values}}),
                    ]
                )
                if len(matched_values) > 0:
                    logger.debug(
                        os.linesep.join(
                            [
                                "matched value"
                                f"{'s' if len(matched_values) > 1 else ''} between "
                                f"{d1!r} and {d2!r}",
                                msg,
                            ]
                        )
                    )
                params[d1].update(matched_values)
                params[d2].update(matched_values)

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
            "water_flexure": WaterFlexure,
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
        with suppress(StopIteration):
            while 1:
                self.run_one_step()

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

        self.grid.event_layers.add(
            self.grid.at_node["sediment_deposit__thickness"][self.grid.node_at_cell],
            **self.layer_properties(),
        )

        self._update_fields()

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
        old_water_depth = np.clip(
            self.grid.at_grid["sea_level__elevation"]
            - self.grid.get_profile("topographic__elevation"),
            a_min=0.0,
            a_max=None,
        )

        if "sediment__total_of_loading" in self.grid.at_node:
            sediment_load = SedimentFlexure._calc_loading(
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
            self.grid.get_profile("sediment__total_of_loading")[:] += sediment_load

        if "bedrock_surface__increment_of_elevation" in self.grid.at_node:
            self.grid.at_node["bedrock_surface__elevation"] += self.grid.at_node[
                "bedrock_surface__increment_of_elevation"
            ]
            self.grid.at_node["bedrock_surface__increment_of_elevation"][:] = 0.0

        self.grid.at_node["topographic__elevation"][self.grid.node_at_cell] = (
            self.grid.at_node["bedrock_surface__elevation"][self.grid.node_at_cell]
            + self.grid.event_layers.thickness
        )

        new_water_depth = np.clip(
            self.grid.at_grid["sea_level__elevation"]
            - self.grid.get_profile("topographic__elevation"),
            a_min=0.0,
            a_max=None,
        )
        if "water__increment_of_depth" in self.grid.at_node:
            change_in_water_depth = self.grid.get_profile("water__increment_of_depth")
            change_in_water_depth[:] = new_water_depth - old_water_depth


def _match_values(d1: dict, d2: dict, keys: Iterable[Hashable]) -> dict:
    """Match values between two dictionaries.

    Parameters
    ----------
    d1 : dict
        The first dictionary.
    d2 : dict
        The second dictionary.
    keys : iterable
        The keys to match between dictionaries.

    Returns
    -------
    dict
        A key/value pairs that were matched.

    Examples
    --------
    >>> a, b = {"foo": 0, "bar": 1}, {"baz": 2}
    >>> _match_values(a, b, ["bar"])
    {'bar': 1}

    >>> a, b = {"foo": 0, "bar": 1}, {"baz": 2}
    >>> sorted(_match_values(a, b, ["foo", "baz"]).items())
    [('baz', 2), ('foo', 0)]

    >>> a, b = {"bar": 1}, {"bar": 2}
    >>> _match_values(a, b, ["bar"])
    Traceback (most recent call last):
    ...
    sequence.errors.ParameterMismatchError: mismatch in parameter: 'bar'

    >>> a, b = {"bar": 1}, {"bar": 2}
    >>> _match_values(a, b, ["foo"])
    {}
    """
    mismatched_keys = []
    matched = {}
    for key in keys:
        with suppress(KeyError):
            matched[key] = d2[key]
        with suppress(KeyError):
            matched.setdefault(key, d1[key])
            if matched[key] != d1[key]:
                mismatched_keys.append(key)

    if mismatched_keys:
        raise ParameterMismatchError(mismatched_keys)
    return matched
