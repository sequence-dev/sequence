import errno
import os

from landlab import Component
from landlab.bmi.bmi_bridge import TimeStepper

from .netcdf import to_netcdf


class OutputWriter(Component):

    """Write output to a netcdf file."""

    def __init__(
        self,
        grid,
        filepath=None,
        interval=1,
        fields=None,
        clobber=False,
        clock=None,
        rows=None,
    ):
        if filepath is None:
            raise ValueError("filepath must be provided")

        super().__init__(grid)

        self._clock = clock or TimeStepper()
        self._clobber = clobber
        self.interval = interval
        self.fields = fields
        self.filepath = filepath

        if rows is not None:
            self._nodes = grid.nodes[(rows,)].flatten()
        else:
            self._nodes = None

        self._time = 0.0
        self._step_count = 0

    def run_one_step(self, dt=None):
        dt = 1.0 if dt is None else float(dt)
        if self._step_count % self.interval == 0:
            to_netcdf(
                self.grid,
                self.filepath,
                mode="a",
                time=self._time,
                names={"node": self.fields},
                ids={"node": self._nodes},
            )
        self._time += dt
        self._step_count += 1

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, new_val):
        if os.path.isfile(new_val) and not self._clobber:
            raise RuntimeError("file exists")
        try:
            os.remove(new_val)
        except OSError as err:
            if err.errno != errno.ENOENT:
                raise
        finally:
            self._filepath = new_val

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, new_val):
        if new_val < 0:
            raise TypeError("interval not an integer")
        elif not isinstance(new_val, int):
            raise ValueError("non-positive interval")
        self._interval = new_val

    @property
    def fields(self):
        return self._fields

    @fields.setter
    def fields(self, new_val):
        if new_val is None:
            self._fields = None
        else:
            self._fields = tuple(new_val)
