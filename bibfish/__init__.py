from os.path import isfile
import argparse
import json
import re
import urllib.request

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase

try:
    from ._version import __version__
except ImportError:
    __version__ = "???"


def extract_citekeys(manuscript_file, cite_commands):
    """
    Search manuscript_file for any cite commands and return the citekeys they
    make reference to. If the manuscript has any nested files (through input,
    import, or include), these will be resursively expanded.
    """
    if len(cite_commands) == 0:
        return []
    with open(manuscript_file, "r") as file:
        manuscript = file.read()
    citekeys = []
    try:
        manuscript = manuscript.split(r"\begin{document}")[1]
    except IndexError:
        pass
    for nestfile in find_imported_files(manuscript):
        try:
            citekeys += extract_citekeys(nestfile, cite_commands)
        except FileNotFoundError:
            pass
    citations = re.findall(
        r"\\(" + "|".join(cite_commands) + r").*?\{(.*?)\}", manuscript
    )
    for citation in citations:
        for key in citation[1].replace(" ", "").split(","):
            if key:
                citekeys.append(key)
    return list(set(citekeys))


def find_imported_files(manuscript):
    """
    Search a manuscript file for input, import, and include, and return any
    filenames found, so that these can be resursively expanded. The filename
    may have a .tex extension or no extension.
    """
    includeinputfiles = re.findall(r"\\(include|input).*?\{(.*?)\}", manuscript)
    importfiles = re.findall(r"\\import.*?\{(.*?)\}.*?\{(.*?)\}", manuscript)
    found_filenames = []
    filenames = []
    for inputfile in includeinputfiles:
        if inputfile[1]:
            found_filenames.append(inputfile[1])
    for inputfile in importfiles:
        if inputfile[1]:
            found_filenames.append(inputfile[0] + inputfile[1])
    for filename in found_filenames:
        if "." in filename:
            if filename[-4:] == ".tex":
                filenames.append(filename)
        else:
            filenames.append(filename + ".tex")
    return filenames


def parse_bibtex_entries(bib_files: list, citekeys: list) -> BibDatabase:
    """
    Return a bibtexparser.bibdatabase.BibDatabase which contains only the
    entries in *bib_files* which match *citekeys*.
    """
    out_db = BibDatabase()
    for p in bib_files:
        with open(p) as f:
            bib_database = bibtexparser.load(
                f,
                parser=bibtexparser.bparser.BibTexParser(
                    interpolate_strings=True,
                    ignore_nonstandard_types=False,
                ),
            )
            out_db = update_bibdatabase(out_db, bib_database)

    out_dict = out_db.entries_dict
    entries = list()
    for k in citekeys:
        if k in out_dict.keys():
            entries.append(out_dict[k])
        else:
            print(f"-> Citekey '{k}' was not found in {bib_files}")

    out_db.entries = entries

    return out_db


def update_bibdatabase(first: BibDatabase, second: BibDatabase) -> BibDatabase:
    """Update the *first* BibDatabase object with information from the *second*."""
    # This just does the work on the publicly available properties of BibDatabase.
    # Perhaps in some future version of BibtexParser the BibDatabase object will
    # know how to update itself.
    entry_dict = first.entries_dict
    entry_dict.update(second.entries_dict)

    first.entries = list(entry_dict.values())
    first.strings.update(second.strings)
    first.preambles.extend(second.preambles)

    return first


def extract_bibtex_entries(master_bib_file, citekeys):
    """
    Extract bibtex entries from master_bib_file that have certain citekeys.
    Return the entries sorted by citekey.
    """
    if len(citekeys) == 0:
        return []
    with open(master_bib_file, "r", encoding="utf-8") as file:
        master_bib = file.read()
    bibtex_entries = []
    for citekey in citekeys:
        match = re.search(
            r"@.*?\{" + citekey + r"\,[\s\S]+?\n\}\n", master_bib, re.UNICODE
        )
        if match is None:
            print(f"-> Citekey '{citekey}' was not found in {master_bib_file}")
        else:
            bibtex_entries.append((citekey, match.group(0)))
    return [entry[1] for entry in sorted(bibtex_entries)]


