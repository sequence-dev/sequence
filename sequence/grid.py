"""Define the grid used for creating *Sequence* models."""
from __future__ import annotations

import os
import sys

import numpy as np
from landlab import RasterModelGrid
from numpy.typing import NDArray

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class SequenceModelGrid(RasterModelGrid):
    """Create a Landlab ModelGrid for use with Sequence."""

    def __init__(
        self, shape: int | tuple[int, int], spacing: float | tuple[float, float] = 100.0
    ):
        """Create a *Landlab* :class:`~landlab.grid.base.ModelGrid` for use with *Sequence*.

        Parameters
        ----------
        shape : int or tuple of int
            The number of columns in the cross-shore direction or, if a ``tuple``,
            ``(n_rows, n_cols)``  where rows are in the along-shore direction and
            columns in the cross-shore direction.
        spacing : float or tuple of float, optional
            The spacing between columns or, if ``len(shape) == 2``,
            ``(row_spacing, col_spacing)``.

        Examples
        --------
        >>> from sequence import SequenceModelGrid
        >>> grid = SequenceModelGrid(5, spacing=10.0)
        >>> grid.y_of_row
        array([  0.,  1.,  2.])
        >>> grid.x_of_column
        array([ 0.,  10.,  20.,  30.,  40.])

        >>> grid = SequenceModelGrid((3, 5), spacing=(10000.0, 10.0))
        >>> grid.y_of_row
        array([  0.,  10000.,  20000.,  30000., 40000.])
        >>> grid.x_of_column
        array([ 0.,  10.,  20.,  30.,  40.])
        """
        row_col_shape: list[int] = np.atleast_1d(np.asarray(shape, dtype=int))
        row_col_spacing: list[float] = np.atleast_1d(np.asarray(spacing, dtype=float))

        if (len(row_col_shape) == 1 and len(row_col_spacing) != 1) or (
            len(row_col_shape) != 1 and len(row_col_spacing) != len(row_col_shape)
        ):
            raise ValueError(
                f"spacing dimension ({len(row_col_spacing)}) does not match shape"
                f" dimension ({len(row_col_shape)})"
            )

        if len(row_col_shape) == 1:
            n_rows, n_cols = 1, row_col_shape[0]
        elif len(row_col_shape) == 2:
            n_rows, n_cols = row_col_shape
        else:
            raise ValueError(
                f"invalid number of dimensions for grid ({len(row_col_shape)})"
            )

        if len(row_col_shape) == 1:
            row_spacing, col_spacing = 1.0, row_col_spacing[0]
        elif len(row_col_shape) == 2:
            row_spacing, col_spacing = row_col_spacing

        super().__init__((n_rows + 2, n_cols), xy_spacing=(col_spacing, row_spacing))

        self.status_at_node[self.nodes_at_top_edge] = self.BC_NODE_IS_CLOSED
        self.status_at_node[self.nodes_at_bottom_edge] = self.BC_NODE_IS_CLOSED

        self.at_node["sediment_deposit__thickness"] = self.zeros(at="node")
        self.at_grid["sea_level__elevation"] = 0.0

        # self.new_field_location("row", size=int(n_rows + 2))
        self.new_field_location("row", size=int(n_rows))

    @property
    def x_of_column(self) -> NDArray:
        """X-coordinate for each column of the grid."""
        return self.x_of_node[self.nodes_at_top_edge]

    @property
    def number_of_rows(self) -> int:
        """Number of rows of nodes."""
        return self.shape[0]
        # return self.shape[0] - 2

    @property
    def number_of_columns(self) -> int:
        """Number of columns of nodes."""
        return self.shape[1]

    @property
    def y_of_row(self) -> NDArray:
        """Y-coordinate for each row of the grid."""
        return self.y_of_node[self.nodes_at_left_edge]

    def get_profile(self, name: str) -> NDArray:
        """Return the values of a field along the grid's profile.

        Parameters
        ----------
        name : str
            The name of an at-node field.

        Returns
        -------
        values : ndarray
            The values of the field located at the middle row of nodes.
        """
        return self.at_node[name].reshape(self.shape)[1:-1]
        # return self.at_node[name].reshape(self.shape)[row]

    @classmethod
    def from_toml(cls, filepath: os.PathLike[str]) -> SequenceModelGrid:
        """Load a :class:`~SequenceModelGrid` from a *toml*-formatted file.

        Parameters
        ----------
        filepath : os.PathLike[str]
            Path to the *toml* file that contains the grid parameters.
        """
        with open(filepath, "rb") as fp:
            return SequenceModelGrid.from_dict(tomllib.load(fp)["sequence"]["grid"])

    @classmethod
    def from_dict(cls, params: dict) -> SequenceModelGrid:
        """Create a :class:`~SequenceModelGrid` from a `dict`.

        If possible, this alternate constructor simply passes
        along the dictionary's items as keywords to
        :meth:`~SequenceModelGrid.__init__`. It also, however,
        supports a dictionary that contains the parameters
        used to create a general :class:`~landlab.grid.raster.RasterModelGrid`,
        quietly ignoring the extra parameters.

        Parameters
        ----------
        params : dict
            A dictionary that contains the parameters needed to
            create the grid.

        Examples
        --------
        >>> from sequence import SequenceModelGrid
        >>> params = {"shape": 5, "spacing": 10.0}
        >>> grid = SequenceModelGrid.from_dict(params)
        >>> grid.y_of_row
        array([  0.,  1.,  2.])
        >>> grid.x_of_column
        array([ 0.,  10.,  20.,  30.,  40.])

        >>> params = {"shape": (3, 5), "spacing": (10000.0, 10.0)}
        >>> grid = SequenceModelGrid.from_dict(params)
        >>> grid.y_of_row
        array([  0.,  10000.,  20000.,  30000., 40000.])
        >>> grid.x_of_column
        array([ 0.,  10.,  20.,  30.,  40.])
        """
        if "shape" in params:
            shape = params["shape"]
        elif "n_cols" in params:
            shape = params["n_cols"]
        else:
            raise KeyError("shape")

        if "spacing" in params:
            spacing = params["spacing"]
        elif "xy_spacing" in params:
            spacing = np.atleast_1d(params["xy_spacing"])[::-1]
        else:
            raise KeyError("spacing")

        return cls(shape, spacing=spacing)
