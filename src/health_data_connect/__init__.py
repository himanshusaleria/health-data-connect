from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("health-data-connect")
except PackageNotFoundError:  # running from source before install
    __version__ = "0.0.0"
