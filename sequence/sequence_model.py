#! /usr/bin/env python
from collections import OrderedDict

import numpy as np
from compaction.landlab import Compact
from landlab import RasterModelGrid
from landlab.bmi.bmi_bridge import TimeStepper

from .bathymetry import BathymetryReader
from .fluvial import Fluvial

# from .raster_model import RasterModel
from .input_reader import load_config
from .output_writer import OutputWriter
from .sea_level import SeaLevelTimeSeries, SinusoidalSeaLevel
from .sediment_flexure import SedimentFlexure
from .shoreline import ShorelineFinder
from .submarine import SubmarineDiffuser
from .subsidence import SubsidenceTimeSeries


class SequenceModel:

    DEFAULT_PARAMS = {
        "grid": {
            "shape": [3, 100],
            "xy_spacing": 1000.0,
            "xy_of_lower_left": [0.0, 0.0],
            "bc": {"top": "closed", "bottom": "closed"},
        },
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
        grid=None,
        clock=None,
        output=None,
        submarine_diffusion=None,
        sea_level=None,
        subsidence=None,
        flexure=None,
        sediments=None,
        bathymetry=None,
        compaction=None,
    ):
        config = {
            "grid": grid,
            "clock": clock,
            "output": output,
            "submarine_diffusion": submarine_diffusion,
            "sea_level": sea_level,
            "subsidence": subsidence,
            "flexure": flexure,
            "sediments": sediments,
            "bathymetry": bathymetry,
            "compaction": compaction,
        }
        missing_kwds = [kwd for kwd, value in config.items() if value is None]
        if missing_kwds:
            raise ValueError(
                "missing required config parameters for SequenceModel ({})".format(
                    ", ".join(missing_kwds)
                )
            )

        self._clock = TimeStepper(**clock)
        self._grid = RasterModelGrid.from_dict(grid)

        self._components = OrderedDict()
        if output:
            self._output = OutputWriter(self._grid, **output)
            self._components["output"] = self._output

        BathymetryReader(self.grid, **bathymetry).run_one_step()

        z = self.grid.at_node["topographic__elevation"]
        z0 = self.grid.add_empty("bedrock_surface__elevation", at="node")
        z0[:] = z - 100.0

        self.grid.at_grid["x_of_shore"] = np.nan
        self.grid.at_grid["x_of_shelf_edge"] = np.nan

        self.grid.event_layers.add(
            100.0,
            age=self.clock.start,
            water_depth=-z0[self.grid.core_nodes],
            t0=10.0,
            percent_sand=0.5,
            porosity=0.5,
        )

        if "filepath" in sea_level:
            self._sea_level = SeaLevelTimeSeries(
                self.grid, sea_level.pop("filepath"), start=clock["start"], **sea_level
            )
        else:
            self._sea_level = SinusoidalSeaLevel(
                self.grid, start=clock["start"], **sea_level
            )

        self._subsidence = SubsidenceTimeSeries(self.grid, **subsidence)

        self._submarine_diffusion = SubmarineDiffuser(self.grid, **submarine_diffusion)
        self._fluvial = Fluvial(
            self.grid,
            0.5,
            start=0,
            sediment_load=submarine_diffusion["sediment_load"],
            plain_slope=submarine_diffusion["plain_slope"],
            hemipelagic=sediments["hemipelagic"],
        )
        self._flexure = SedimentFlexure(self.grid, **flexure)
        self._shoreline = ShorelineFinder(self.grid, alpha=submarine_diffusion["alpha"])
        self._compaction = Compact(self.grid, **compaction)

        self._components.update(
            sea_level=self._sea_level,
            subsidence=self._subsidence,
            compaction=self._compaction,
            submarine_diffusion=self._submarine_diffusion,
            fluvial=self._fluvial,
            flexure=self._flexure,
            shoreline=self._shoreline,
        )

    @property
    def grid(self):
        return self._grid

    @property
    def clock(self):
        return self._clock

    @classmethod
    def from_path(cls, filepath, fmt=None):
        return cls(**load_config(filepath, fmt=fmt))

    def set_params(self, params):
        for component, values in params.items():
            c = self._components[component]
            for param, value in values.items():
                setattr(c, param, value)

    def run_one_step(self, dt=None, output=None):
        """Run each component for one time step."""
        dt = dt or self.clock.step
        self.clock.dt = dt
        self.clock.advance()

        self.advance_components(dt)

    def run(self, output=None):
        """Run the model until complete."""
        try:
            while 1:
                self.run_one_step()
        except StopIteration:
            pass

    def advance_components(self, dt):
        for component in self._components.values():
            component.run_one_step(dt)

        dz = self.grid.at_node["sediment_deposit__thickness"]
        percent_sand = self.grid.at_node["delta_sediment_sand__volume_fraction"]
        water_depth = (
            self.grid.at_grid["sea_level__elevation"]
            - self.grid.at_node["topographic__elevation"]
        )

        self.grid.event_layers.add(
            dz[self.grid.node_at_cell],
            age=self.clock.time,
            water_depth=water_depth[self.grid.node_at_cell],
            t0=dz[self.grid.node_at_cell].clip(0.0),
            percent_sand=percent_sand[self.grid.node_at_cell],
            porosity=self._compaction.porosity_max,
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
                age=np.max,
                percent_sand=np.mean,
                porosity=np.mean,
                t0=np.sum,
                water_depth=np.mean,
            )
            self._n_archived_layers += 1
