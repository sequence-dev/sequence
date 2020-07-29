import pkg_resources

from .output_writer import OutputWriter
from .submarine import SubmarineDiffuser

__version__ = pkg_resources.get_distribution("sequence").version
__all__ = ["OutputWriter", "SubmarineDiffuser"]
