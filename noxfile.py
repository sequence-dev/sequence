import os
import pathlib
import shutil
from itertools import chain

import nox

PROJECT = "sequence"
ROOT = pathlib.Path(__file__).parent


@nox.session
def test(session: nox.Session) -> None:
    """Run the tests."""
    session.install("-r", "requirements-testing.in")

    args = session.posargs or ["-n", "auto", "--cov", PROJECT, "-vvv"]
    if "CI" in os.environ:
        args.append("--cov-report=xml:$(pwd)/coverage.xml")
    session.run("pytest", *args)


@nox.session(name="test-notebooks")
def test_notebooks(session: nox.Session) -> None:
    """Run the notebooks."""
    session.install("nbmake")
    session.install("-r", "requirements-testing.in")
    session.install("-r", "notebooks/requirements.in")

    session.run("pytest", "--nbmake", "notebooks/")


@nox.session(name="test-cli")
def test_cli(session: nox.Session) -> None:
    """Test the command line interface."""
    session.install(".")
    session.run("sequence", "--version")
    session.run("sequence", "--help")
    session.run("sequence", "generate", "--help")
    session.run("sequence", "plot", "--help")
    session.run("sequence", "run", "--help")
    session.run("sequence", "setup", "--help")

    INFILES = ("bathymetry.csv", "sealevel.csv", "sequence.toml", "subsidence.csv")

    for infile in INFILES:
        session.run("sequence", "generate", infile)
    session.run("sequence", "generate", "sequence.yaml")

    tmp_dir = pathlib.Path(session.create_tmp()).absolute()
    session.cd(tmp_dir)
    for infile in INFILES:
        (tmp_dir / infile).unlink(missing_ok=True)

    session.run("sequence", "setup")
    for infile in INFILES:
        assert pathlib.Path(infile).is_file()
    assert not pathlib.Path("sequence.yaml").exists()


@nox.session
def lint(session: nox.Session) -> None:
    """Look for lint."""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files", "--verbose")


@nox.session
def towncrier(session: nox.Session) -> None:
    """Check that there is a news fragment."""
    session.install("towncrier")
    session.run("towncrier", "check", "--compare-with", "origin/develop")


@nox.session(name="build-docs", reuse_venv=True)
def build_docs(session: nox.Session) -> None:
    """Build the docs."""
    with session.chdir(ROOT):
        session.install("-r", "docs/requirements.in")

    clean_docs(session)

    with session.chdir(ROOT):
        session.run(
            "sphinx-apidoc",
            "-e",
            "-force",
            "--no-toc",
            "--module-first",
            # "--templatedir",
            # "docs/_templates",
            "-o",
            "docs/api",
            "sequence",
        )
        session.run(
            "sphinx-build",
            "-b",
            "html",
            "-W",
            "docs",
            "build/html",
        )


@nox.session(name="live-docs", reuse_venv=True)
def live_docs(session: nox.Session) -> None:
    session.install("sphinx-autobuild")
    session.install(".[doc]")
    session.run(
        "sphinx-apidoc",
        "-e",
        "-force",
        "--no-toc",
        "--module-first",
        "--templatedir",
        "docs/_templates",
        "-o",
        "docs/api",
        "sequence",
    )
    session.run(
        "sphinx-autobuild",
        "-b",
        "dirhtml",
        "docs",
        "build/html",
        "--open-browser",
    )


@nox.session
def build(session: nox.Session) -> None:
    """Build sdist and wheel dists."""
    session.install("pip")
    session.install("wheel")
    session.install("setuptools")
    session.run("python", "--version")
    session.run("pip", "--version")
    session.run(
        "python", "setup.py", "bdist_wheel", "sdist", "--dist-dir", "./wheelhouse"
    )


@nox.session
def release(session):
    """Tag, build and publish a new release to PyPI."""
    session.install("zest.releaser[recommended]")
    session.install("zestreleaser.towncrier")
    session.run("fullrelease")


@nox.session
def publish_testpypi(session):
    """Publish wheelhouse/* to TestPyPI."""
    session.run("twine", "check", "wheelhouse/*")
    session.run(
        "twine",
        "upload",
        "--skip-existing",
        "--repository-url",
        "https://test.pypi.org/legacy/",
        "wheelhouse/*.tar.gz",
    )


@nox.session
def publish_pypi(session):
    """Publish wheelhouse/* to PyPI."""
    session.run("twine", "check", "wheelhouse/*")
    session.run(
        "twine",
        "upload",
        "--skip-existing",
        "wheelhouse/*.tar.gz",
    )


@nox.session(python=False)
def clean(session):
    """Remove all .venv's, build files and caches in the directory."""
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("wheelhouse", ignore_errors=True)
    shutil.rmtree(f"{PROJECT}.egg-info", ignore_errors=True)
    shutil.rmtree(".pytest_cache", ignore_errors=True)
    shutil.rmtree(".venv", ignore_errors=True)
    for p in chain(ROOT.rglob("*.py[co]"), ROOT.rglob("__pycache__")):
        if p.is_dir():
            p.rmdir()
        else:
            p.unlink()


@nox.session(python=False, name="clean-docs")
def clean_docs(session: nox.Session) -> None:
    """Clean up the docs folder."""
    with session.chdir(ROOT / "build"):
        if os.path.exists("html"):
            shutil.rmtree("html")

    with session.chdir(ROOT / "docs"):
        for p in pathlib.Path("api").rglob("sequence*.rst"):
            p.unlink()
