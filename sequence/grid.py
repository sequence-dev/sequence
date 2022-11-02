"""
Sequence-specific :class:`~landlab.grid.base.ModelGrid`
=======================================================

Define the grid used for creating *Sequence* models.
"""
import os

from landlab import RasterModelGrid

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


class SequenceModelGrid(RasterModelGrid):
    """Create a Landlab ModelGrid for use with Sequence."""

    def __init__(self, n_cols, spacing=100.0):
        """Create a *Landlab* :class:`~landlab.grid.base.ModelGrid` for use with *Sequence*.

        Parameters
        ----------
        n_cols : int
            The number of columns.
        spacing : float, optional
            The spacing between columns.

        Examples
        --------
        >>> from sequence.grid import SequenceModelGrid
        >>> grid = SequenceModelGrid(500, spacing=10.0)
        >>> grid.shape
        (3, 500)
        >>> grid.spacing
        (10.0, 10.0)
        """

        super().__init__((3, n_cols), xy_spacing=spacing)

        self.status_at_node[self.nodes_at_top_edge] = self.BC_NODE_IS_CLOSED
        self.status_at_node[self.nodes_at_bottom_edge] = self.BC_NODE_IS_CLOSED

        self.at_node["sediment_deposit__thickness"] = self.zeros(at="node")
        self.at_grid["sea_level__elevation"] = 0.0

    @classmethod
    def from_toml(cls, filepath: os.PathLike[str]):
        """Load a :class:`~SequenceModelGrid` from a *toml*-formatted file.

        Parameters
        ----------
        filepath : os.PathLike[str]
            Path to the *toml* file that contains the grid parameters.
        """
        with open(filepath, "rb") as fp:
            return SequenceModelGrid.from_dict(tomllib.load(fp)["sequence"])

    @classmethod
    def from_dict(cls, params: dict):
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
        """
        n_cols = params.get("n_cols", params["shape"][1])
        spacing = params.get("spacing", params["xy_spacing"])

        return cls(n_cols, spacing=spacing)
