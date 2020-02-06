#! /usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from .bathymetry import BathymetryReader
from .fluvial import Fluvial
from .raster_model import RasterModel
from .sea_level import SeaLevelTimeSeries, SinusoidalSeaLevel
from .sediment_flexure import SedimentFlexure
from .shoreline import ShorelineFinder
from .submarine import SubmarineDiffuser
from .subsidence import SubsidenceTimeSeries


class SequenceModel(RasterModel):

    DEFAULT_PARAMS = {
        "grid": {
            "shape": [3, 100],
            "xy_spacing": 100.0,
            "xy_of_lower_left": [0.0, 0.0],
            "bc": {"top": "closed", "bottom": "closed"},
        },
        "clock": {"start": 0.0, "stop": 20000.0, "step": 100.0},
        "output": {
            "interval": 10,
            "filepath": "sequence.nc",
            "clobber": True,
            "rows": [1],
            "fields": ["sediment_deposit__thickness"],
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
            "wave_length": 1000.0,
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
    ):
        RasterModel.__init__(self, grid=grid, clock=clock, output=output)

        alpha = submarine_diffusion["alpha"]

        BathymetryReader(self.grid, **bathymetry).run_one_step()

        z = self.grid.at_node["topographic__elevation"]
        z0 = self.grid.add_empty("bedrock_surface__elevation", at="node")
        z0[:] = z - 100.0

        self.grid.at_grid["x_of_shore"] = np.nan
        self.grid.at_grid["x_of_shelf_edge"] = np.nan
        self._alpha = alpha

        self.grid.event_layers.add(
            100.0,
            age=self.clock.start,
            water_depth=-z0[self.grid.core_nodes],
            t0=10.0,
            percent_sand=0.5,
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

        self._components += (
            self._sea_level,
            self._subsidence,
            self._submarine_diffusion,
            self._fluvial,
            self._flexure,
            self._shoreline,
        )

    def advance_components(self, dt):
        for component in self._components:
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
        )
