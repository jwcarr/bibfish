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
    found_filenames = []
    for included_file in re.findall(r"\\(include|input).*?\{(.*?)\}", manuscript):
        if included_file[1]:
            found_filenames.append(included_file[1])
    for included_file in re.findall(r"\\import.*?\{(.*?)\}.*?\{(.*?)\}", manuscript):
        if included_file[1]:
            found_filenames.append(included_file[0] + included_file[1])
    filenames = []
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
    for bib_file in reversed(bib_files):  # give priority to earlier bib files
        with open(bib_file) as file:
            bib_database = bibtexparser.load(
                file,
                parser=bibtexparser.bparser.BibTexParser(
                    interpolate_strings=True,
                    ignore_nonstandard_types=False,
                ),
            )
            out_db = update_bibdatabase(out_db, bib_database)
    out_db_entries = {entry["ID"]: entry for entry in out_db.entries}
    db_citekeys = set()  # citekeys in the new database
    entries = []  # entries in the new BibDatabase object
    key_list = citekeys
    while len(key_list) > 0:
        crossrefs = []
        for citekey in key_list:
            entry = out_db_entries.get(citekey, None)
            if entry is None:
                print(f"bibfish: Citekey '{citekey}' was not found in {bib_files}")
            else:
                db_citekeys.add(citekey)
                entries.append(entry)
                if "crossref" in entry:
                    xkey = entry["crossref"]
                    if xkey not in db_citekeys:
                        crossrefs.append(xkey)
        key_list = crossrefs
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
    master_bib_files,
    local_bib_file,
    cite_commands,
    force_overwrite=False,
    short_dois=False,
    drop_fields=None,
):
    """
    Create a new local bib file from a (set of) master bib file(s) based on
    the citations found in a manuscript file.
    """
    if not force_overwrite and isfile(local_bib_file):
        print(f"bibfish: {local_bib_file} already exists. Use -f to force overwrite.")
        return

    citekeys = extract_citekeys(manuscript_file, cite_commands)
    if not isinstance(master_bib_files, list):
        master_bib_files = [master_bib_files]
    bibtex_db = parse_bibtex_entries(master_bib_files, citekeys)

    if short_dois:
        bibtex_db = shorten_dois_in_db(bibtex_db)

    if isinstance(drop_fields, list) and len(drop_fields) > 0:
        bibtex_db = filter_fields(bibtex_db, drop_fields)

    # If there are crossrefs, do not sort alphabetically. This is a hack and
    # should be fixed by extracting the crossrefs separately and
    # concatenating them to the end of the output file.
    db_writer = bibtexparser.bwriter.BibTexWriter()
    if any("crossref" in entry for entry in bibtex_db.entries):
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
        help="Master .bib file to extract BibTeX entries from. If you have multiple .bib files, use the --bib option to supply additional files.",
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
        help="Additional .bib files to extract BibTeX entries from. If the same citekey exists in multiple .bib files, earlier .bib files take priority over later ones.",
    )
    parser.add_argument(
        "-c",
        "--cc",
        action="store",
        type=str,
        default="cite,citet,citep",
        dest="cite_commands",
        help="Comma-separated list of cite commands (default: 'cite,citet,citep')",
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
        action="store",
        type=str,
        metavar="FIELDS",
        dest="drop_fields",
        help="Comma-separated list of BibTex fields to drop in the local .bib file",
    )
    args = parser.parse_args()

    master_bib_files = [args.master_bib_file]
    if args.bib is not None:
        master_bib_files.extend(args.bib)

    cite_commands = [cc.strip() for cc in args.cite_commands.split(",")]

    if args.drop_fields is not None and len(args.drop_fields) > 0:
        drop_fields = [f.strip() for f in args.drop_fields.split(",")]
    else:
        drop_fields = None

    main(
        manuscript_file=args.manuscript_file,
        master_bib_files=master_bib_files,
        local_bib_file=args.local_bib_file,
        cite_commands=cite_commands,
        force_overwrite=args.force_overwrite,
        short_dois=args.short_dois,
        drop_fields=drop_fields,
    )
