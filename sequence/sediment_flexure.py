import numpy as np
from landlab.components.flexure import Flexure1D


class SedimentFlexure(Flexure1D):

    _name = "Sediment-loading flexure"

    _input_var_names = ("sediment_deposit__thickness", "bedrock_surface__elevation")

    _output_var_names = (
        "bedrock_surface__increment_of_elevation",
        "bedrock_surface__elevation",
    )

    _var_units = {
        "sediment_deposit__thickness": "m",
        "bedrock_surface__increment_of_elevation": "m",
        "bedrock_surface__elevation": "m",
    }

    _var_mapping = {
        "sediment_deposit__thickness": "node",
        "bedrock_surface__increment_of_elevation": "node",
        "bedrock_surface__elevation": "node",
    }

    _var_doc = {
        "sediment_deposit__thickness": "Thickness of deposited or eroded sediment",
        "bedrock_surface__increment_of_elevation": "Amount of subsidence due to sediment loading",
        "bedrock_surface__elevation": "New bedrock elevation following subsidence",
    }

    def __init__(
        self,
        grid,
        sand_density=2650,
        mud_density=2720.0,
        isostasytime=7000.0,
        **kwds,
        # **sediments,
    ):
        self._rho_sand = sand_density * (1 - 0.4) + 1030.0 * 0.4  # porosity = 40%
        self._rho_mud = mud_density * (1 - 0.65) + 1030.0 * 0.65  # porosity = 65%
        self._isostasytime = isostasytime
        self._dt = 100.0  # default timestep = 100 y

        Flexure1D.__init__(self, grid, **kwds)

        self.grid.add_zeros("lithosphere__increment_of_overlying_pressure", at="node")
        self.grid.add_zeros("lithosphere_surface__increment_of_elevation", at="node")
        self.subs_pool = self.grid.add_zeros("node", "subsidence_pool")

    @property
    def sand_density(self):
        return self._rho_sand

    @property
    def mud_density(self):
        return self._rho_mud

    def update(self):

        if self._isostasytime > 0.0:
            isostasyfrac = 1 - np.exp(-1.0 * self._dt / self._isostasytime)
        else:
            isostasyfrac = 1.0

        self.grid.at_node["lithosphere_surface__increment_of_elevation"][:] = 0.0

        # calculate density based on sand_frac
        percent_sand = self.grid.at_node[
            "delta_sediment_sand__volume_fraction"
        ].reshape(self.grid.shape)[1]
        rho_sediment = (
            percent_sand * self._rho_sand + (1 - percent_sand) * self._rho_mud
        )

        # load underwater displaces water
        z = self.grid.at_node["topographic__elevation"].reshape(self.grid.shape)[1]
        sea_level = self.grid.at_grid["sea_level__elevation"]
        under_water = z < sea_level
        rho_sediment[under_water] = rho_sediment[under_water] - 1030.0

        dz = self.grid.at_node["sediment_deposit__thickness"].reshape(self.grid.shape)[
            1
        ]
        pressure = self.grid.at_node[
            "lithosphere__increment_of_overlying_pressure"
        ].reshape(self.grid.shape)[1]
        pressure[:] = dz * rho_sediment * self.gravity * self.grid.dx

        Flexure1D.update(self)

        dz = self.grid.at_node["lithosphere_surface__increment_of_elevation"]
        self.subs_pool[:] += dz
        dz = self.subs_pool[:] * isostasyfrac
        self.subs_pool[:] = self.subs_pool[:] - dz

        self.grid.at_node["bedrock_surface__increment_of_elevation"][:] = dz

        self.grid.at_node["bedrock_surface__elevation"] -= dz
        self.grid.at_node["topographic__elevation"] -= dz

    def run_one_step(self, dt=100.0):
        self._dt = dt
        self.update()
