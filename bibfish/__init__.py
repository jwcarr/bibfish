import argparse
import re


def extract_citekeys(manuscript_file, cite_commands):
    """
    Search manuscript_file for any cite commands and return the citekeys
    they make reference to.
    """
    with open(manuscript_file, "r") as file:
        manuscript = file.read()
    manuscript = manuscript.split(r"\begin{document}")[1]
    cite_commands = cite_commands.split(",")
    citations = re.findall(
        r"\\(" + "|".join(cite_commands) + r").*?\{(.*?)\}", manuscript
    )
    citekeys = []
    for citation in citations:
        citekeys.extend(citation[1].replace(" ", "").split(","))
    return list(set(citekeys))


def extract_bibtex_entries(master_bib_file, citekeys):
    """
    Extract bibtex entries from master_bib_file that have certain
    citekeys. Return the entries sorted by citekey.
    """
    with open(master_bib_file, "r", encoding="utf-8") as file:
        master_bib = file.read()
    bibtex_entries = []
    for citekey in citekeys:
        match = re.search(
            r"@.*?\{" + citekey + r"[\s\S]+?\n\}\n", master_bib, re.UNICODE
        )
        if match is None:
            print('Citekey "%s" is missing from %s' % (citekey, master_bib_file))
        else:
            bibtex_entries.append((citekey, match.group(0)))
    return [entry[1] for entry in sorted(bibtex_entries)]


def create_bib_file(bibtex_entries, bib_file):
    """
    Write out some bibtex entries to bib_file.
    """
    with open(bib_file, "w", encoding="utf-8") as file:
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
        print("DOI shortening requires the requests package. pip install requests")
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


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "manuscript_file",
        action="store",
        type=str,
        help=".tex file to extract citekeys from",
    )
    parser.add_argument(
        "master_bib_file",
        action="store",
        type=str,
        help=".bib file to extract references from",
    )
    parser.add_argument(
        "bib_file",
        action="store",
        type=str,
        help=".bib file to write references out to",
    )
    parser.add_argument(
        "--cc",
        dest="cite_commands",
        action="store",
        type=str,
        default="citet,citep",
        help="cite commands separated by commas",
    )
    parser.add_argument(
        "--sdoi",
        action="store_true",
        default=False,
        dest="shorten_dois",
        help="shorten DOIs",
    )
    args = parser.parse_args()
    citekeys = extract_citekeys(args.manuscript_file, args.cite_commands)
    bibtex_entries = extract_bibtex_entries(args.master_bib_file, citekeys)
    if args.shorten_dois:
        bibtex_entries = shorten_dois(bibtex_entries)
    create_bib_file(bibtex_entries, args.bib_file)
