"""Subside a `SequenceModelGrid` using flexure."""
import logging
from typing import Optional, Union

import numpy as np
import tomlkit as toml
from landlab.components.flexure import Flexure1D
from numpy.typing import NDArray

from ._grid import SequenceModelGrid

logger = logging.getLogger("sequence")


class DynamicFlexure(Flexure1D):
    """Calculate non-isostatic flexure."""

    def __init__(self, grid, isostasytime: Optional[float] = 7000.0, **kwds: dict):
        """Inherit from this base class for non-isostatic flexure.

        Parameters
        ----------
        grid : SequenceModelGrid
            A *Landlab* grid.
        isostasytime : float, optional
            The e-folding time for a deflection to reach equilibrium.
        """
        if isostasytime is None or np.isclose(isostasytime, 0.0):
            self._isostasy_time = None
        else:
            self._isostasy_time = self.validate_isostasy_time(isostasytime)

        active_rows = np.arange(1, grid.shape[0] - 1)

        super().__init__(grid, rows=active_rows, method="flexure", **kwds)

        self._subsidence_pool = np.zeros((len(active_rows), grid.shape[1]), dtype=float)

    @staticmethod
    def validate_isostasy_time(time: float) -> float:
        """Validate an isostasy time value.

        Parameters
        ----------
        time : float
            The isostasy time value to validate.

        Returns
        -------
        float
            The isostasy time value.

        Raises
        ------
        ValueError
            Raised if the value is invalid.
        """
        if time < 0.0:
            raise ValueError(f"negative isostasy time ({time})")
        return time

    @property
    def isostasy_time(self) -> Optional[float]:
        """Return the isostasy time."""
        return self._isostasy_time

    @staticmethod
    def calc_isostasy_fraction(isostasy_time: Optional[float], dt: float) -> float:
        """Calculate the fraction of isostatic subsidence.

        Parameters
        ----------
        isostasy_time : float or None
            The time parameter that represente the e-folding time
            to isostasy. If ``None``, assume isostasy.
        dt : float
            Time step.

        Returns
        -------
        float
            Fraction of isostatic subsidence that occurs over the time step.
        """
        if isostasy_time is None:
            return 1.0
        else:
            return 1.0 - np.exp(-dt / isostasy_time)

    def calc_dynamic_deflection(
        self, isostatic_deflection: NDArray[np.floating], dt: float
    ) -> NDArray[np.floating]:
        """Calculate the non-isostatic deflection.

        Parameters
        ----------
        isostatic_deflection : ndarray of float
            The isostatic deflection.
        dt : float
            Time step over which to subside.

        Returns
        -------
        deflection : ndarray of float
            The deflections over the given time step.
        """
        isostasy_fraction = self.calc_isostasy_fraction(self.isostasy_time, dt)

        isostasy_fraction /= self.grid.shape[0] - 2

        self._subsidence_pool[:] += isostatic_deflection
        deflection = self._subsidence_pool[:] * isostasy_fraction
        self._subsidence_pool[:] -= deflection

        return deflection


