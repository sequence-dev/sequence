from ._version import get_versions
from .output_writer import OutputWriter
from .submarine import SubmarineDiffuser

__all__ = ["OutputWriter", "SubmarineDiffuser"]


__version__ = get_versions()["version"]
del get_versions
