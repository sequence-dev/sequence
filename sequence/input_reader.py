import inspect
import pathlib
import warnings

import numpy as np
import tomlkit as toml
import yaml


def load_config(stream, fmt=None):
    if fmt is None and isinstance(stream, (str, pathlib.Path)):
        fmt = pathlib.Path(stream).suffix[1:]

    loader = TimeVaryingConfig.get_loader(fmt)

    if isinstance(stream, (str, pathlib.Path)):
        with open(stream) as fp:
            times_and_params = loader(fp)
    else:
        times_and_params = loader(stream)

    if len(times_and_params) == 1:
        return times_and_params[0][1]
    else:
        return times_and_params


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

    def dump(self, fmt="toml"):
        docs = [_expand_dict(self._dicts[0])]
        for prev, next_ in zip(self._times[:-1], self._times[1:]):
            docs.append(_expand_dict(self.diff(prev, next_)))
        for time, doc in zip(self._times, docs):
            doc["_time"] = time

        if fmt == "toml":
            return toml.dumps(dict(sequence=docs))
        elif fmt == "yaml":
            return yaml.dump(docs, default_flow_style=False)
        else:
            raise ValueError(f"unrecognized format: {fmt}")

    @classmethod
    def from_files(cls, names, times=None):
        dicts = []
        for name in [pathlib.Path(n) for n in names]:
            with open(name) as fp:
                loader = TimeVaryingConfig.get_loader(name.suffix[1:])
                dicts.extend([p for _, p in loader(fp)])
        if times is None:
            times = list(range(len(dicts)))
        return cls(times, dicts)

    @classmethod
    def from_file(cls, name, fmt=None):
        filepath = pathlib.Path(name)
        if fmt is None:
            fmt = filepath.suffix[1:]
        try:
            loader = getattr(cls, f"load_{fmt}")
        except AttributeError:
            raise ValueError(f"unrecognized format: {fmt}")

        with open(name) as fp:
            times_and_params = loader(fp)
        return cls(*zip(*times_and_params))

    @staticmethod
    def load_yaml(stream):
        doc = yaml.safe_load_all(stream)
        params = []
        for d in doc:
            if isinstance(d, list):
                params.extend(d)
            else:
                params.append(d)
        return [(d.pop("_time", idx), d) for idx, d in enumerate(params)]

    @staticmethod
    def load_toml(stream):
        def _tomlkit_to_popo(d):
            try:
                result = getattr(d, "value")
            except AttributeError:
                result = d

            if isinstance(result, list):
                result = [_tomlkit_to_popo(x) for x in result]
            elif isinstance(result, dict):
                result = {
                    _tomlkit_to_popo(key): _tomlkit_to_popo(val)
                    for key, val in result.items()
                }
            elif isinstance(result, toml.items.Integer):
                result = int(result)
            elif isinstance(result, toml.items.Float):
                result = float(result)
            elif isinstance(result, (toml.items.String, str)):
                result = str(result)
            elif isinstance(result, (toml.items.Bool, bool)):
                result = bool(result)
            else:
                warnings.warn(
                    "unexpected type ({!r}) encountered when converting toml to a dict".format(
                        result.__class__.__name__
                    )
                )

            return result

        doc = toml.parse(stream.read()).pop("sequence")
        if isinstance(doc, list):
            params = [_tomlkit_to_popo(table) for table in doc]
        else:
            params = [_tomlkit_to_popo(doc)]

        return [(d.pop("_time", idx), d) for idx, d in enumerate(params)]

    @staticmethod
    def get_loader(fmt):
        try:
            return getattr(TimeVaryingConfig, f"load_{fmt}")
        except AttributeError:
            fmts = set(TimeVaryingConfig.get_supported_formats())
            raise ValueError(f"unrecognized format: {fmt!r} (not on of {fmts!r})")

    @staticmethod
    def get_supported_formats():
        return [
            name.split("_", maxsplit=1)[1]
            for name, _ in inspect.getmembers(TimeVaryingConfig, inspect.isfunction)
            if name.startswith("load_")
        ]


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
                yield from _walk_dict(value, prev + (key,))
            elif isinstance(value, list) or isinstance(value, tuple):
                yield prev + (key,), value
            else:
                yield prev + (key,), value
    else:
        yield indict
