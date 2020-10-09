from setuptools import setup, find_packages
import os


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


pkg_info = {}

with open("rss_parser/__version__.py") as f:
    """Executing init to set __version__ value"""
    exec(f.read(), pkg_info)

REPO_URL = "https://github.com/dhvcc/rss-parser"
SITE_URL = "https://dhvcc.github.io/rss-parser"

setup(
    name="rss-parser",
    version=pkg_info["__version__"],
    author=pkg_info["__author__"],
    author_email=pkg_info["__email__"],
    description="Pythonic rss parser",
    url=REPO_URL,
    license=pkg_info["__license__"],
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "bs4==0.0.1",
        "pydantic==1.6.1",
        "lxml==4.5.2",
        "requests==2.24.0",
    ],
    project_urls={
        "Homepage": SITE_URL,
        "Source": REPO_URL,
        "Tracker": f"{REPO_URL}/issues",
    },
    keywords=[
        "python", "python3", "cli",
        "rss", "parser", "scraper",
        "mit", "mit-license",
        "typed", "typed-python"
    ],
    classifiers=[
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 5 - Production/Stable",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: XML",
        "Typing :: Typed",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ]
)