class WaterFlexure(DynamicFlexure):
    """*Landlab* component that deflects a `SequenceModelGrid` due to water loading."""

    def __init__(
        self,
        grid: SequenceModelGrid,
        isostasytime: Optional[float] = 7000.0,
        **kwds: dict,
    ):
        """Calculate flexural subsidence due to changes in water loading.

        Parameters
        ----------
        grid : SequenceModelGrid
            A *Landlab* grid.
        isostasytime : float
            The e-folding time for a deflection to reach equilibrium.
        water_density : float, optional
            Density of water.
        """
        if "lithosphere__increment_of_overlying_pressure" not in grid.at_node:
            grid.add_zeros("lithosphere__increment_of_overlying_pressure", at="node")
        if "water__increment_of_depth" not in grid.at_node:
            grid.add_zeros("water__increment_of_depth", at="node")
        if "sea_level__increment_of_elevation" not in grid.at_grid:
            grid.at_grid["sea_level__increment_of_elevation"] = 0.0

        super().__init__(grid, isostasytime=isostasytime, **kwds)

        if "bedrock_surface__increment_of_elevation" not in grid.at_node:
            grid.add_zeros("bedrock_surface__increment_of_elevation", at="node")

        self._dt = 1.0
        logger.debug(
            "Flexure parameters\n"
            + toml.dumps(
                {
                    "isostasy_time": 0.0
                    if self._isostasy_time is None
                    else self._isostasy_time,
                    "alpha": self.alpha,
                    "rigidity": self.rigidity,
                    "gamma_mantle": self.gamma_mantle,
                    "method": self.method,
                    "eet": self.eet,
                    "youngs": self.youngs,
                }
            )
        )

    @staticmethod
    def calc_water_loading(
        z: NDArray[np.floating], water_density: float
    ) -> NDArray[np.floating]:
        """Calculate the water load."""
        water_depth = np.clip(-z, a_min=0.0, a_max=None)
        return water_density * water_depth

    def calc_half_plane_deflection(self, load: float) -> NDArray[np.floating]:
        """Calculate the deflection due to a half-plane load.

        Parameters
        ----------
        load : float
            The added (or removed) load.

        Returns
        -------
        ndarray
            The deflections along the grid.
        """
        x = self.grid.x_of_node[: self.grid.shape[1]]
        r = (x[-1] - x) / self.alpha
        c = load / (2.0 * self.gamma_mantle)
        return c * np.exp(-r) * np.cos(r)

    def calc_flexure_due_to_water(
        self, change_in_water_depth: NDArray[np.floating], change_in_sea_level: float
    ):
        """Calculate flexure due to water loading.

        Parameters
        ----------
        change_in_water_depth : ndarray or float
            The change in water depth along the profile causing the deflection.
        change_in_sea_level : float
            The change in sea level that adds to the deflection.

        Returns
        -------
        ndarray of float
            Deflections along the profile caused by the water loading.
        """
        load = change_in_water_depth * self.rho_water * self.gravity * self.grid.dx
        return Flexure1D.calc_flexure(
            self.grid.x_of_node[: self.grid.shape[1]], load, self.alpha, self.rigidity
        ) + self.calc_half_plane_deflection(
            change_in_sea_level * self.rho_water * self.gravity
        )

    def update(self):
        """Update the component by a single time step."""
        self.grid.get_profile("lithosphere_surface__increment_of_elevation").fill(0.0)

        change_in_sea_level = self.grid.at_grid["sea_level__increment_of_elevation"]
        change_in_water_depth = self.grid.get_profile("water__increment_of_depth")

        isostatic_deflection = self.calc_flexure_due_to_water(
            change_in_water_depth, change_in_sea_level
        )

        deflection = self.calc_dynamic_deflection(isostatic_deflection, self._dt)

        total_deflection = self.grid.get_profile(
            "bedrock_surface__increment_of_elevation"
        )
        total_deflection[:] -= deflection

        logger.debug(
            "deflection due to water loading\n"
            f"min = {deflection.min()}\n"
            f"max = {deflection.max()}"
        )

    def run_one_step(self, dt):
        """Update the component by a time step.

        Parameters
        ----------
        dt : float, optional
            The time step over which to update the component.
        """
        self._dt = dt
        self.update()


