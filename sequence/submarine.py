#! /usr/bin/env python
import numpy as np
from landlab.components import LinearDiffuser

from .shoreline import find_shoreline


class SubmarineDiffuser(LinearDiffuser):

    _name = "Submarine Diffusion"

    _time_units = "y"

    _info = {
        "sea_level__elevation": {
            "dtype": "float",
            "intent": "in",
            "optional": False,
            "units": "m",
            "mapping": "grid",
            "doc": "Position of sea level",
        },
        "topographic__elevation": {
            "dtype": "float",
            "intent": "inout",
            "optional": False,
            "units": "m",
            "mapping": "node",
            "doc": "land and ocean bottom elevation, positive up",
        },
        "sediment_deposit__thickness": {
            "dtype": "float",
            "intent": "out",
            "optional": False,
            "units": "m",
            "mapping": "node",
            "doc": "Thickness of deposition or erosion",
        },
    }

    def __init__(
        self,
        grid,
        sea_level=0.0,
        plain_slope=0.0008,
        wave_base=60.0,
        shoreface_height=15.0,
        alpha=0.0005,
        shelf_slope=0.001,
        sediment_load=3.0,
        load_sealevel=0.0,
        basin_width=500000.0,
        **kwds
    ):
        """Diffuse the ocean bottom.
        Parameters
        ----------
        grid: RasterModelGrid
            A landlab grid.
        sea_level: float, optional
            The current sea level (m).
        plain_slope: float, optional
            Slope of the delta plain (m / m).
        wave_base: float, optional
            Wave base (m).
        shoreface_height: float, optional
            Water depth of the shelf/slope break (m).
        alpha: float, optional
            Some coefficient (1 / m).
        shelf_slope: float, optional
            Slope of the shelf (m / m).
        sediment_load: float, optional
            Sediment load entering the profile (m2 / y).
        load_sealevel: float, optional
            Fractional variation of sediment load with sea level (m2/y/m_sl).
            i.e., .003 =0.3% increase/decrease with sea level rise/fall (30% with 100m)
        basin_width: float, optional
            Length of drainage basin upstream of model.  Creates increase in
            diffusivity downstream by (basin_width + x) / basin_width
            from increase river flow (m).
        """
        self._plain_slope = float(plain_slope)
        self._wave_base = float(wave_base)
        self._shoreface_height = float(shoreface_height)
        self._alpha = float(alpha)
        self._shelf_slope = float(shelf_slope)
        self._load0 = float(sediment_load)
        self._load_sl = float(load_sealevel)
        self._sea_level = sea_level
        self._load = self._load0 * (1 + self._sea_level * self._load_sl)
        self._ksh = self._load / self._plain_slope
        self._basin_width = float(basin_width)
        grid.at_grid["sea_level__elevation"] = sea_level
        self._sea_level = grid.at_grid["sea_level__elevation"]
        grid.at_grid["sediment_load"] = self._load

        if "kd" not in grid.at_node:
            grid.add_zeros("kd", at="node")
        if "sediment_deposit__thickness" not in grid.at_node:
            grid.add_zeros("sediment_deposit__thickness", at="node")

        self._time = 0.0

        kwds.setdefault("linear_diffusivity", "kd")
        super().__init__(grid, **kwds)

    @property
    def plain_slope(self):
        return self._plain_slope

    @plain_slope.setter
    def plain_slope(self, value):
        self._plain_slope = float(value)
        self._ksh = self._load / self._plain_slope

    @property
    def wave_base(self):
        return self._wave_base

    @wave_base.setter
    def wave_base(self, value):
        self._wave_base = float(value)

    @property
    def shoreface_height(self):
        return self._shoreface_height

    @shoreface_height.setter
    def shoreface_height(self, value):
        self._shoreface_height = float(value)

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        self._alpha = float(value)

    @property
    def shelf_slope(self):
        return self._shelf_slope

    @shelf_slope.setter
    def shelf_slope(self, value):
        self._shelf_slope = float(value)

    @property
    def sediment_load(self):
        return self._load0

    @sediment_load.setter
    def sediment_load(self, value):
        self._load0 = float(value)
        self._load = self._load0 * (1 + self._sea_level * self._load_sl)
        self._ksh = self._load / self._plain_slope
        self.grid.at_grid["sediment_load"] = self._load

    @property
    def k0(self):
        return self._k0

    @property
    def load0(self):
        return self._load0

    @property
    def k_land(self):
        return self._ksh

    @property
    def time(self):
        return self._time

    @property
    def sea_level(self):
        return self.grid.at_grid["sea_level__elevation"]

    @sea_level.setter
    def sea_level(self, sea_level):
        self.grid.at_grid["sea_level__elevation"] = sea_level

    def calc_diffusion_coef(self, x_of_shore):
        """Calculate and store diffusion coefficient values.

        Examples
        --------

        The example below tests the result with 3 of the middle-row nodes above
        sea level and three below, two of which are in deep water (below the
        default 60 m wave base).

        >>> from landlab import RasterModelGrid
        >>> import numpy as np

        >>> grid = RasterModelGrid((3, 6), xy_spacing=200.0)
        >>> z = grid.add_zeros("topographic__elevation", at="node")
        >>> z[6:12] = np.array([3., 3., 1., -1., -85., -85.])
        >>> z.reshape((3, 6))
        array([[  0.,   0.,   0.,   0.,   0.,   0.],
               [  3.,   3.,   1.,  -1., -85., -85.],
               [  0.,   0.,   0.,   0.,   0.,   0.]])

        >>> submarine_diffuser = SubmarineDiffuser(grid, basin_width=0.0)
        >>> diffusion_coef = submarine_diffuser.calc_diffusion_coef(x_of_shore=500.0)

        >>> np.round(diffusion_coef.reshape((3, 6))[1])
        array([ 3750.,  3750.,  3750.,   333.,    11.,    16.])

        The calculated diffusion coefficient is also saved as an *at-node* field.

        >>> diffusion_coef is grid.at_node["kd"]
        True
        """
        sea_level = self.grid.at_grid["sea_level__elevation"]
        water_depth = sea_level - self._grid.at_node["topographic__elevation"]

        under_water = water_depth > 0.0
        deep_water = water_depth > self._wave_base
        land = ~under_water

        k = self.grid.at_node["kd"]

        x = self.grid.x_of_node
        b = (self._shoreface_height * self._alpha + self._shelf_slope) * self.grid.dx

        k[under_water] = (
            self._load
            * ((x[under_water] - x_of_shore) + self.grid.dx)
            / (water_depth[under_water] + b)
        )

        k[deep_water] *= np.exp(
            -(water_depth[deep_water] - self._wave_base) / self._wave_base
        )

        self._load = self._load0 * (1 + sea_level * self._load_sl)
        self._ksh = self._load / self._plain_slope
        if self._basin_width > 0.0:
            k[land] = self._ksh * (self._basin_width + x[land]) / self._basin_width
        else:
            k[land] = self._ksh

        return k

    def run_one_step(self, dt):
        z_before = self.grid.at_node["topographic__elevation"].copy()

        shore = find_shoreline(
            self.grid.x_of_node[self.grid.node_at_cell],
            z_before[self.grid.node_at_cell],
            sea_level=self.grid.at_grid["sea_level__elevation"],
        )

        self.calc_diffusion_coef(shore)

        # set elevation at upstream boundary to ensure proper sediment influx
        x = self.grid.x_of_node.reshape(self.grid.shape)
        z = self._grid.at_node["topographic__elevation"].reshape(self.grid.shape)
        # k = self._grid.at_node["kd"].reshape(self.grid.shape)
        # z[1, 0] = z[1,1] + self._load / k[1, 0] * (x[1,1]-x[1,0])
        z[1, 0] = z[1, 1] + self._plain_slope * (x[1, 1] - x[1, 0])
        # self._load/self._load0)

        super().run_one_step(dt)

        self.grid.at_node["sediment_deposit__thickness"][:] = (
            self.grid.at_node["topographic__elevation"] - z_before
        )

        self._time += dt
