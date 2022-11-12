import os
from setuptools import setup, find_packages


def read_file(rel_path: str) -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path), "r", encoding="utf-8") as f:
        return f.read()


def get_version(rel_path: str) -> str:
    for line in read_file(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]

    raise RuntimeError("Unable to find version string.")


setup(
    name="serial_tool",
    url="https://github.com/damogranlabs/serial-tool",
    author="Domen Jurkovic",
    author_email="domen.jurkovic@damogranlabs.com",
    description="Serial Tool is a utility for developing, debugging and " "validating serial communication with PC.",
    long_description=read_file("README.md"),
    keywords=["serial tool", "UART", "serial", "RS232"],
    version=get_version("src/serial_tool/__init__.py"),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
    ],
    license="MIT license",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=["PyQt5", "aioserial", "pyserial"],
    include_package_data=False,
)
