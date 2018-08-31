import os

from landlab import Component
from landlab.bmi.bmi_bridge import TimeStepper
from landlab.io.netcdf import write_raster_netcdf


class OutputWriter(Component):
    def __init__(
        self, grid, filepath, interval=1, fields=None, clobber=False, clock=None
    ):
        super(OutputWriter, self).__init__(grid)

        self._clock = clock or TimeStepper()
        self._clobber = clobber
        self.interval = interval
        self.fields = fields
        self.filepath = filepath

        self._step_count = 0

    def run_one_step(self, dt=None):
        if self._step_count % self.interval == 0:
            write_raster_netcdf(
                self.filepath,
                self.grid,
                append=True,
                time=self._step_count,
                # time=self.clock.time,
                names=self.fields,
            )
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
        except FileNotFoundError:
            pass
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
