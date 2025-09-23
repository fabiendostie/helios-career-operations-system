"""Setup configuration for Profile Ingestor service."""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="resume-extractor",
    version="1.0.0",
    description="Profile Ingestor Service - Resume data extraction and consolidation",
    author="Helios Career Operations System",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    python_requires=">=3.13.0",
    entry_points={
        "console_scripts": [
            "resume-extractor=resume_extractor.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
    ],
)