def create_bib_file(local_bib_file, bibtex_entries):
    """
    Write out some bibtex entries to local_bib_file.
    """
    with open(local_bib_file, "w", encoding="utf-8") as file:
        for entry in bibtex_entries:
            file.write(entry + "\n")


def shorten_dois(bibtex_entries):
    """
    Given some bibtex entries, check each one for a doi field and, if it
    contains one, attempt to replace the doi with its short version as
    provided by shortdoi.org.
    """
    new_bibtex_entries = []
    for entry in bibtex_entries:
        match = re.search(r"doi = \{(.+)\}", entry, re.UNICODE)
        if match is not None:
            doi = match.group(1).replace(r"\_", "_")
            short_doi = get_short_doi(doi)
            entry = entry.replace(doi.replace("_", r"\_"), short_doi)
        new_bibtex_entries.append(entry)
    return new_bibtex_entries


def shorten_dois_in_db(bib_db: BibDatabase) -> BibDatabase:
    """
    Returns a BibDatabase identical to the input BibDatabase, except that any
    DOI entries are replaced by their shortdoi.org version.
    """
    for i, entry in enumerate(bib_db.entries):
        if "doi" in entry:
            bib_db.entries[i]["doi"] = get_short_doi(entry["doi"])

    return bib_db


def get_short_doi(doi: str) -> str:
    """Return the shortdoi.org version of the provided DOI."""
    url = "http://shortdoi.org/" + doi + "?format=json"

    with urllib.request.urlopen(url) as resp:
        response = json.load(resp)

    if response["DOI"] == doi:
        return response["ShortDOI"]
    else:
        return doi


def main(
    manuscript_file,
    bib_files: list,
    local_bib_file,
    cite_commands,
    force_overwrite=False,
    short_dois=False,
):
    """
    Create a new local bib file from a master bib file based on the citations
    in a manuscript file.
    """
    if not force_overwrite and isfile(local_bib_file):
        print(f"-> {local_bib_file} already exists. Use -f to force overwrite.")
    else:
        citekeys = extract_citekeys(manuscript_file, cite_commands)
        print(f"Found {len(citekeys)} cite keys.")
        # bibtex_entries = extract_bibtex_entries(master_bib_file, citekeys)
        # if short_dois:
        #     bibtex_entries = shorten_dois(bibtex_entries)
        # create_bib_file(local_bib_file, bibtex_entries)

        bibtex_db = parse_bibtex_entries(bib_files, citekeys)
        if short_dois:
            bibtex_db = shorten_dois_in_db(bibtex_db)

        print(f"Fished {len(bibtex_db.entries)} BibTeX entries.")

        with open(local_bib_file, "w") as f:
            bibtexparser.dump(bibtex_db, f)


def cli():
    """
    Command line interface
    """
    parser = argparse.ArgumentParser(
        description="Extract entries from a .bib file that are cited in a .tex file."
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument(
        "manuscript_file",
        action="store",
        type=str,
        help="LaTeX file to extract citekeys from",
    )
    parser.add_argument(
        "master_bib_file",
        action="store",
        type=str,
        help="Master .bib file to extract BibTeX entries from",
    )
    parser.add_argument(
        "local_bib_file",
        action="store",
        type=str,
        help="Local .bib file to write BibTeX entries to",
    )
    parser.add_argument(
        "-b",
        "--bib",
        nargs="*",
        help="Additional .bib files to extract BibTeX entries from.  If the same "
        "citekey is in more than one .bib file, the information from the last "
        "file in the list is used (the master_bib_file is considered first in "
        "the list).",
    )
    parser.add_argument(
        "--cc",
        action="store",
        type=str,
        default="cite,citet,citep",
        dest="cite_commands",
        help="Cite commands separated by commas (default: 'cite,citet,citep')",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        dest="force_overwrite",
        help="Overwrite the local .bib file if it already exists",
    )
    parser.add_argument(
        "--sdoi",
        action="store_true",
        dest="short_dois",
        help="Shorten DOIs using http://shortdoi.org/",
    )
    args = parser.parse_args()

    bib_files = [
        args.master_bib_file,
    ]

    if args.bib is not None:
        bib_files.extend(args.bib)

    main(
        args.manuscript_file,
        bib_files,
        args.local_bib_file,
        args.cite_commands.split(","),
        args.force_overwrite,
        args.short_dois,
    )
