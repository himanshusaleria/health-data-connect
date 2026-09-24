import importlib


def test_package_imports_and_has_version():
    pkg = importlib.import_module("health_data_connect")
    assert isinstance(pkg.__version__, str)
    assert pkg.__version__
