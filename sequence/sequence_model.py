#! /usr/bin/env python
import numpy as np
from .bathymetry import BathymetryReader
from .fluvial import Fluvial
from .raster_model import RasterModel
from .sea_level import SinusoidalSeaLevel
from .sediment_flexure import SedimentFlexure
from .submarine import SubmarineDiffuser
from .subsidence import SubsidenceTimeSeries


class SequenceModel(RasterModel):

    DEFAULT_PARAMS = {
        "grid": {
            "shape": [3, 100],
            "spacing": 100.,
            "origin": 0.,
            "bc": {"top": "closed", "bottom": "closed"},
        },
        "clock": {"start": -20000., "stop": 0., "step": 100.},
        "submarine_diffusion": {
            "plain_slope": 0.0008,
            "wave_base": 60.,
            "shoreface_height": 15.,
            "alpha": .0005,
            "shelf_slope": .001,
            "sediment_load": 3.,
        },
        "sea_level": {"amplitude": 10., "wave_length": 1000., "phase": 0., "linear": 0.},
        "subsidence": {"filepath": "subsidence.csv"},
        "flexure": {"method": "airy", "rho_mantle": 3300.},
        "sediments": {
            "layers": 2,
            "sand": 1.0,
            "mud": 0.006,
            "sand_density": 2650.,
            "mud_density": 2720.,
            "sand_frac": 0.5,
        },
        "bathymetry": {"filepath": "bathymetry.csv", "kind": "linear"},
    }

    LONG_NAME = {"z": "topographic__elevation", "z0": "bedrock_surface__elevation"}

    def __init__(
        self,
        grid=None,
        clock=None,
        submarine_diffusion=None,
        sea_level=None,
        subsidence=None,
        flexure=None,
        sediments=None,
        bathymetry=None,
    ):
        RasterModel.__init__(self, grid=grid, clock=clock)

        #z0 = self.grid.add_empty("bedrock_surface__elevation", at="node")
        #z = self.grid.add_empty("topographic__elevation", at="node")
        #percent_sand = self.grid.add_empty("sand_frac", at="node")
        
        #shoreface_height=submarine_diffusion["shoreface_height"]
        #alpha=submarine_diffusion["alpha"]
        #spacing=grid["spacing"]

        #z[:] = -.001 * self.grid.x_of_node + 120.
        #shore = 120./.001
        
        #shore = 30/(.001 * spacing )*1000
        #under_water = z < 0.
        #z[under_water] = z[under_water] - shoreface_height*(
        #    1 - np.exp(-1*alpha*(self.grid.x_of_node[under_water] - shore))
        #)

        
        #z0[:] = z - 100.
        BathymetryReader(self.grid, **bathymetry).run_one_step()

        z0 = self.grid.at_node["bedrock_surface__elevation"]
        z = self.grid.add_empty("topographic__elevation", at="node")
        z[:] = z0
        z0 -= 100.

        self.grid.layers.add(
            100.,
            age=self.clock.start,
            water_depth=-z0[self.grid.core_nodes],
            t0=10.,
            percent_sand=0.5,
        )

        # z = self.grid.add_empty("topographic__elevation", at="node")
        # z[:] = z0 + 100.

        self._sea_level = SinusoidalSeaLevel(
            self.grid, start=clock["start"], **sea_level
        )

        self._subsidence = SubsidenceTimeSeries(self.grid, **subsidence)

        self._submarine_diffusion = SubmarineDiffuser(self.grid, **submarine_diffusion)
        self._fluvial = Fluvial(
            self.grid,
            .5,
            start=0,
            sediment_load=submarine_diffusion["sediment_load"],
            plain_slope=submarine_diffusion["plain_slope"],
        )
        self._flexure = SedimentFlexure(self.grid, **flexure)

        self._components = (
            self._sea_level,
            self._subsidence,
            self._submarine_diffusion,
            self._fluvial,
            self._flexure,
        )

    def advance_components(self, dt):
        for component in self._components:
            component.run_one_step(dt)

        dz = self.grid.at_node["sediment_deposit__thickness"]
        water_depth = (
            self.grid.at_grid["sea_level__elevation"]
            - self.grid.at_node["topographic__elevation"]
        )
        percent_sand = self.grid.at_node["delta_sediment_sand__volume_fraction"]

        self.grid.layers.add(
            dz[self.grid.node_at_cell],
            age=self.clock.time,
            water_depth=water_depth[self.grid.node_at_cell],
            t0=dz[self.grid.node_at_cell].clip(0.),
            percent_sand=percent_sand[self.grid.node_at_cell],
        )
