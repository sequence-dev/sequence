import pathlib

import numpy as np
import yaml


class TimeVaryingConfig:
    """A configuration dictionary that is able to change with time.

    Parameters
    ----------
    times : iterable of int
        Time keys for each dictionary.
    dicts : iterable of dict
        Dictionary to use at each time.

    Examples
    --------
    >>> from sequence.input_reader import TimeVaryingConfig
    >>> params = TimeVaryingConfig([0, 1], [dict(foo=0, bar=1), dict(foo=1)])
    >>> sorted(params.items())
    [(('bar',), 1), (('foo',), 0)]
    >>> params.update(1)
    {'foo': 1}
    >>> sorted(params.items())
    [(('bar',), 1), (('foo',), 1)]
    """

    def __init__(self, times, dicts):
        self._times = tuple(times)
        self._dicts = [_flatten_dict(d) for d in dicts]
        self._time = 0

        for d in self._dicts:
            for key, value in d.items():
                if isinstance(value, list):
                    d[key] = tuple(value)

        self._current = self._dicts[0]

    def items(self):
        return self._current.items()

    def as_dict(self):
        return _expand_dict(self._current)

    def __call__(self, time):
        d = {}
        for next_dict in self._dicts[: self._bisect_times(time)]:
            d.update(next_dict)
        return d

    def _bisect_times(self, time):
        return np.searchsorted(self._times, time, side="right")

    def diff(self, start, stop):
        start, stop = self(start), self(stop)
        return {k: stop[k] for k, _ in set(stop.items()) - set(start.items())}

    def update(self, inc):
        next_time = self._time + inc
        prev, next_ = self._bisect_times([self._time, next_time])
        if next_ > prev:
            self._current = self(next_time)
            diff = _expand_dict(self.diff(self._time, next_time))
        else:
            diff = {}

        self._time = next_time
        return diff

    def dump(self):
        docs = [_expand_dict(self._dicts[0])]
        for prev, next_ in zip(self._times[:-1], self._times[1:]):
            docs.append(_expand_dict(self.diff(prev, next_)))
        for time, doc in zip(self._times, docs):
            doc["_time"] = time
        return yaml.dump_all(docs, default_flow_style=False)

    @classmethod
    def from_files(cls, names, times=None):
        if times is None:
            times = list(range(len(names)))
        dicts = []
        for name in [pathlib.Path(n) for n in names]:
            with open(name, "r") as fp:
                dicts.append(yaml.safe_load(fp))
        return cls(times, dicts)

    @classmethod
    def from_file(cls, name):
        with open(name, "r") as fp:
            dicts = yaml.safe_load_all(fp)
            times = [d.pop("_time", index) for index, d in enumerate(dicts)]
        return cls(times, dicts)


def _flatten_dict(d, sep=None):
    """Flatten a dictionary so that each value has it's own key.

    Parameters
    ----------
    d : dict
        The dictionary to flatten.
    sep : str, optional
        Separator to use when creating flattened keys.

    Returns
    ------
    dict
        A flattened version of the dictionary.

    Examples
    --------
    >>> from sequence.input_reader import _flatten_dict
    >>> sorted(_flatten_dict({"foo": 0, "bar": 1}).items())
    [(('bar',), 1), (('foo',), 0)]
    >>> sorted(_flatten_dict({"foo": {"baz": 0, "foobar": "baz"}, "bar": 1}).items())
    [(('bar',), 1), (('foo', 'baz'), 0), (('foo', 'foobar'), 'baz')]
    >>> sorted(_flatten_dict(
    ...     {"foo": {"baz": 0, "foobar": "baz"}, "bar": 1}, sep=".").items()
    ... )
    [('bar', 1), ('foo.baz', 0), ('foo.foobar', 'baz')]
    """
    if sep is None:
        return {keys: value for keys, value in _walk_dict(d)}
    else:
        return {sep.join(keys): value for keys, value in _walk_dict(d)}


def _add_flattened_item(keys, value, base=None):
    expanded = {} if base is None else base
    parent, name = keys[:-1], keys[-1]

    level = expanded
    for k in parent:
        if k not in level:
            level[k] = dict()
        level = level[k]
    if isinstance(value, tuple):
        value = list(value)
    level[name] = value

    return base


def _expand_dict(flat_dict):
    expanded = dict()
    for key, value in flat_dict.items():
        _add_flattened_item(key, value, base=expanded)
    return expanded


def _walk_dict(indict, prev=None):
    """Walk the elements of a dictionary.

    Parameters
    ----------
    indict : dict
        The dictionary to walk.
    prev : dict, optional
        The parent dictionary, if any, that is being walked.

    Yields
    ------
    tuple of (*keys*, value)
        The first element of the tuple is itself a tuple of the keys that have
        been walked to get to this point, the second the value.

    Examples
    --------
    >>> from sequence.input_reader import _walk_dict
    >>> sorted(_walk_dict({"foo": 0, "bar": 1}))
    [(('bar',), 1), (('foo',), 0)]
    >>> sorted(_walk_dict({"foo": {"baz": 0}, "bar": 1}))
    [(('bar',), 1), (('foo', 'baz'), 0)]
    >>> sorted(_walk_dict({"foo": {"bar": {"baz": 0, "foo": "bar"}}, "bar": 1}))
    [(('bar',), 1), (('foo', 'bar', 'baz'), 0), (('foo', 'bar', 'foo'), 'bar')]
    """
    prev = tuple(prev) if prev else ()

    if isinstance(indict, dict):
        for key, value in indict.items():
            if isinstance(value, dict):
                for d in _walk_dict(value, prev + (key,)):
                    yield d
            elif isinstance(value, list) or isinstance(value, tuple):
                yield prev + (key,), value
            else:
                yield prev + (key,), value
    else:
        yield indict
