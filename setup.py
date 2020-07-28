from setuptools import find_packages, setup

import versioneer


def read(filename):
    with open(filename, "r", encoding="utf-8") as fp:
        return fp.read()


long_description = u'\n\n'.join(
    [
        read('README.rst'),
        read('AUTHORS.rst'),
        read('CHANGES.rst'),
    ]
)


setup(
    author="Eric Hutton",
    author_email="mcflugen@gmail.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Python version of the Steckler Sequence model",
    long_description=long_description,
    install_requires=open("requirements.txt", "r").read().splitlines(),
    license="MIT license",
    include_package_data=True,
    keywords=["sequence", "landlab"],
    name="sequence",
    packages=find_packages(include=["sequence"]),
    test_suite="tests",
    url="https://github.com/sequence-dev/sequence",
    version=versioneer.get_version(),
    entry_points={"console_scripts": ["sequence=sequence.cli:sequence"]},
    cmdclass=versioneer.get_cmdclass(),
    zip_safe=False,
)
