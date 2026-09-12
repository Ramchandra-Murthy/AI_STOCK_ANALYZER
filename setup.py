from setuptools import find_namespace_packages, setup

setup(
    name="ai_stock_analyzer",
    version="1.0.0",
    author="Ramchandra-Murthy",
    packages=find_namespace_packages(include=["backend*", "core*", "services*", "api*"]),
    install_requires=[
        "streamlit",
        "yfinance",
        "pandas",
        "numpy",
        "plotly",
        "scikit-learn",
        "pandas_ta",
        "python-dotenv",
        "pydantic",
    ],
    entry_points={
        "console_scripts": [
            "analyze-stock=main:main",
        ]
    },
    python_requires=">=3.13",
)
