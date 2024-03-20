bibfish 0.3 - 2024-03-20
========================

Added
-----

- Support for crossrefs. Cross-referenced Bibtex entries will be extracted automatically and placed in the output bib file.

- New `drop-fields` option, which allows you to drop Bibtext fields in the output bib file (e.g., abstracts, filenames, notes, and other unwanted data).

Changed
-------

- If multiple master files are specified and there are duplicate citekeys, earlier bib files will now take priority over later files.

- Bibfish is now fixed to version 1.4.1 of Bibtexparser to avoid potential issues with the upcoming version 2 release.


bibfish 0.2.1 - 2023-10-10
==========================

Fixed
-----

- Bibfish will now explicitly ignore bracketed text between a cite command and the citekey to avoid issues in which bracketed text might contain braces that are erroneously captured as the citekey, e.g., `\cite[some \textit{italic} text]{myCiteKey}`.


bibfish 0.2.0 - 2023-01-22
==========================

Added
-----

- bibfish can now handle multiple bibtex databases with the --bib option, which may be useful if you maintain separate databases.

Changed
-------

- bibfish now uses bibtexparser. This permits more robust parsing of bibtex files and produces more consistent bibtex output.


bibfish 0.1.0 - 2023-01-06
==========================

Added
-----

- Added support for nested input files.


bibfish 0.0.5 - 2022-10-07
==========================

Changed
-------

- Ignore empty cite commands.


bibfish 0.0.4 - 2022-07-06
==========================

Fixed
-----

- Fixed bug where bibtex a for closely named citekeys (e.g. Warner2019 and Warner2019a) would not be extracted correctly. This requires that the citekey in the bibtex entry is directly followed by a comma.


bibfish 0.0.3 - 2022-01-30
==========================

Fixed
-----

- Fixed bug in DOI shortening.


bibfish 0.0.2 - 2021-01-31
==========================

Changed
-------

- bibfish no longer overwrites the local .bib file if it already exists.
