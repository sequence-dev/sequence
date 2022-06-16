import numpy as np
from landlab import Component
from scipy import interpolate


class SeaLevelTimeSeries(Component):

    _name = "Sea Level Changer"

    _time_units = "y"

    _unit_agnostic = True

    _info = {
        "sea_level__elevation": {
            "dtype": "float",
            "intent": "out",
            "optional": False,
            "units": "m",
            "mapping": "grid",
            "doc": "Sea level elevation",
        }
    }

    def __init__(self, grid, filepath, kind="linear", start=0.0, **kwds):
        """Generate sea level values.

        Parameters
        ----------
        grid: ModelGrid
            A landlab grid.
        filepath: str
            Name of csv-formatted sea-level file.
        kind: str, optional
            Kind of interpolation as a string (one of 'linear',
            'nearest', 'zero', 'slinear', 'quadratic', 'cubic').
            Default is 'linear'.
        """
        super().__init__(grid, **kwds)

        self._filepath = filepath
        self._kind = kind

        self._sea_level = SeaLevelTimeSeries._sea_level_interpolator(
            np.loadtxt(self._filepath, delimiter=","), kind=self._kind
        )
        self._time = start

    @staticmethod
    def _sea_level_interpolator(data, kind="linear"):
        return interpolate.interp1d(
            data[:, 0],
            data[:, 1],
            kind=kind,
            copy=True,
            assume_sorted=True,
            bounds_error=True,
        )

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, new_path):
        self._filepath = new_path
        self._sea_level = SeaLevelTimeSeries._sea_level_interpolator(
            np.loadtxt(self._filepath, delimiter=","), kind=self._kind
        )

    @property
    def time(self):
        return self._time

    def run_one_step(self, dt):
        self._time += dt
        self.grid.at_grid["sea_level__elevation"] = self._sea_level(self.time)


class SinusoidalSeaLevel(SeaLevelTimeSeries):
    def __init__(
        self,
        grid,
        wave_length=1.0,
        amplitude=1.0,
        phase=0.0,
        mean=0.0,
        start=0.0,
        linear=0.0,
        **kwds
    ):
        """Generate sea level values.

        Parameters
        ----------
        grid: ModelGrid
            A landlab grid.
        """
        wave_length /= 2.0 * np.pi
        super(SeaLevelTimeSeries, self).__init__(grid, **kwds)

        self._sea_level = (
            lambda time: (
                np.sin((time - phase) / wave_length)
                + 0.3 * np.sin((2 * (time - phase)) / wave_length)
            )
            * amplitude
            + mean
            + linear * time
        )

        self._time = start


def sea_level_type(dictionary):
    from .sea_level import sea_level_file

    sl_type = dictionary["sl_type"]
    if sl_type == "sinusoid":
        return sea_level_function(dictionary)
    else:
        sl_file_name = dictionary["sl_file_name"]
        return sea_level_file(sl_file_name, dictionary)


def sea_level_function(dictionary):
    # time is an array of x values (ex. arange(0,1000, pi/4))
    # amplitude is the amplitude of the sin function
    # phase is th phase shift
    # t is the title of the graph (String)
    # xt is the title of the x axis (string)
    # xy is the title of the y axis (STRING)
    # Function starts at 0 or P.
    # Fs is the period of the function. (10,000)
    phase = dictionary["sea_level_phase"]
    amplitude = dictionary["sea_level_amplitude"]
    slope = dictionary["sea_level_linear"]
    Fs = dictionary["sea_level_period"]
    start_time = dictionary["start_time"]
    run_duration = dictionary["run_duration"]
    dt = dictionary["dt"]

    time = np.arange(start_time, start_time + run_duration, dt)
    sl_array = (
        amplitude
        * (
            np.sin((2 * np.pi * (phase + time)) / Fs)
            + 0.3 * np.sin((2 * np.pi * (2 * phase + 2 * time)) / Fs)
        )
        + slope * time
    )
    return time, sl_array


def sea_level_file(filename, dictionary):
    """
    reading in the file above
    x is an array of x values (ex. x = arange(0, 10))
    y is an array of y values (ex. y = np.exp(x/2.0))
    start time (default should be 0)
    dt
    run duration

    Note: The array of x values can be pretermined to a set of
          values. Goes backwards so the start will be at -12500 years
          There will be a sea level array that stores these values
    """
    start_time = dictionary["start_time"]
    run_duration = dictionary["run_duration"]
    dt = dictionary["dt"]

    xes = []
    ys = []
    with open(filename) as f:
        for line in f:
            x, y = line.split()
            xes.append(x)
            ys.append(y)
    x = []
    for item in xes:
        x.append(float(item))
    y = []
    for item in ys:
        y.append(float(item))

    f = interpolate.interp1d(x, y, kind="cubic")
    times = np.arange(start_time, start_time + run_duration, dt)
    sl_array = f(times)
    return times, sl_array
