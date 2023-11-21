import os
import pathlib
import shutil
from itertools import chain

import nox

PYTHON_VERSION = "3.12"
PROJECT = "sequence"
ROOT = pathlib.Path(__file__).parent

FOLDER = {
    "build": ROOT / "build",
    "docs": ROOT / "docs",
    "docs_generated": ROOT / "docs" / "generated",
    "docs_ref": ROOT / "docs" / "reference",
    "notebooks": ROOT / "docs" / "tutorials" / "notebooks",
    "root": ROOT,
}


@nox.session(python=PYTHON_VERSION, venv_backend="conda")
def test(session: nox.Session) -> None:
    """Run the tests."""
    session.install("-r", "requirements-testing.in")
    session.install(".")

    args = session.posargs or ["-n", "auto", "--cov", PROJECT, "-vvv"]
    if "CI" in os.environ:
        args.append("--cov-report=xml:$(pwd)/coverage.xml")
    session.run("pytest", *args)


@nox.session(name="test-notebooks", python=PYTHON_VERSION, venv_backend="conda")
def test_notebooks(session: nox.Session) -> None:
    """Run the notebooks."""
    session.install("nbmake")
    session.install("-r", "requirements-testing.in")
    session.install("-r", str(FOLDER["notebooks"] / "requirements.in"))
    session.install(".")

    session.run("pytest", "--nbmake", str(FOLDER["notebooks"]))


@nox.session(name="test-cli", python=PYTHON_VERSION, venv_backend="conda")
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
    session.install("-r", str(FOLDER["docs"] / "requirements.in"))
    session.install("-e", ".")

    clean_docs(session)
    build_generated_docs(session)

    FOLDER["build"].mkdir(exist_ok=True)
    with session.chdir(FOLDER["root"]):
        session.run(
            "sphinx-build",
            "-b",
            "html",
            "-W",
            "--keep-going",
            "docs",
            "build/html",
        )


@nox.session(name="build-generated-docs", reuse_venv=True)
def build_generated_docs(session: nox.Session) -> None:
    """Build auto-generated files used by the docs."""
    FOLDER["docs_generated"].mkdir(exist_ok=True)

    session.install("sphinx")
    session.install("-e", ".")

    session.run("sequence", "--version")

    session.log("generating example sequence input files")
    with session.chdir(FOLDER["docs_generated"]):
        for fname in [
            "bathymetry.csv",
            "sealevel.csv",
            "sequence.toml",
            "subsidence.csv",
        ]:
            generated = f"_{fname}"
            with open(generated, "wb") as fp:
                session.log(f"Creating file: {generated}")
                session.run("sequence", "generate", fname, stdout=fp)

    with session.chdir(FOLDER["root"]):
        session.log(f"generating api docs in {FOLDER['docs_generated']}")
        session.run(
            "sphinx-apidoc",
            "-e",
            "-force",
            "--no-toc",
            "--module-first",
            "-o",
            str(FOLDER["docs_generated"]),
            "sequence",
        )


@nox.session(name="live-docs", reuse_venv=True)
def live_docs(session: nox.Session) -> None:
    build_generated_docs(session)

    session.install("sphinx-autobuild")
    session.install(".[doc]")
    session.run(
        "sphinx-autobuild",
        "-b",
        "dirhtml",
        str(FOLDER["docs"]),
        str(FOLDER["build"] / "html"),
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
        "python",
        "setup.py",
        "bdist_wheel",
        "sdist",
        "--dist-dir",
        str(FOLDER["build"] / "wheelhouse"),
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
    session.run("twine", "check", str(FOLDER["build"] / "wheelhouse" / "*"))
    session.run(
        "twine",
        "upload",
        "--skip-existing",
        "--repository-url",
        "https://test.pypi.org/legacy/",
        str(FOLDER["build"] / "wheelhouse" / "*.tar.gz"),
    )


@nox.session
def publish_pypi(session):
    """Publish wheelhouse/* to PyPI."""
    session.run("twine", "check", str(FOLDER["build"] / "wheelhouse" / "*"))
    session.run(
        "twine",
        "upload",
        "--skip-existing",
        str(FOLDER["build"] / "wheelhouse" / "*.tar.gz"),
    )


@nox.session(python=False)
def clean(session):
    """Remove all .venv's, build files and caches in the directory."""
    shutil.rmtree(FOLDER["build"], ignore_errors=True)
    shutil.rmtree(FOLDER["build"] / "wheelhouse", ignore_errors=True)
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
    if (FOLDER["build"] / "html").is_dir():
        shutil.rmtree(FOLDER["build"] / "html")

    for p in chain(
        FOLDER["docs_generated"].rglob("sequence*.rst"),
        FOLDER["docs_generated"].rglob("_*"),
    ):
        p.unlink()
