from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="troi",
    version="0.0.1pre",
    author="MetaBrainz Foundation",
    description="An empathetic music recommendation system pipeline",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/metabrainz/troi-recommendation-playground",
    install_requires=["click>=7", "ujson>=2", "requests>=2.24", "pylistenbrainz", "openpost"],
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    entry_points = {
        'console_scripts': ['troi=troi.cli:cli'],
    }
)
