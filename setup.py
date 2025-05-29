from setuptools import setup
from cefpygame.version import __version__

setup(
    version=__version__,
    keywords="pygame gamedev",
    packages=["cefpanda"],
    install_requires=[
        "pygame==1.9.6",
        "cefpython3==66.1",
    ],
    setup_requires=["pytest-runner"],
    tests_require=[
        "pytest",
        "pylint==2.3.*",
        "pytest-pylint",
    ],
)
