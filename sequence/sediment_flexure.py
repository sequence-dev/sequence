import numpy as np
from landlab.components.flexure import Flexure1D


class SedimentFlexure(Flexure1D):

    _name = "Sediment-loading flexure"

    _unit_agnostic = True

    _time_units = "y"

    _info = {
        "sediment_deposit__thickness": {
            "dtype": "float",
            "intent": "in",
            "optional": True,
            "units": "m",
            "mapping": "node",
            "doc": "Thickness of deposited or eroded sediment",
        },
        "sea_level__elevation": {
            "dtype": "float",
            "intent": "in",
            "optional": True,
            "units": "m",
            "mapping": "grid",
            "doc": "Elevation of sea level",
        },
        "topographic__elevation": {
            "dtype": "float",
            "intent": "inout",
            "optional": True,
            "units": "m",
            "mapping": "node",
            "doc": "land and ocean bottom elevation, positive up",
        },
        "bedrock_surface__elevation": {
            "dtype": "float",
            "intent": "inout",
            "optional": True,
            "units": "m",
            "mapping": "node",
            "doc": "New bedrock elevation following subsidence",
        },
        "bedrock_surface__increment_of_elevation": {
            "dtype": "float",
            "intent": "out",
            "optional": True,
            "units": "m",
            "mapping": "node",
            "doc": "Amount of subsidence due to sediment loading",
        },
        "delta_sediment_sand__volume_fraction": {
            "dtype": "float",
            "intent": "in",
            "optional": True,
            "units": "-",
            "mapping": "node",
            "doc": "delta sand fraction",
        },
    }

    def __init__(
        self,
        grid,
        sand_density=2650,
        mud_density=2720.0,
        isostasytime=7000.0,
        water_density=1030.0,
        **kwds,
        # **sediments,
    ):
        """Subside elevations due to sediment loading.

        Parameters
        ----------
        grid : ModelGrid
            A landlab grid.
        sand_density : float, optional
            Grain density of the sediment sand-fraction.
        mud_density : float, optional
            Grain density of the sediment mud-fraction.
        water_density : float, optional
            Density of water.
        isostasytime : float, optional
            Response time of the lithosphere to loading.
        """
        self._water_density = SedimentFlexure.validate_density(water_density)
        self._sand_density = SedimentFlexure.validate_density(sand_density)
        self._mud_density = SedimentFlexure.validate_density(mud_density)

        self._rho_sand = self._calc_bulk_density(
            self.sand_density, self.water_density, 0.4
        )
        self._rho_mud = self._calc_bulk_density(
            self.mud_density, self.water_density, 0.65
        )

        self._isostasytime = SedimentFlexure.validate_isostasy_time(isostasytime)

        self._dt = 100.0  # default timestep = 100 y

        # grid.add_zeros("lithosphere__increment_of_overlying_pressure", at="node")

        super().__init__(grid, **kwds)

        if "lithosphere__increment_of_overlying_pressure" not in grid.at_node:
            grid.add_zeros("lithosphere__increment_of_overlying_pressure", at="node")
        if "lithosphere_surface__increment_of_elevation" not in grid.at_node:
            grid.add_empty("lithosphere_surface__increment_of_elevation", at="node")
        if "sea_level__elevation" not in grid.at_grid:
            grid.at_grid["sea_level__elevation"] = 0.0
        if "delta_sediment_sand__volume_fraction" not in grid.at_node:
            grid.add_ones("delta_sediment_sand__volume_fraction", at="node")
        if "bedrock_surface__increment_of_elevation" not in grid.at_node:
            grid.add_empty("bedrock_surface__increment_of_elevation", at="node")

        self.subs_pool = self.grid.zeros(at="node")

    @staticmethod
    def _calc_bulk_density(grain_density, water_density, porosity):
        return grain_density * (1.0 - porosity) + water_density * porosity

    @staticmethod
    def validate_density(density):
        if density <= 0.0:
            raise ValueError(f"negative or zero density ({density})")
        return density

    @staticmethod
    def validate_isostasy_time(time):
        if time < 0.0:
            raise ValueError(f"negative isostasy time ({time})")
        return time

    @property
    def sand_density(self):
        return self._sand_density

    @sand_density.setter
    def sand_density(self, density):
        # porosity = 40%
        self._sand_density = SedimentFlexure.validate_density(density)
        self._rho_sand = SedimentFlexure._calc_bulk_density(
            self.sand_density, self.water_density, 0.4
        )

    @property
    def sand_bulk_density(self):
        return self._rho_sand

    @property
    def mud_density(self):
        return self._mud_density

    @mud_density.setter
    def mud_density(self, density):
        # porosity = 65%
        self._mud_density = SedimentFlexure.validate_density(density)
        self._rho_mud = SedimentFlexure._calc_bulk_density(
            self.mud_density, self.water_density, 0.65
        )

    @property
    def mud_bulk_density(self):
        return self._rho_mud

    @property
    def water_density(self):
        return self._water_density

    @water_density.setter
    def water_density(self, density):
        self._water_density = SedimentFlexure.validate_density(density)
        self._rho_sand = SedimentFlexure._calc_bulk_density(
            self.sand_density, self.water_density, 0.4
        )
        self._rho_mud = SedimentFlexure._calc_bulk_density(
            self.mud_density, self.water_density, 0.65
        )

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
        rho_sediment[under_water] = rho_sediment[under_water] - self.water_density

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
