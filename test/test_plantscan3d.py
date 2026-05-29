from importlib.resources import files

from openalea.plantscan3d.processpoints import load_points


def test_load_points():
    datadir = files("openalea.plantscan3d.data.scans_example")
    points = load_points(str(datadir / "A3B4.asc"))
    assert len(points) > 1

