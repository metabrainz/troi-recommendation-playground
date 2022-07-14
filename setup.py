from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

# read dependencies from requirements.txt skipping any comment lines
with open("requirements.txt", "r") as fh:
    requirements = [line for line in fh.read().splitlines() if not line.startswith("#")]


setup(
    name="troi",
    version="0.1.0",
    author="MetaBrainz Foundation",
    description="An empathetic music recommendation system pipeline",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/metabrainz/troi-recommendation-playground",
    install_requires=requirements,
    packages=find_packages(exclude=("patches",)),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points = {
        'console_scripts': ['troi=troi.cli:cli'],
    }
)
