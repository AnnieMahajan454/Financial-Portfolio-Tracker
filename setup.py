"""
Financial Portfolio Tracker Setup Script

This script provides utilities for setting up and managing the
Financial Portfolio Tracker project.
"""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="financial-portfolio-tracker",
    version="1.0.0",
    author="Annie Mahajan",
    author_email="annie.mahajan@example.com",
    description="A comprehensive Python-based portfolio tracking system with real-time data integration, advanced risk analytics, and Power BI dashboard capabilities.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AnnieMahajan454/Financial-Portfolio-Tracker",
    project_urls={
        "Bug Tracker": "https://github.com/AnnieMahajan454/Financial-Portfolio-Tracker/issues",
        "Documentation": "https://github.com/AnnieMahajan454/Financial-Portfolio-Tracker#readme",
        "Source Code": "https://github.com/AnnieMahajan454/Financial-Portfolio-Tracker",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "visualization": [
            "matplotlib>=3.6.0",
            "seaborn>=0.12.0",
            "plotly>=5.15.0",
        ],
        "excel": [
            "openpyxl>=3.1.0",
            "xlsxwriter>=3.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "portfolio-tracker=portfolio_tracker.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.json", "*.sql"],
    },
    zip_safe=False,
    keywords="portfolio finance risk-analysis powerbi dashboard investment tracking",
)
