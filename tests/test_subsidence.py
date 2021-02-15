import pytest
from numpy.testing import assert_array_equal

from sequence.subsidence import SubsidenceTimeSeries
from landlab import RasterModelGrid


def test_bad_filepath(tmpdir):
    grid = RasterModelGrid((3, 5))
    grid.add_full("bedrock_surface__elevation", 0.0, at="node")
    grid.add_full("topographic__elevation", 0.0, at="node")

    with pytest.raises(ValueError):
        SubsidenceTimeSeries(grid)

    with tmpdir.as_cwd():
        with pytest.raises(OSError):
            SubsidenceTimeSeries(grid, filepath="missing-file.csv")


def test_constant_subsidence(tmpdir):
    grid = RasterModelGrid((3, 5))
    grid.add_full("bedrock_surface__elevation", 0.0, at="node")
    grid.add_full("topographic__elevation", 0.0, at="node")

    with tmpdir.as_cwd():
        with open("subsidence.csv", "w") as fp:
            fp.write("0.0,1.0\n5.0,1.0")
        subsidence = SubsidenceTimeSeries(grid, filepath="subsidence.csv")
        assert_array_equal(grid.at_node["bedrock_surface__increment_of_elevation"], 1.0)

        subsidence.run_one_step(dt=1.0)
        assert_array_equal(grid.at_node["bedrock_surface__elevation"], 1.0)

        subsidence.run_one_step(dt=1.0)
        assert_array_equal(grid.at_node["bedrock_surface__elevation"], 2.0)


def test_linear_subsidence(tmpdir):
    grid = RasterModelGrid((3, 5))
    grid.add_full("bedrock_surface__elevation", 0.0, at="node")
    grid.add_full("topographic__elevation", 0.0, at="node")

    with tmpdir.as_cwd():
        with open("subsidence.csv", "w") as fp:
            fp.write("0.0,0.0\n4.0,40.0")
        subsidence = SubsidenceTimeSeries(grid, filepath="subsidence.csv")
        assert_array_equal(
            grid.at_node["bedrock_surface__increment_of_elevation"].reshape((3, 5)),
            [
                [0.0, 10.0, 20.0, 30.0, 40.0],
                [0.0, 10.0, 20.0, 30.0, 40.0],
                [0.0, 10.0, 20.0, 30.0, 40.0],
            ],
        )

        subsidence.run_one_step(dt=1.0)
        assert_array_equal(
            grid.at_node["bedrock_surface__elevation"].reshape((3, 5)),
            [
                [0.0, 10.0, 20.0, 30.0, 40.0],
                [0.0, 10.0, 20.0, 30.0, 40.0],
                [0.0, 10.0, 20.0, 30.0, 40.0],
            ],
        )

        subsidence.run_one_step(dt=1.0)
        assert_array_equal(
            grid.at_node["bedrock_surface__elevation"].reshape((3, 5)),
            [
                [0.0, 20.0, 40.0, 60.0, 80.0],
                [0.0, 20.0, 40.0, 60.0, 80.0],
                [0.0, 20.0, 40.0, 60.0, 80.0],
            ],
        )


def test_set_subsidence_file(tmpdir):
    grid = RasterModelGrid((3, 5))
    grid.add_full("bedrock_surface__elevation", 0.0, at="node")
    grid.add_full("topographic__elevation", 0.0, at="node")

    with tmpdir.as_cwd():
        with open("subsidence-0.csv", "w") as fp:
            fp.write("0.0,10.0\n4.0,10.0")
        subsidence = SubsidenceTimeSeries(grid, filepath="subsidence-0.csv")
        assert_array_equal(
            grid.at_node["bedrock_surface__increment_of_elevation"], 10.0
        )

        subsidence.run_one_step(dt=1.0)
        assert_array_equal(grid.at_node["bedrock_surface__elevation"], 10.0)

        with open("subsidence-1.csv", "w") as fp:
            fp.write("0.0,-100.0\n4.0,-100.0")
        subsidence.filepath = "subsidence-1.csv"
        assert_array_equal(
            grid.at_node["bedrock_surface__increment_of_elevation"], -100.0
        )

        subsidence.run_one_step(dt=1.0)
        assert_array_equal(grid.at_node["bedrock_surface__elevation"], -90.0)
