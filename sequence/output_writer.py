"""Write a `SequenceModelGrid` to a file."""
from __future__ import annotations

import errno
import os
from collections.abc import Iterable
from os import PathLike

import numpy as np
from landlab import Component

from sequence.grid import SequenceModelGrid
from sequence.netcdf import to_netcdf


class OutputWriter(Component):
    """Write output to a netcdf file."""

    def __init__(
        self,
        grid: SequenceModelGrid,
        filepath: str | PathLike[str],
        interval: int = 1,
        fields: Iterable[str] | None = None,
        clobber: bool = False,
        rows: Iterable[str] | None = None,
    ):
        """Create an output-file writer.

        Parameters
        ----------
        grid : SequenceModelGrid
            The grid to write to a file.
        filepath : path-like
            Path to the output file.
        interval : int, optional
            The number of time steps between updates to the output file.
        fields : list of str, optional
            Names of (at-node) fields to include in the output file.
        clobber : bool, optional
            If `True` and the provided file already exists, quietly overwrite
            it, otherwise raise an exception.
        rows : iterable of int
            The rows of the grid to include in the file.
        """
        if fields is None:
            fields = []

        super().__init__(grid)

        self._clobber = clobber
        self.interval = interval
        self.fields = fields
        self.filepath = filepath

        if rows is not None:
            self._rows = np.asarray(rows) - 1
        else:
            self._rows = np.arange(grid.shape[0] - 2)

        self._time = 0.0
        self._step_count = 0

    def run_one_step(self, dt: float | None = None) -> None:
        """Update the writer by a time step.

        Parameters
        ----------
        dt : float, optional
            The time step to update the component by.
        """
        dt = 1.0 if dt is None else float(dt)
        if self._step_count % self.interval == 0:
            to_netcdf(
                self.grid,
                self.filepath,
                mode="a",
                time=self._time,
                names={"node": self.fields},
                ids={
                    "row": self._rows,
                    "column": np.arange(self.grid.shape[1] - 2),
                },
            )
        self._time += dt
        self._step_count += 1

    @property
    def filepath(self) -> str | PathLike[str]:
        """Return the path to the output file."""
        return self._filepath

    @filepath.setter
    def filepath(self, new_val: str | PathLike[str]) -> None:
        if os.path.isfile(new_val) and not self._clobber:
            raise RuntimeError("file exists")
        try:
            os.remove(new_val)
        except OSError as err:
            if err.errno != errno.ENOENT:
                raise
        finally:
            self._filepath = str(new_val)

    @property
    def interval(self) -> int:
        """Return the interval for which output will be written."""
        return self._interval

    @interval.setter
    def interval(self, new_val: int) -> None:
        if new_val < 0:
            raise TypeError("interval not an integer")
        elif not isinstance(new_val, int):
            raise ValueError("non-positive interval")
        self._interval = new_val

    @property
    def fields(self) -> Iterable[str]:
        """Return the names of the fields to include in the output file."""
        return self._fields

    @fields.setter
    def fields(self, new_val: Iterable[str]) -> None:
        self._fields = tuple(new_val)
