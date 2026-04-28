from setuptools import find_packages, setup


setup(
    name="jinguzhou",
    version="0.2.1",
    description="A model-agnostic safety gateway, policy engine, and audit layer for LLM applications.",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        "fastapi>=0.115,<1.0",
        "httpx>=0.28,<1.0",
        "pydantic>=2.7,<3.0",
        "pyyaml>=6.0,<7.0",
        "typer>=0.12,<1.0",
        "uvicorn>=0.30,<1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0,<9.0",
        ],
        "postgres": [
            "psycopg[binary]>=3.2,<4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "jinguzhou=jinguzhou.cli:app",
        ]
    },
)
