"""Diffuse sediment along a profile."""
from typing import Any

import numpy as np
from landlab.components import LinearDiffuser
from numpy.typing import NDArray

from ._grid import SequenceModelGrid
from .shoreline import find_shoreline


class SubmarineDiffuser(LinearDiffuser):
    """Model sea-floor evolution on a `SequenceModelGrid` as diffusion."""

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
            "intent": "inout",
            "optional": False,
            "units": "m",
            "mapping": "node",
            "doc": "Thickness of deposition or erosion",
        },
    }

    def __init__(
        self,
        grid: SequenceModelGrid,
        sea_level: float = 0.0,
        plain_slope: float = 0.0008,
        wave_base: float = 60.0,
        shoreface_height: float = 15.0,
        alpha: float = 0.0005,
        shelf_slope: float = 0.001,
        sediment_load: float = 3.0,
        load_sealevel: float = 0.0,
        basin_width: float = 500000.0,
        **kwds: Any,
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
            Coefficient used to calculate the diffusion coefficient (1 / m).
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
    def plain_slope(self) -> float:
        """Return the gradient of the delta plain."""
        return self._plain_slope

    @plain_slope.setter
    def plain_slope(self, value: float) -> None:
        self._plain_slope = float(value)
        self._ksh = self._load / self._plain_slope

    @property
    def wave_base(self) -> float:
        """Return the depth of the wave base."""
        return self._wave_base

    @wave_base.setter
    def wave_base(self, value: float) -> None:
        self._wave_base = float(value)

    @property
    def shoreface_height(self) -> float:
        """Return the height of the shoreface."""
        return self._shoreface_height

    @shoreface_height.setter
    def shoreface_height(self, value: float) -> None:
        self._shoreface_height = float(value)

    @property
    def alpha(self) -> float:
        """Return the alpha parameter."""
        return self._alpha

    @alpha.setter
    def alpha(self, value: float) -> None:
        self._alpha = float(value)

    @property
    def shelf_slope(self) -> float:
        """Return the slope of the shelf."""
        return self._shelf_slope

    @shelf_slope.setter
    def shelf_slope(self, value: float) -> None:
        self._shelf_slope = float(value)

    @property
    def sediment_load(self) -> float:
        """Return the sediment load entering the profile."""
        return self._load0

    @sediment_load.setter
    def sediment_load(self, value: float) -> None:
        self._load0 = float(value)
        self._load = self._load0 * (1 + self._sea_level * self._load_sl)
        self._ksh = self._load / self._plain_slope
        self.grid.at_grid["sediment_load"] = self._load

    @property
    def load0(self) -> float:
        """Return the sediment load entering the profile."""
        return self._load0

    @property
    def k_land(self) -> float:
        """Return the diffusion coefficient use for land."""
        return self._ksh

    @property
    def time(self) -> float:
        """Return the component's current time."""
        return self._time

    @property
    def sea_level(self) -> float:
        """Return sea level elevation."""
        return self.grid.at_grid["sea_level__elevation"]

    @sea_level.setter
    def sea_level(self, sea_level: float) -> None:
        self.grid.at_grid["sea_level__elevation"] = sea_level

    def calc_diffusion_coef(
        self, x_of_shore: NDArray[np.floating] | float
    ) -> NDArray[np.floating]:
        """Calculate and store diffusion coefficient values.

        Parameters
        ----------
        x_of_shore : float
            The x-position of the shoreline.

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
        x_of_shore = np.atleast_1d(x_of_shore)

        sea_level = self.grid.at_grid["sea_level__elevation"]

        water_depth = sea_level - self._grid.get_profile("topographic__elevation")
        k = self.grid.get_profile("kd")
        x = self.grid.x_of_column

        n_rows = k.shape[0]

        assert len(x_of_shore) == n_rows

        for row in range(n_rows):
            under_water = water_depth[row] > 0.0
            deep_water = water_depth[row] > self._wave_base
            land = ~under_water

            b = (
                self._shoreface_height * self._alpha + self._shelf_slope
            ) * self.grid.dx

            k[row, under_water] = (
                self._load
                * ((x[under_water] - x_of_shore[row]) + self.grid.dx)
                / (water_depth[row, under_water] + b)
            )

            k[row, deep_water] *= np.exp(
                -(water_depth[row, deep_water] - self._wave_base) / self._wave_base
            )

            self._load = self._load0 * (1 + sea_level * self._load_sl)
            self._ksh = self._load / self._plain_slope

            if self._basin_width > 0.0:
                k[row, land] = (
                    self._ksh * (self._basin_width + x[land]) / self._basin_width
                )
            else:
                k[row, land] = self._ksh

            # TODO: modify diffusion outside of the channel row.
            if row != n_rows // 2:
                k[row, land] *= 0.5

            # if row == n_rows // 2:
            #     if self._basin_width > 0.0:
            #         k[row, land] = (
            #             self._ksh * (self._basin_width + x[land]) / self._basin_width
            #         )
            #     else:
            #         k[row, land] = self._ksh
            # else:  # outside of the channel with low diffusivity
            #     if self._basin_width > 0.0:
            #         k[row, land] = self._ksh * (self.grid.dx + x[land]) / self._basin_width
            #     else:
            #         k[row, land] = self._ksh * (self.grid.dx) / self._basin_width

            # if self._basin_width > 0.0:
            #     k[land] = self._ksh * (self._basin_width + x[land]) / self._basin_width
            # else:
            #     k[land] = self._ksh

        k = self.grid.at_node["kd"].reshape(self.grid.shape)
        k[0, :] = k[1, :]
        k[-1, :] = k[-1, :]

        return k

    def run_one_step(self, dt: float) -> None:
        """Advance component one time step.

        Parameters
        ----------
        dt : float
            Time step to advance component by.
        """
        shore = find_shoreline(
            self.grid.x_of_column,
            self.grid.get_profile("topographic__elevation"),
            sea_level=self.grid.at_grid["sea_level__elevation"],
        )

        self.calc_diffusion_coef(shore)

        # set elevation at upstream boundary to ensure proper sediment influx
        x = self.grid.x_of_column
        z = self._grid.at_node["topographic__elevation"].reshape(self.grid.shape)
        # k = self._grid.at_node["kd"].reshape(self.grid.shape)
        # z[1, 0] = z[1,1] + self._load / k[1, 0] * (x[1,1]-x[1,0])
        # z[1, 0] = z[1, 1] + self._plain_slope * (x[1, 1] - x[1, 0])
        z[1, 0] = z[1, 1] + self._plain_slope * (x[1] - x[0])

        z[1:-1, 0] = z[1:-1, 1] + self._plain_slope * (x[1] - x[0])

        z_before = self.grid.at_node["topographic__elevation"].copy()

        super().run_one_step(dt)

        dz = self.grid.at_node["topographic__elevation"] - z_before
        self.grid.at_node["topographic__elevation"][:] = z_before

        self.grid.at_node["sediment_deposit__thickness"][:] += dz

        self._time += dt
