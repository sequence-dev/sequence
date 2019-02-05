#! /usr/bin/env python
import os

import click
import numpy as np
import yaml

from landlab.core import load_params

from .bathymetry import BathymetryReader
from .fluvial import Fluvial
from .raster_model import RasterModel
from .sea_level import SinusoidalSeaLevel
from .sediment_flexure import SedimentFlexure
from .submarine import SubmarineDiffuser
from .subsidence import SubsidenceTimeSeries
from .shoreline import find_shoreline
from .shoreline import find_shoreline_index

class SequenceModel(RasterModel):

    DEFAULT_PARAMS = {
        "grid": {
            "shape": [3, 100],
            "spacing": 100.0,
            "origin": 0.0,
            "bc": {"top": "closed", "bottom": "closed"},
        },
        "clock": {"start": -20000.0, "stop": 0.0, "step": 100.0},
        "output": None,
        "submarine_diffusion": {
            "plain_slope": 0.0008,
            "wave_base": 60.0,
            "shoreface_height": 15.0,
            "alpha": 0.0005,
            "shelf_slope": 0.001,
            "sediment_load": 3.0,
        },
        "sea_level": {"amplitude": 10.0, "wave_length": 1000.0, "phase": 0.0, "linear": 0.0},
        "subsidence": {"filepath": "subsidence.csv"},
        "flexure": {"method": "flexure", "rho_mantle": 3300.0},
        "sediments": {
            "layers": 2,
            "sand": 1.0,
            "mud": 0.006,
            "sand_density": 2650.0,
            "mud_density": 2720.0,
            "sand_frac": 0.5,
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

        z = self.grid.at_node["topographic__elevation"]
        z0 = self.grid.add_empty("bedrock_surface__elevation", at="node")
        z0[:] = z - 100.0

        self.grid.event_layers.add(
            100.0,
            age=self.clock.start,
            water_depth=-z0[self.grid.core_nodes],
            t0=10.0,
            percent_sand=0.5,
            shoreline = 0.,
            shelfedge = 0.
        )

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
        )
        self._flexure = SedimentFlexure(self.grid, **flexure)

        self._components += (
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
        
        x = self.grid.x_of_node
        dx = x[1]-x[0]
        z = self.grid.at_node["topographic__elevation"].copy()
        shore = find_shoreline(
            self.grid.x_of_node[self.grid.node_at_cell],
            z[self.grid.node_at_cell],
            sea_level=self.grid.at_grid["sea_level__elevation"],
        )
        
        under_water = water_depth > 0.
        slope = np.gradient(under_water) 
        curv = np.gradient(slope) 
        edge = (np.argmax(curv)+find_shoreline_index(x, z, 
                sea_level=self.grid.at_grid["sea_level__elevation"])
               )*dx
        
        self.grid.event_layers.add(
            dz[self.grid.node_at_cell],
            age=self.clock.time,
            water_depth=water_depth[self.grid.node_at_cell],
            t0=dz[self.grid.node_at_cell].clip(0.0),
            percent_sand=percent_sand[self.grid.node_at_cell],
            shoreline = shore,
            shelfedge = edge,
        )


@click.command()
@click.option("--dry-run", is_flag=True, help="do not actually run the model")
@click.option(
    "-v", "--verbose", is_flag=True, help="Also emit status messages to stderr."
)
@click.option(
    "--with-citations", is_flag=True, help="print citations for components used"
)
@click.argument(
    "file", type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True)
)
def main(file, with_citations, verbose, dry_run):
    params = load_params(file)

    if verbose:
        click.secho(yaml.dump(params, default_flow_style=False), err=True)

    model = SequenceModel(**params)

    if with_citations:
        from landlab.core.model_component import registry

        click.secho("👇👇👇These are the citations to use👇👇👇", err=True)
        click.secho(registry.format_citations())
        click.secho("👆👆👆These are the citations to use👆👆👆", err=True)

    if not dry_run:
        try:
            with click.progressbar(
                length=int(model.clock.stop // model.clock.step),
                label=os.path.basename(file),
            ) as bar:
                while 1:
                    model.run_one_step()
                    bar.update(1)
        except StopIteration:
            pass

        click.secho("💥 Finished! 💥", err=True, fg="green")
        if "output" in params:
            click.secho(
                "Output written to {0}".format(params["output"]["filepath"]), fg="green"
            )
    else:
        click.secho("Nothing to do. 😴", fg="green")
