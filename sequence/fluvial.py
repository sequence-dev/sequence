"""Calculate the fraction of sand on the delta plain.

This module contains *Landlab* components that add a sand fraction to a
`SequenceModelGrid`.
"""
import numpy as np
from landlab import Component

from ._grid import SequenceModelGrid
from .shoreline import find_shoreline


class Fluvial(Component):
    """*Landlab* component that calculates delta-plain sand fraction."""

    _name = "Sand Percent Calculator"

    _time_units = "y"

    _info = {
        "topographic__elevation": {
            "dtype": "float",
            "intent": "in",
            "optional": False,
            "units": "m",
            "mapping": "node",
            "doc": "land and ocean bottom elevation, positive up",
        },
        "sea_level__elevation": {
            "dtype": "float",
            "intent": "in",
            "optional": False,
            "units": "m",
            "mapping": "grid",
            "doc": "Position of sea level",
        },
        "sediment_deposit__thickness": {
            "dtype": "float",
            "intent": "inout",
            "optional": False,
            "units": "m",
            "mapping": "node",
            "doc": "Thickness of deposition or erosion",
        },
        "delta_sediment_sand__volume_fraction": {
            "dtype": "float",
            "intent": "out",
            "optional": False,
            "units": "-",
            "mapping": "node",
            "doc": "delta sand fraction",
        },
    }

    def __init__(
        self,
        grid: SequenceModelGrid,
        sand_frac: float = 0.5,
        wave_base: float = 60.0,
        sediment_load: float = 3.0,
        sand_density: float = 2650.0,
        plain_slope: float = 0.0008,
        hemipelagic: float = 0.0,
        sea_level: float = 0.0,
    ):
        """Generate percent sand/mud for fluvial section.

        Add hemipelagic mud to the seaward end of section.

        Parameters
        ----------
        grid: SequenceModelGrid
            A landlab grid.
        sand_frac: str, optional
            Fraction of sand on the delta.
        wave_base: float, optional
            Wave base (m).
        sediment_load : float, optional
            Sediment load.
        sand_density : float, optional
            The grain density of sand [kg / m^3]
        plain_slope : float, optional
            The gradient of the flood plain.
        hemipelagic : float, optional
            Hemipelagic sedimentation.
        sea_level: float, optional
            The current sea level (m).
        """
        super().__init__(grid)

        # fixed parameters
        self.sand_grain = 0.001  # grain size = 1 mm
        self.alpha = (
            10.0  # ratio of channel depth to channel belt thickness  */ was 10.
        )
        self.beta = 0.1  # beta*h is flow depth of flood, beta = .1 to .5   */
        # lambdap = .30
        self.flood_period = 10.0  # recurrence time of floods ~1-10 y  */
        self.basin_width = 10000.0  # Basin width or river spacing of 20 km */ was 5000.
        self.basin_length = (
            100000.0  # length for downstream increase in diffusion */ was 500000.
        )
        self.hemi_taper = 100000.0  # taper out hemipelagic deposition over 100 km

        self.sand_frac = sand_frac
        self.sediment_load = sediment_load
        self.sand_density = sand_density
        self.plain_slope = plain_slope
        self.wave_base = float(wave_base)
        self.hemi = float(hemipelagic)

        if "delta_sediment_sand__volume_fraction" not in grid.at_node:
            grid.add_zeros("delta_sediment_sand__volume_fraction", at="node")
        if "bedrock_surface__increment_of_elevation" not in grid.at_node:
            grid.add_zeros("bedrock_surface__increment_of_elevation", at="node")

    def run_one_step(self, dt: float) -> None:
        """Update the component one time step.

        Parameters
        ----------
        dt : float
            The time step to update the component by.
        """
        # Upstream boundary conditions  */
        mud_vol = self.sediment_load * (1.0 - self.sand_frac) / self.sand_frac
        sand_vol = self.sediment_load
        qs = (
            10.0
            * np.sqrt(9.8 * (self.sand_density / 1000.0 - 1.0))
            * (self.sand_grain**1)
        )
        # m^2/s  units */
        # print (self.sand_frac,mud_vol,sand_vol,qs)

        # upstream diffusivity is set by equilibrium slope */
        diffusion = self.sediment_load / self.plain_slope
        qw = diffusion / 0.61
        conc_mud = np.zeros(self.grid.shape[1])
        conc_mud[0] = mud_vol / qw

        # channel_width = sand_vol * self.basin_width / qs / 31536000.
        channel_width = sand_vol / qs

        x = self.grid.x_of_node.reshape(self.grid.shape)[1]
        elevation = self.grid.get_profile("topographic__elevation")

        shore = find_shoreline(
            x, elevation, sea_level=self.grid.at_grid["sea_level__elevation"]
        )

        land = x < shore
        water = x >= shore
        # land = self.grid.x_of_node[self.grid.node_at_cell] < shore
        # slope = np.gradient(z[1, land]) / self.grid.dx
        slope = np.gradient(elevation) / self.grid.dx
        # slp = np.zeros(1)
        # slp[0] = self.plain_slope
        # slope = np.concatenate((slp,slop))

        # channel_depth[land] = (
        #     (self.sand_density - 1000.) / 1000. * self.sand_grain / slope[land]
        # )

        # channel_depth = np.zeros(self.grid.number_of_cells)
        channel_depth = np.zeros_like(elevation)  # use upsteam slope
        # channel_depth[0] = (
        #    (self.sand_density - 1000.) / 1000. * self.sand_grain / self.plain_slope
        channel_depth[land] = (
            (self.sand_density - 1000.0) / 1000.0 * self.sand_grain / slope[land]
        )

        # Type of channelization */
        if channel_width / channel_depth[0] > 75.0:
            epsilon = 0.4  # braided 0.3-0.5  */
        else:
            epsilon = 0.125  # meandering  0.1-0.15  */
        # width_cb = channel_width/epsilon

        # Original: r_cb = (model.new_height[i]-model.height[i]+model.d_sl);
        r_cb = self.grid.get_profile("sediment_deposit__thickness") * epsilon
        dz = self.grid.get_profile("bedrock_surface__increment_of_elevation").copy()
        # original: r_b = model.thickness[i];
        r_b = self.grid.get_profile("sediment_deposit__thickness").copy()
        # r_fp = np.zeros(self.grid.shape[1])
        r_fp = np.zeros_like(elevation)
        percent_sand = self.grid.get_profile("delta_sediment_sand__volume_fraction")
        percent_sand.fill(0.0)

        for i in np.where(land)[0]:
            if channel_width / channel_depth[i] > 75.0:
                epsilon = 0.4
                # braided 0.3-0.5  */
            else:
                epsilon = 0.125
                # meandering  0.1-0.15  */
            width_cb = channel_width / epsilon

            # all rates  per timestep */
            # channelbelt deposition  */
            if r_cb[i] < 0.0:
                r_cb[i] = 0.0

            # floodplain deposition  */
            r_fp[i] = (
                self.beta
                * channel_depth[i]
                / self.flood_period
                * conc_mud[i]
                # * dt
                # * 1000.
            )
            if r_fp[i] > r_cb[i]:
                r_fp[i] = r_cb[i]

            # Find avulsion rate and sand density   */
            if r_b[i] > 0.0:

                bigN = self.alpha * (r_cb[i] - r_fp[i]) / r_b[i]
                if bigN > 1.0:
                    r_cb[i] *= bigN
                # rate is bigger because of avulsions */

                if r_cb[i] <= 0.0:
                    r_cb[i] = 0.0
                    percent_sand[i] = 1.0

                else:
                    bigN = self.alpha * (r_cb[i] - r_fp[i]) / r_b[i]
                    percent_sand[i] = 1.0 - np.exp(
                        -1.0 * width_cb / self.basin_width * bigN
                    )
                if percent_sand[i] > 1.0:
                    percent_sand[i] = 1.0
                if percent_sand[i] < 0.0:
                    percent_sand[i] = 0.0

            else:
                percent_sand[i] = 0.0
                # NULL;*/

            # adjust parameters for next downstream point */
            if dz[i] > 0.0:
                sand_vol -= (
                    percent_sand[i] * self.grid.dx * (dz[i] + dz[i + 1]) / 2 / dt
                )
                mud_vol -= (
                    (1.0 - percent_sand[i])
                    * self.grid.dx
                    * (dz[i] + dz[i + 1])
                    / 2
                    / dt
                )
            diffusion = (
                self.sediment_load / self.plain_slope  # slope[i]
            )  # question is i correct? Yes - add increasing water downstream
            # * (1. + i * self.grid.dx / self.basin_length)

            qw = diffusion / 0.61
            conc_mud[i + 1] = mud_vol / qw
            channel_depth[i] = (
                (self.sand_density - 1000.0) / 1000.0 * self.sand_grain / slope[i]
            )

        # Add mud layer increasing from 0 at wave_base to hemipelagic at 2*wave_base

        water_depth = (
            self.grid.at_grid["sea_level__elevation"]
            - self.grid.at_node["topographic__elevation"]
        )
        add_mud = np.zeros(self.grid.shape[1])
        taper = 1

        for i in np.where(water)[0]:
            if water_depth[i] < self.wave_base:
                add_mud[i] = 0.0
            if water_depth[i] > self.wave_base and water_depth[i] < 2 * self.wave_base:
                add_mud[i] = (
                    (water_depth[i] - self.wave_base)
                    / (self.wave_base)
                    * (self.hemi * dt)
                )
                taper = i
            elif water_depth[i] >= 2 * self.wave_base:
                add_mud[i] = (self.hemi * dt) * (
                    1 - (x[i] - x[taper]) / self.hemi_taper
                )
                if add_mud[i] < 0.0:
                    add_mud[i] = 0.0

        sediment_thickness = self.grid.get_profile("sediment_deposit__thickness")
        sediment_thickness[water] += add_mud[water]

        np.divide(
            sediment_thickness[water] - add_mud[water],
            sediment_thickness[water],
            where=sediment_thickness[water] > 0.0,
            out=percent_sand[water],
        )
        np.clip(percent_sand[water], 0.0, 1.0, out=percent_sand[water])
