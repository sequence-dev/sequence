"""Subside a `SequenceModelGrid` using flexure."""
from typing import Union

import numpy as np
from landlab.components.flexure import Flexure1D
from numpy.typing import NDArray

from ._grid import SequenceModelGrid


class SedimentFlexure(Flexure1D):
    """*Landlab* component that deflects a `SequenceModelGrid` due to sediment loading."""

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
            "intent": "in",
            "optional": True,
            "units": "m",
            "mapping": "node",
            "doc": "land and ocean bottom elevation, positive up",
        },
        "delta_sediment_sand__volume_fraction": {
            "dtype": "float",
            "intent": "in",
            "optional": True,
            "units": "-",
            "mapping": "node",
            "doc": "delta sand fraction",
        },
        "bedrock_surface__increment_of_elevation": {
            "dtype": "float",
            "intent": "inout",
            "optional": True,
            "units": "m",
            "mapping": "node",
            "doc": "Total amount of subsidence",
        },
        "sediment__increment_of_thickness": {
            "dtype": "float",
            "intent": "in",
            "optional": True,
            "units": "m",
            "mapping": "node",
            "doc": "Thickness of new sediment",
        },
        "sediment__bulk_density": {
            "dtype": "float",
            "intent": "in",
            "optional": True,
            "units": "m",
            "mapping": "node",
            "doc": "Density of new sediment",
        },
    }

    def __init__(
        self,
        grid: SequenceModelGrid,
        sand_density: float = 2650,
        mud_density: float = 2720.0,
        isostasytime: Union[float, None] = 7000.0,
        water_density: float = 1030.0,
        **kwds: dict,
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

        if np.isclose(isostasytime, 0.0):
            isostasytime = None
        self._isostasy_time = (
            SedimentFlexure.validate_isostasy_time(isostasytime)
            if isostasytime is not None
            else None
        )
        self._dt = 1.0

        super().__init__(grid, rows=1, **kwds)

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

        self.subs_pool = np.zeros_like(
            self.grid.get_profile("lithosphere_surface__increment_of_elevation")
        )

    @staticmethod
    def _calc_bulk_density(
        grain_density: float, water_density: float, porosity: float
    ) -> float:
        return grain_density * (1.0 - porosity) + water_density * porosity

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
    def isostasy_time(self) -> Union[float, None]:
        """Return the isostasy time."""
        return self._isostasy_time

    @property
    def sand_density(self) -> float:
        """Return the density of sand."""
        return self._sand_density

    @sand_density.setter
    def sand_density(self, density: float) -> None:
        # porosity = 40%
        self._sand_density = SedimentFlexure.validate_density(density)
        self._rho_sand = SedimentFlexure._calc_bulk_density(
            self.sand_density, self.water_density, 0.4
        )

    @property
    def sand_bulk_density(self) -> float:
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
        self._rho_mud = SedimentFlexure._calc_bulk_density(
            self.mud_density, self.water_density, 0.65
        )

    @property
    def mud_bulk_density(self) -> float:
        """Return the bulk density of mud."""
        return self._rho_mud

    @property
    def water_density(self) -> float:
        """Return the density of water."""
        return self._water_density

    @water_density.setter
    def water_density(self, density: float) -> None:
        self._water_density = SedimentFlexure.validate_density(density)
        self._rho_sand = SedimentFlexure._calc_bulk_density(
            self.sand_density, self.water_density, 0.4
        )
        self._rho_mud = SedimentFlexure._calc_bulk_density(
            self.mud_density, self.water_density, 0.65
        )

    @staticmethod
    def _calc_loading(
        deposit_thickness: NDArray[np.floating],
        z: NDArray[np.floating],
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
        mixed = ~dry & ~wet

        density = np.full_like(z, sediment_density)
        density[wet] -= water_density

        dry_fraction = np.abs(
            np.maximum(z_new[mixed], z[mixed]) / deposit_thickness[mixed]
        )
        wet_fraction = 1.0 - dry_fraction

        density[mixed] -= wet_fraction * water_density

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

    @staticmethod
    def _calc_isostasy_fraction(isostasy_time: Union[float, None], dt: float) -> float:
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

    def update(self) -> None:
        """Update the component by a single time step."""
        self.grid.get_profile("lithosphere_surface__increment_of_elevation").fill(0.0)

        sea_level = self.grid.at_grid["sea_level__elevation"]
        elevation = self.grid.get_profile("topographic__elevation")
        deposit_thickness = self.grid.get_profile("sediment_deposit__thickness")
        sand_fraction = self.grid.get_profile("delta_sediment_sand__volume_fraction")

        sediment_density = self._calc_density(
            sand_fraction, self.sand_bulk_density, self.mud_bulk_density
        )

        pressure = self.grid.get_profile("lithosphere__increment_of_overlying_pressure")
        pressure[:] = (
            self._calc_loading(
                deposit_thickness,
                elevation - sea_level,
                sediment_density,
                self.water_density,
            )
            * self.gravity
            * self.grid.dx
        )

        Flexure1D.update(self)

        isostatic_deflection = self.grid.get_profile(
            "lithosphere_surface__increment_of_elevation"
        )
        isostasy_fraction = self._calc_isostasy_fraction(self.isostasy_time, self._dt)
        self.subs_pool[:] += isostatic_deflection
        deflection = self.subs_pool[:] * isostasy_fraction
        self.subs_pool[:] = self.subs_pool[:] - deflection

        total_deflection = self.grid.get_profile(
            "bedrock_surface__increment_of_elevation"
        )
        total_deflection += deflection

    def run_one_step(self, dt: float = 1.0) -> None:
        """Update the component by a time step.

        Parameters
        ----------
        dt : float, optional
            The time step over which to update the component.
        """
        self._dt = dt
        self.update()
