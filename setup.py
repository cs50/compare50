from setuptools import setup

setup(
    author="CS50",
    author_email="sysadmins@cs50.harvard.edu",
    classifiers=[
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3.6",
        "Topic :: Education",
        "Topic :: Utilities"
    ],
    license="GPLv3",
    description="This is compare50, with which you can compare files for similarities.",
    install_requires=["attrs", "astropy", "numpy", "patool", "pygments"],
    keywords=["compare", "compare50"],
    name="compare50",
    python_requires=">=3.5",
    packages=["compare50"],
    scripts=["bin/compare50"],
    url="https://github.com/cs50/compare50",
    version="1.0.0"
)
