import numpy as np

from landlab import Component
from plume import Plume

from .shoreline import find_shoreline_index


class CoastalPlume(Component):

    _name = "1D hypopycnal plume along a coast"

    _input_var_names = (
        "sediment__removal_rate",
        "sediment__bulk_density",
        "channel_exit_water_flow__speed",
        "channel_exit__width",
        "channel_exit__x",
        "channel_exit__y",
    )

    _output_var_names = ("sediment_deposit__thickness",)

    _var_units = {
        "sediment_deposit__thickness": "m",
        "sediment__removal_rate": "1 / d",
        "sediment__bulk_density": "kg / m^3",
        "channel_exit_water_flow__speed": "m / s",
        "channel_exit__width": "m",
        "channel_exit__x": "m",
        "channel_exit__y": "m",
    }

    _var_mapping = {
        "sediment_deposit__thickness": "node",
        "sediment__removal_rate": "grid",
        "sediment__bulk_density": "grid",
        "channel_exit_water_flow__speed": "grid",
        "channel_exit__width": "grid",
        "channel_exit__x": "grid",
        "channel_exit__y": "grid",
    }

    _var_doc = {}

    def __init__(self, grid, **kwds):
        self._params = {
            "river_velocity": kwds.pop("river_velocity", 1.),
            "river_width": kwds.pop("river_width", 1.),
            "river_depth": kwds.pop("river_depth", 1.),
            "river_concentration": kwds.pop("river_concentration", 1.),
            "sediment_removal_rate": kwds.pop("sediment_removal_rate", 1.),
            "sediment_bulk_density": kwds.pop("sediment_bulk_density", 1600.),
            "river_loc": (0., grid.dx),
        }

        super(CoastalPlume, self).__init__(grid, **kwds)

        if "sediment_deposit__thickness" not in self.grid.at_node:
            self.grid.add_zeros("sediment_deposit__thickness", at="node")

    def update(self):
        self.grid.at_node["sediment_deposit__thickness"].fill(0.)
        z_before = self.grid.at_node["topographic__elevation"].copy()

        shore = find_shoreline(
            self.grid.x_of_node[self.grid.node_at_cell],
            z_before[self.grid.node_at_cell],
            sea_level=self.grid.at_grid["sea_level__elevation"],
        )

        self._params["river_loc"] = (shore, self.grid.dx)

        plume = Plume(self.grid, **self._params)
        plume.run_one_step()

    def run_one_step(self, dt=None):
        Plume(self.grid, **self._params).run_one_step()

        z = self.grid.at_node["topographic__elevation"].reshape((3, -1))[1]
        z_before = z.copy()
        plume_deposit = (
            self.grid.at_node["sediment_deposit__thickness"].reshape((3, -1))[1] # .copy()
        )
        plume_deposit *= dt * 365.
        index_at_max = np.argmax(plume_deposit)
        plume_deposit[:index_at_max] = plume_deposit[index_at_max]

        deposit_and_prograde(
            plume_deposit, z, sea_level=self.grid.at_grid["sea_level__elevation"]
        )

        dz = self.grid.at_node["sediment_deposit__thickness"].reshape((3, -1))[1]
        dz[:] = z - z_before


def deposit_and_prograde(deposit, z, sea_level=0.):
    """Deposit to sea level and prograde.

    Parameters
    ----------
    deposit : array_like
        A 1-D array of deposit thicknesses, starting at the shoreline.
    z : array_like
        A 1-D array of surface elevations.
    sea_level : float, optional
        Elevation of sea level.

    Examples
    --------
    >>> import numpy as np
    >>> from sequence.coastal_plume import deposit_and_prograde
    >>> z = np.array([1., 0., -1., -2])
    >>> dz = np.array([.5, .2, .1, 0.05, 0., 0.])
    >>> deposit_and_prograde(dz, z)
    array([ 1. ,  0. , -0.5, -1.8])
    """
    while deposit[0] > 0.:
        try:
            index_at_shore = find_shoreline_index(z, sea_level=sea_level)
        except ValueError:
            if z[0] <= sea_level:
                index_at_shore = 0
            elif z[-1] >= sea_level:
                break
            else:
                raise

        depth_at_shore = sea_level - z[index_at_shore]
        fraction_to_deposit = np.clip(depth_at_shore / deposit[0], 0., 1.)

        z[index_at_shore:] += (
            deposit[: len(z) - index_at_shore] * fraction_to_deposit
        )
        deposit *= 1 - fraction_to_deposit

    return z
