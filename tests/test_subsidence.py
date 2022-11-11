import pytest
from numpy.testing import assert_array_equal

from sequence import SequenceModelGrid
from sequence.subsidence import SubsidenceTimeSeries


def test_bad_filepath(tmpdir):
    grid = SequenceModelGrid(5)

    with pytest.raises(TypeError):
        SubsidenceTimeSeries(grid)

    with tmpdir.as_cwd():
        with pytest.raises(OSError):
            SubsidenceTimeSeries(grid, filepath="missing-file.csv")


def test_time_step(tmpdir):
    grid = SequenceModelGrid(5, spacing=1.0)

    with tmpdir.as_cwd():
        with open("subsidence.csv", "w") as fp:
            fp.write("0.0,1.0\n5.0,1.0")
        subsidence = SubsidenceTimeSeries(grid, filepath="subsidence.csv")
        assert_array_equal(subsidence.subsidence_rate, 1.0)
        assert_array_equal(grid.at_node["bedrock_surface__increment_of_elevation"], 0.0)

        subsidence.run_one_step(dt=1.0)
        assert_array_equal(subsidence.subsidence_rate, 1.0)
        assert_array_equal(
            grid.get_profile("bedrock_surface__increment_of_elevation"), 1.0
        )

        grid.at_node["bedrock_surface__increment_of_elevation"][:] = 0.0
        subsidence.run_one_step(dt=2.0)
        assert_array_equal(
            grid.get_profile("bedrock_surface__increment_of_elevation"), 2.0
        )


def test_constant_subsidence(tmpdir):
    grid = SequenceModelGrid(5, spacing=1.0)

    with tmpdir.as_cwd():
        with open("subsidence.csv", "w") as fp:
            fp.write("0.0,1.0\n5.0,1.0")
        subsidence = SubsidenceTimeSeries(grid, filepath="subsidence.csv")
        assert_array_equal(grid.at_node["bedrock_surface__increment_of_elevation"], 0.0)

        subsidence.run_one_step(dt=1.0)
        assert_array_equal(
            grid.get_profile("bedrock_surface__increment_of_elevation"), 1.0
        )

        grid.at_node["bedrock_surface__increment_of_elevation"][:] = 0.0
        subsidence.run_one_step(dt=1.0)
        assert_array_equal(
            grid.get_profile("bedrock_surface__increment_of_elevation"), 1.0
        )


def test_linear_subsidence(tmpdir):
    grid = SequenceModelGrid(5, spacing=1.0)

    with tmpdir.as_cwd():
        with open("subsidence.csv", "w") as fp:
            fp.write("0.0,0.0\n4.0,40.0")
        subsidence = SubsidenceTimeSeries(grid, filepath="subsidence.csv")
        assert_array_equal(subsidence.subsidence_rate, [0.0, 10.0, 20.0, 30.0, 40.0])
        assert_array_equal(grid.at_node["bedrock_surface__increment_of_elevation"], 0.0)

        grid.at_node["bedrock_surface__increment_of_elevation"][:] = 0.0
        subsidence.run_one_step(dt=1.0)
        assert_array_equal(
            grid.get_profile("bedrock_surface__increment_of_elevation"),
            [0.0, 10.0, 20.0, 30.0, 40.0],
        )


def test_add_to_existing_subsidence(tmpdir):
    grid = SequenceModelGrid(5, spacing=1.0)
    grid.add_ones("bedrock_surface__increment_of_elevation", at="node")

    with tmpdir.as_cwd():
        with open("subsidence.csv", "w") as fp:
            fp.write("0.0,0.0\n4.0,40.0")
        subsidence = SubsidenceTimeSeries(grid, filepath="subsidence.csv")
        assert_array_equal(subsidence.subsidence_rate, [0.0, 10.0, 20.0, 30.0, 40.0])
        assert_array_equal(grid.at_node["bedrock_surface__increment_of_elevation"], 1.0)

        subsidence.run_one_step(dt=1.0)
        assert_array_equal(
            grid.get_profile("bedrock_surface__increment_of_elevation"),
            [1.0, 11.0, 21.0, 31.0, 41.0],
        )


def test_set_subsidence_file(tmpdir):
    grid = SequenceModelGrid(5, spacing=1.0)

    with tmpdir.as_cwd():
        with open("subsidence-0.csv", "w") as fp:
            fp.write("0.0,10.0\n4.0,10.0")
        with open("subsidence-1.csv", "w") as fp:
            fp.write("0.0,-100.0\n4.0,-100.0")

        subsidence = SubsidenceTimeSeries(grid, filepath="subsidence-0.csv")
        assert_array_equal(subsidence.subsidence_rate, 10.0)

        subsidence.run_one_step(dt=1.0)
        assert_array_equal(
            grid.get_profile("bedrock_surface__increment_of_elevation"), 10.0
        )

        grid.at_node["bedrock_surface__increment_of_elevation"][:] = 0.0
        subsidence.filepath = "subsidence-1.csv"
        assert_array_equal(subsidence.subsidence_rate, -100.0)

        subsidence.run_one_step(dt=1.0)
        assert_array_equal(
            grid.get_profile("bedrock_surface__increment_of_elevation"), -100
        )
