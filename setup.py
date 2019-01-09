from setuptools import find_packages, setup

import versioneer

with open("README.rst") as readme_file:
    readme = readme_file.read()

requirements = []

setup_requirements = []

test_requirements = ["pytest"]

setup(
    author="Eric Hutton",
    author_email="mcflugen@gmail.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Python version of the Steckler Sequence model",
    install_requires=requirements,
    license="MIT license",
    include_package_data=True,
    keywords="sequence",
    name="sequence",
    packages=find_packages(include=["sequence"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/sequence-dev/sequence",
    version=versioneer.get_version(),
    entry_points={"console_scripts": ["sequence=sequence.sequence_model:main"]},
    cmdclass=versioneer.get_cmdclass(),
    zip_safe=False,
)