class SedimentFlexure(DynamicFlexure):
    """*Landlab* component that deflects a `SequenceModelGrid` due to sediment loading."""

    _name = "Sediment-loading flexure"

    _unit_agnostic = True

    _time_units = "y"

    _info = {
        "sediment__total_of_loading": {
            "dtype": "float",
            "intent": "in",
            "optional": True,
            "units": "m",
            "mapping": "node",
            "doc": "Total sediment loading",
        },
        "bedrock_surface__increment_of_elevation": {
            "dtype": "float",
            "intent": "inout",
            "optional": True,
            "units": "m",
            "mapping": "node",
            "doc": "Total amount of subsidence",
        },
    }

    def __init__(
        self,
        grid: SequenceModelGrid,
        sand_density: float = 2650,
        mud_density: float = 2720.0,
        isostasytime: Optional[float] = 7000.0,
        water_density: float = 1030.0,
        **kwds: dict,
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

        self._rho_sand = self.calc_bulk_density(
            self.sand_density, self.water_density, 0.4
        )
        self._rho_mud = self.calc_bulk_density(
            self.mud_density, self.water_density, 0.65
        )
        kwds.pop("method", None)

        self._dt = 1.0

        if "sediment__total_of_loading" not in grid.at_node:
            grid.add_zeros("sediment__total_of_loading", at="node")

        super().__init__(grid, isostasytime=isostasytime, **kwds)

        if "lithosphere__increment_of_overlying_pressure" not in grid.at_node:
            grid.add_zeros("lithosphere__increment_of_overlying_pressure", at="node")
        if "lithosphere_surface__increment_of_elevation" not in grid.at_node:
            grid.add_empty("lithosphere_surface__increment_of_elevation", at="node")
        if "bedrock_surface__increment_of_elevation" not in grid.at_node:
            grid.add_zeros("bedrock_surface__increment_of_elevation", at="node")

        self._last_load = self.grid.get_profile("sediment__total_of_loading").copy()

        logger.debug(
            "Flexure parameters\n"
            + toml.dumps(
                {
                    "sand_density": self._sand_density,
                    "mud_density": self._mud_density,
                    "water_density": self._water_density,
                    "isostasy_time": 0.0
                    if self.isostasy_time is None
                    else self.isostasy_time,
                    "alpha": self.alpha,
                    "rigidity": self.rigidity,
                    "gamma_mantle": self.gamma_mantle,
                    "method": self.method,
                    "eet": self.eet,
                    "youngs": self.youngs,
                }
            )
        )

    @staticmethod
    def calc_bulk_density(
        grain_density: Union[float, NDArray[np.floating]],
        void_density: Union[float, NDArray[np.floating]],
        porosity: Union[float, NDArray[np.floating]],
    ) -> Union[float, NDArray[np.floating]]:
        """Calculate the bulk density of a material with a given porosity.

        Parameters
        ----------
        grain_density : float
            Density of grains.
        void_density : float
            Density of material that fills the void space.
        porosity : float
            The porosity of the mixture.

        Returns
        -------
        float
            The bulk density of the material.
        """
        return porosity * (void_density - grain_density) + grain_density

    @staticmethod
    def validate_density(density: float) -> float:
        """Validate a density value.

        Parameters
        ----------
        density : float
            The density value to validate.

        Returns
        -------
        float
            The density value.

        Raises
        ------
        ValueError
            Raised if the value is invalid.
        """
        if density <= 0.0:
            raise ValueError(f"negative or zero density ({density})")
        return density

    @property
    def sand_density(self) -> float:
        """Return the density of sand."""
        return self._sand_density

    @sand_density.setter
    def sand_density(self, density: float) -> None:
        # porosity = 40%
        self._sand_density = SedimentFlexure.validate_density(density)
        self._rho_sand = SedimentFlexure.calc_bulk_density(
            self.sand_density, self.water_density, 0.4
        )

    @property
    def sand_bulk_density(self) -> Union[float, NDArray[np.floating]]:
        """Return the bulk density of sand."""
        return self._rho_sand

    @property
    def mud_density(self) -> float:
        """Return the density of mud."""
        return self._mud_density

    @mud_density.setter
    def mud_density(self, density: float) -> None:
        # porosity = 65%
        self._mud_density = SedimentFlexure.validate_density(density)
        self._rho_mud = SedimentFlexure.calc_bulk_density(
            self.mud_density, self.water_density, 0.65
        )

    @property
    def mud_bulk_density(self) -> Union[float, NDArray[np.floating]]:
        """Return the bulk density of mud."""
        return self._rho_mud

    @property
    def water_density(self) -> float:
        """Return the density of water."""
        return self._water_density

    @water_density.setter
    def water_density(self, density: float) -> None:
        self._water_density = SedimentFlexure.validate_density(density)
        self._rho_sand = SedimentFlexure.calc_bulk_density(
            self.sand_density, self.water_density, 0.4
        )
        self._rho_mud = SedimentFlexure.calc_bulk_density(
            self.mud_density, self.water_density, 0.65
        )

    @staticmethod
    def _calc_loading(
        deposit_thickness: NDArray[np.floating],
        z: NDArray[np.floating],
        sediment_porosity: float,
        sediment_density: Union[float, NDArray[np.floating]],
        water_density: float,
    ) -> NDArray[np.floating]:
        """Calculate the loading due to a, possibly submerged, sediment deposit.

        Parameters
        ----------
        deposit_thickness : array-like
            The amount of sediment deposited along the profile.
        z : array-like
            The elevation of the profile before the new sediment has
            been added.
        sediment_porosity : float
            The porosity of the sediment.
        sediment_density : float
            The bulk density of the added sediment.
        water_density : float
            The density of water.

        Returns
        -------
        ndarray
            The loading along the profile.
        """
        z_new = z + deposit_thickness

        dry = (z >= 0.0) & (z_new >= 0.0)
        wet = (z <= 0.0) & (z_new <= 0.0)

        void_density = np.zeros_like(z)
        void_density[wet] = water_density

        mixed = ~dry & ~wet
        dry_fraction = np.abs(
            np.maximum(z_new[mixed], z[mixed]) / deposit_thickness[mixed]
        )

        void_density[mixed] = water_density * (1.0 - dry_fraction)

        density = SedimentFlexure.calc_bulk_density(
            sediment_density, void_density, sediment_porosity
        )

        return density * deposit_thickness

    @staticmethod
    def _calc_density(
        sand_fraction: Union[float, NDArray], sand_density: float, mud_density: float
    ) -> Union[float, NDArray]:
        """Calculate the density of a sand/mud mixture.

        Parameters
        ----------
        sand_fraction : float or ndarray
            Fraction of sediment that is sand. The rest is mud.
        sand_density : float
            The density of the sand.
        mud_density : float
            The density of the mud.

        Returns
        -------
        float or ndarray
            The density of the mixture.

        Examples
        --------
        >>> from sequence.sediment_flexure import SedimentFlexure
        >>> SedimentFlexure._calc_density(0.5, 1600, 1200)
        1400.0
        >>> SedimentFlexure._calc_density([1.0, 0.75, 0.5, 0.25, 0.0], 1600.0, 1200.0)
        array([ 1600.,  1500.,  1400.,  1300.,  1200.])
        """
        sand_fraction = np.asarray(sand_fraction)
        return sand_fraction * sand_density + (1.0 - sand_fraction) * mud_density

    def update(self) -> None:
        """Update the component by a single time step."""
        self.grid.get_profile("lithosphere_surface__increment_of_elevation").fill(0.0)

        total_load = self.grid.get_profile("sediment__total_of_loading")
        new_load = total_load - self._last_load
        self._last_load[:] = total_load

        pressure = self.grid.get_profile("lithosphere__increment_of_overlying_pressure")
        pressure[:] = new_load * self.gravity * self.grid.dx

        Flexure1D.update(self)

        isostatic_deflection = self.grid.get_profile(
            "lithosphere_surface__increment_of_elevation"
        )

        deflection = self.calc_dynamic_deflection(isostatic_deflection, self._dt)

        total_deflection = self.grid.get_profile(
            "bedrock_surface__increment_of_elevation"
        )
        total_deflection -= deflection

        logger.debug(
            "deflection due to sediment loading\n"
            f"min = {deflection.min()}\n"
            f"max = {deflection.max()}"
        )

    def run_one_step(self, dt: float = 1.0) -> None:
        """Update the component by a time step.

        Parameters
        ----------
        dt : float, optional
            The time step over which to update the component.
        """
        self._dt = dt
        self.update()
