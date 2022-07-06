from os.path import isfile
import argparse
import re

try:
    from ._version import __version__
except ImportError:
    __version__ = "???"


def extract_citekeys(manuscript_file, cite_commands):
    """

    Search manuscript_file for any cite commands and return the citekeys they
    make reference to.

    """
    if len(cite_commands) == 0:
        return []
    with open(manuscript_file, "r") as file:
        manuscript = file.read()
    manuscript = manuscript.split(r"\begin{document}")[1]
    citations = re.findall(
        r"\\(" + "|".join(cite_commands) + r").*?\{(.*?)\}", manuscript
    )
    citekeys = []
    for citation in citations:
        citekeys.extend(citation[1].replace(" ", "").split(","))
    return list(set(citekeys))


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
    try:
        import requests
    except ImportError:
        print("-> DOI shortening requires the requests package. pip install requests")
        return bibtex_entries
    import json

    new_bibtex_entries = []
    for entry in bibtex_entries:
        match = re.search(r"doi = \{(.+)\}", entry, re.UNICODE)
        if match is not None:
            doi = match.group(1).replace(r"\_", "_")
            short_doi_query = "http://shortdoi.org/" + doi + "?format=json"
            request = requests.get(short_doi_query)
            response = json.loads(request.text)
            if response["DOI"] == doi:
                short_doi = response["ShortDOI"]
                entry = entry.replace(doi.replace("_", r"\_"), short_doi)
        new_bibtex_entries.append(entry)
    return new_bibtex_entries


def main(
    manuscript_file,
    master_bib_file,
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
        bibtex_entries = extract_bibtex_entries(master_bib_file, citekeys)
        if short_dois:
            bibtex_entries = shorten_dois(bibtex_entries)
        create_bib_file(local_bib_file, bibtex_entries)


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
        "--cc",
        action="store",
        type=str,
        default="citet,citep",
        dest="cite_commands",
        help="Cite commands separated by commas (default: 'citet,citep')",
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
    main(
        args.manuscript_file,
        args.master_bib_file,
        args.local_bib_file,
        args.cite_commands.split(","),
        args.force_overwrite,
        args.short_dois,
    )
