#!/usr/bin/env python
"""This module has unit tests for the bibfish __init__ functions."""

# Copyright 2023-2024, bibfish developers
#
# Licensed under the MIT License, see the top-level LICENSE
# file for more information.

from textwrap import dedent
import unittest
from unittest.mock import mock_open, patch

from bibtexparser.bibdatabase import BibDatabase

import bibfish


class TestDOI(unittest.TestCase):
    def test_get_short_doi(self):
        doi = "10.3847/PSJ/ac09e9"
        short_doi = "10/js88"

        self.assertEqual(short_doi, bibfish.get_short_doi(doi))


class TestBibtexParser(unittest.TestCase):

    def test_update_bibdatabase(self):
        entries1 = [
            {"ID": "one", "ENTRYTYPE": "book"},
            {"ID": "two", "ENTRYTYPE": "article"},
        ]
        entries2 = [
            {"ID": "three", "ENTRYTYPE": "book"},
            {"ID": "four", "ENTRYTYPE": "article"},
        ]

        db1 = BibDatabase()
        db1.entries = entries1

        db2 = BibDatabase()
        db2.entries = entries2

        new_db = bibfish.update_bibdatabase(db1, db2)

        self.assertEqual(new_db.entries, entries1 + entries2)


class TestCitekeys(unittest.TestCase):

    def test_extract_citekeys(self):

        with patch(
            "bibfish.open",
            mock_open(
                read_data=dedent(
                    r"""\
                \documentclass{book}
                % If there are commented lines, which contain
                % \begin{document}
                % but no citation commands, we want to make sure
                % only the uncommented lines count.
                \begin{document}
                This line has a citation \citep{ref1}.
                This one doesn't.
                """
                )
            ),
        ):
            citekeys = bibfish.extract_citekeys("dummy.tex", ["cite", "citet", "citep"])
            self.assertEqual(len(citekeys), 1)
