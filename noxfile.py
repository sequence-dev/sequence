import os
import pathlib
import shutil

import nox


@nox.session
def tests(session: nox.Session) -> None:
    session.install("pytest")
    session.install(".[dev]")
    session.run("pytest", "--cov=sequence", "-vvv")
    session.run("coverage", "report", "--ignore-errors", "--show-missing")
    # "--fail-under=100",


@nox.session
def notebooks(session: nox.Session) -> None:
    session.install(".[dev,notebook]")
    session.run("pytest", "--nbmake", "notebooks/")


@nox.session
def cli(session: nox.Session) -> None:
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
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files")


@nox.session
def docs(session: nox.Session) -> None:
    session.install(".[doc]")

    session.chdir("docs")
    if os.path.exists("_build"):
        shutil.rmtree("_build")
        session.run("sphinx-apidoc", "--force", "-o", "api", "sequence", "tests")
        session.run("sphinx-build", "-b", "html", "-W", ".", "_build/html")
