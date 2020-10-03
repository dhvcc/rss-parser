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
    project_urls={
        "Homepage": SITE_URL,
        "Source": REPO_URL,
        "Tracker": f"{REPO_URL}/issues",
    },
    keywords=["python", "cli", "rss", "parser"],
    classifiers=[
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ]
)
