import setuptools

with open("README.md", encoding="utf-8") as file:
    long_description = file.read()

setuptools.setup(
    name="bibfish",
    use_scm_version={
        "write_to": "bibfish/_version.py",
        "write_to_template": '__version__ = "{version}"',
        "fallback_version": "???",
    },
    author="Jon Carr",
    author_email="jcarr@sissa.it",
    description="Extract entries from a .bib file that are cited in a .tex file",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jwcarr/bibfish",
    license="MIT",
    packages=["bibfish"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Text Processing :: Markup :: LaTeX",
    ],
    python_requires=">=3.6",
    setup_requires=["setuptools_scm"],
    entry_points={
        "console_scripts": [
            "bibfish = bibfish:cli",
        ],
    },
)
