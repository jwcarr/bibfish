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


def extract_citekeys(manuscript_file: str, cite_commands: list) -> list:
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
        r"\\(" + "|".join(cite_commands) + r")(\[.+?\])?.*?\{(.*?)\}", manuscript
    )
    for citation in citations:
        for key in citation[2].replace(" ", "").split(","):
            if key:
                citekeys.append(key)
    return list(set(citekeys))


def find_imported_files(manuscript: str) -> list:
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
    # If an entry exists in multiple bib-files, BibTeX will use the first one.
    # Since update_database() uses update method on dictionaries, it overwrites
    # existing entries with new ones -> process the bib-files in reversed order.
    # (An alternative would be to rewrite the update_database() method...)
    for bib_file in reversed(bib_files):
        with open(bib_file) as file:
            bib_database = bibtexparser.load(
                file,
                parser=bibtexparser.bparser.BibTexParser(
                    interpolate_strings=True,
                    ignore_nonstandard_types=False,
                ),
            )
            out_db = update_bibdatabase(out_db, bib_database)
    
    # In bibtexparser 1.x, each we access of entries_dict property of BibDatabase
    # object db calls db.get_entry_dict(), which creates db._entries_dict by
    # reading the whole list of entries.
    # This is VERY inefficient with multiple calls -> we create our own dict
    out_db_dict = {entry['ID']: entry for entry in out_db.entries}

    db_keys = set()  # keys in the new database
    entries = []     # entries in the new BibDatabase object
    key_list = citekeys
    while len(key_list) > 0:
        crossrefs = []
        for citekey in key_list:
            entry = out_db_dict.get(citekey, None)
            if entry is None:
                print(f"bibfish: Citekey '{citekey}' was not found in {bib_files}")
            else:
                db_keys.add(citekey)
                entries.append(entry)
                if 'crossref' in entry:
                    xkey = entry['crossref']
                    if xkey not in db_keys:
                        crossrefs.append(xkey)
        key_list = crossrefs

    # override database with the selected entries
    out_db.entries = entries
    return out_db


def update_bibdatabase(first: BibDatabase, second: BibDatabase) -> BibDatabase:
    """
    Update the *first* BibDatabase object with information from the *second*.
    """
    # This just does the work on the publicly available properties of BibDatabase.
    # Perhaps in some future version of BibtexParser the BibDatabase object will
    # know how to update itself.
    entry_dict = first.entries_dict
    entry_dict.update(second.entries_dict)
    first.entries = list(entry_dict.values())
    first.strings.update(second.strings)
    first.preambles.extend(second.preambles)
    return first


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
    """
    Return the shortdoi.org version of the provided DOI.
    """
    url = "http://shortdoi.org/" + doi + "?format=json"
    with urllib.request.urlopen(url) as resp:
        response = json.load(resp)
    if response["DOI"] == doi:
        return response["ShortDOI"]
    else:
        return doi


def filter_fields(bib_db: BibDatabase, drop_fields: list) -> BibDatabase:
    """
    Returns a BibDatabase identical to the input BibDatabase, except that
    all fields in the drop_fields list are dropped from all entries
    """
    for entry in bib_db.entries:
        for field in drop_fields:
            entry.pop(field, None)
    return bib_db


def main(
    manuscript_file,
    master_bib_file,
    local_bib_file,
    cite_commands,
    force_overwrite=False,
    short_dois=False,
    drop_fields=None
):
    """
    Create a new local bib file from a master bib file based on the citations
    in a manuscript file.
    """
    if not force_overwrite and isfile(local_bib_file):
        print(f"bibfish: {local_bib_file} already exists. Use -f to force overwrite.")
        return

    citekeys = extract_citekeys(manuscript_file, cite_commands)
    if not isinstance(master_bib_file, list):
        master_bib_file = [master_bib_file]
    bibtex_db = parse_bibtex_entries(master_bib_file, citekeys)

    # post-processing
    if short_dois:
        bibtex_db = shorten_dois_in_db(bibtex_db)
    if isinstance(drop_fields, list) and len(drop_fields) > 0:
        bibtex_db = filter_fields(bibtex_db, drop_fields)

    # if the database has keys with 'crossref', the referenced keys must come after
    # - we ensure this by the way the process the database, but bibtexparser.dump()
    #   sorts keys alphabetically by default -> have to be disabled for crossref
    db_writer = bibtexparser.bwriter.BibTexWriter()
    if any('crossref' in entry for entry in bibtex_db.entries):
        db_writer.order_entries_by = None
    with open(local_bib_file, "w") as file:
        bibtexparser.dump(bibtex_db, file, db_writer)


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
    parser.add_argument(
        "--drop-fields",
        type=str,
        metavar="FIELDS",
        help="Comma-separated list of fields that should be dropped from the output"
    )
    args = parser.parse_args()

    bib_files = [args.master_bib_file]
    if args.bib is not None:
        bib_files.extend(args.bib)

    drop_fields = [f.strip() for f in args.drop_fields.split(",")] \
        if args.drop_fields is not None and len(args.drop_fields) > 0 else None

    main(
        args.manuscript_file,
        bib_files,
        args.local_bib_file,
        args.cite_commands.split(","),
        force_overwrite=args.force_overwrite,
        short_dois=args.short_dois,
        drop_fields=drop_fields
    )
