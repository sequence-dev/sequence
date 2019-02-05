#! /usr/bin/env python
import numpy as np

from landlab import Component

from .shoreline import find_shoreline


class Fluvial(Component):

    _name = "Sand Percent Calculator"

    _time_units = "y"

    _input_var_names = ()

    _output_var_names = ("delta_sediment_sand__volume_fraction",)

    _var_units = {"delta_sediment_sand__volume_fraction": "%"}

    _var_mapping = {"delta_sediment_sand__volume_fraction": "node"}

    _var_doc = {"delta_sediment_sand__volume_fraction": "delta sand fraction"}

    def __init__(
        self,
        grid,
        sand_frac,
        start=0.0,
        sediment_load=3.0,
        sand_density=2650.0,
        plain_slope=0.0008,
        **kwds
    ):
        """Generate percent sand/mud for fluvial section.

        Parameters
        ----------
        grid: ModelGrid
            A landlab grid.
        sand_frac: str
            Name of csv-formatted sea-level file.
        """
        super(Fluvial, self).__init__(grid, **kwds)

        # fixed parameters
        self.sand_grain = 0.001  # grain size = 1 mm
        self.alpha = 10.0  # ratio of channel depth to channel belt thickness  */ was 10.
        self.beta = 0.1  # beta*h is flow depth of flood, beta = .1 to .5   */
        # lambdap = .30
        self.flood_period = 10.0  # recurrence time of floods ~1-10 y  */
        self.basin_width = 10000.0  # Basin width or river spacing of 20 km */ was 5000.
        self.basin_length = 100000.0  # length for downstream increase in diffusion */ was 500000.

        self.sand_frac = sand_frac
        self.sediment_load = sediment_load
        self.sand_density = sand_density
        self.plain_slope = plain_slope

        grid.add_zeros("delta_sediment_sand__volume_fraction", at="node")

    def run_one_step(self, dt):
        # Upstream boundary conditions  */
        mud_vol = self.sediment_load * (1. - self.sand_frac)/self.sand_frac
        sand_vol = self.sediment_load
        qs = (
            10.
            * np.sqrt(9.8 * (self.sand_density / 1000. - 1.))
            * (self.sand_grain ** 1)
        )
        # m^2/s  units */
        #print (self.sand_frac,mud_vol,sand_vol,qs)

        # upstream diffusivity is set by equilibrium slope */
        diffusion = self.sediment_load / self.plain_slope
        qw = diffusion / 0.61
        conc_mud = np.zeros(self.grid.shape[1])
        conc_mud[0] = mud_vol / qw

        #channel_width = sand_vol * self.basin_width / qs / 31536000.
        channel_width = sand_vol / qs 
        
        x = self.grid.x_of_node.reshape(self.grid.shape)[1]
        z = self.grid.at_node["topographic__elevation"].reshape(self.grid.shape)[1]

        shore = find_shoreline(
            x, z, sea_level=self.grid.at_grid["sea_level__elevation"]
        )

        land = x < shore
        # land = self.grid.x_of_node[self.grid.node_at_cell] < shore
        # slope = np.gradient(z[1, land]) / self.grid.dx
        slope = np.gradient(z) / self.grid.dx
        #slp = np.zeros(1)
        #slp[0] = self.plain_slope
        #slope = np.concatenate((slp,slop))

        # channel_depth[land] = (
        #     (self.sand_density - 1000.) / 1000. * self.sand_grain / slope[land]
        # )

        # channel_depth = np.zeros(self.grid.number_of_cells)
        channel_depth = np.zeros_like(z) # use upsteam slope
        #channel_depth[0] = (
        #    (self.sand_density - 1000.) / 1000. * self.sand_grain / self.plain_slope
        channel_depth[land] = (
            (self.sand_density - 1000.0) / 1000.0 * self.sand_grain / slope[land]
        )

        # Type of channelization */
        if channel_width / channel_depth[0] > 75.:
             epsilon = 0.4 # braided 0.3-0.5  */
        else:
             epsilon = 0.125 # meandering  0.1-0.15  */
        # width_cb = channel_width/epsilon

        # Original: r_cb = (model.new_height[i]-model.height[i]+model.d_sl);
        r_cb = self.grid.at_node["sediment_deposit__thickness"].reshape(
            self.grid.shape 
        )[1].copy() * epsilon
        dz = self.grid.at_node["bedrock_surface__elevation_increment"].reshape(
            self.grid.shape
        )[1].copy()
        # original: r_b = model.thickness[i];
        r_b = self.grid.at_node["sediment_deposit__thickness"].reshape(
            self.grid.shape
        )[1].copy()
        # r_fp = np.zeros(self.grid.shape[1])
        r_fp = np.zeros_like(z)
        percent_sand = self.grid.at_node[
            "delta_sediment_sand__volume_fraction"
        ].reshape(self.grid.shape)[1]
        percent_sand.fill(0.)

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
                        - 1.0 * width_cb / self.basin_width * bigN
                    )
            else:
                percent_sand[i] = 0.
                # NULL;*/

            # adjust parameters for next downstream point */
            if dz[i] > 0.0:
                sand_vol -= (
                    percent_sand[i] * self.grid.dx * (dz[i] + dz[i + 1]) / 2 / dt
                )
                mud_vol -= (
                    (1. - percent_sand[i]) * self.grid.dx * (dz[i] + dz[i + 1]) / 2 / dt
                )
            diffusion = (
                self.sediment_load
                / self.plain_slope   # slope[i]
            )  # question is i correct? Yes - add increasing water downstream
            #* (1. + i * self.grid.dx / self.basin_length) 
           
            qw = diffusion / 0.61
            conc_mud[i + 1] = mud_vol / qw
            channel_depth[i] = (self.sand_density - 1000.)/1000. * self.sand_grain / slope[i]
