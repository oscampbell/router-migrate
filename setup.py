from setuptools import setup, find_packages

setup(
    name="router-migrate",
    version="0.1.0",
    description="Universal Router Configuration Migration Tool",
    author="Oliver",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "router-migrate=router_migrate.cli:main",
        ],
    },
    python_requires=">=3.8",
)
