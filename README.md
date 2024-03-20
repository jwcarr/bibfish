bibfish
=======

Bibfish generates a local BibTeX file from a central BibTeX database based on the citations found in a LaTeX file. This is useful if you want to maintain a single master BibTeX file (or several) and automatically generate a separate, independent BibTeX file for each manuscript you're working on. It is similar to [Bibexport](https://www.ctan.org/tex-archive/biblio/bibtex/utils/bibexport/) and [Makebib](https://gitlab.com/Verner/makebib), except Bibfish is not dependent on any particular LaTeX tool and is therefore agnostic about your choice of bibliographic software (BibTeX vs. BibLaTeX, etc.) or general typesetting pipeline.


Installation
------------

Bibfish is written in Python and can be installed using `pip`:

```shell
pip install bibfish
```


Basic usage
-----------

Bibfish may be used from the command line like so:

```shell
bibfish manuscript.tex ~/master.bib references.bib
```

> **Warning**
> Ordering these filenames incorrectly could result in data loss! Ensure that the arguments are ordered as follows: (1) The LaTeX manuscript file. (2) Your master BibTeX database. (3) The output file that will be created by Bibfish.

By default, Bibfish will not overwrite a local .bib file if it already exists. To override this behavior, use the `-f` option:

```shell
bibfish -f manuscript.tex ~/master.bib references.bib
```

By default, Bibfish searches your manuscript for `\cite{}`, `\citet{}`, and `\citep{}`. If you are using a different set of cite commands, you can specify them with the `--cc` option:

```shell
bibfish --cc "textcite,parencite,possessivecite" manuscript.tex ~/master.bib references.bib
```

If you maintain multiple BibTex databases, you can pass additional .bib files with the `--bib` option:

```shell
bibfish manuscript.tex ~/master.bib references.bib --bib ~/my_papers.bib ~/my_abstracts.bib
```


Usage as part of a larger pipeline
-----------------------------------

Bibfish can also be used as an integral part of your typesetting procedure, with the following intended usage pattern:

1. Start a new LaTeX document and, when setting up the bibliography, point it to e.g. `references.bib` (no need to create this file; it will be generated automatically). For example, depending on how you set things up, you might have a line like `\bibliography{references.bib}` or `\addbibresource{references.bib}`.
2. Add any BibTeX entries you want to cite to your `master.bib` (stored e.g. in your home directory).
3. Cite some BibTeX entries in your LaTeX document using their citekeys as normal.
4. Before typesetting, run Bibfish first; this will fish out the relevant entries from `master.bib` and place them in `references.bib`.
5. Continue with the rest of your typesetting procedure, e.g. run `pdflatex`, `latex`, `xelatex`, `bibtex`, `biber`, `dvipdf`, or whatever else you normally do in your pipeline.

For example, you might create a typesetting script like this:

```shell
#!/bin/bash

bibfish -f manuscript.tex ~/master.bib references.bib
latex manuscript.tex
bibtex manuscript.aux
latex manuscript.tex
dvipdfm manuscript.dvi
```

Each time you run this script, Bibfish will search `manuscript.tex` for citekeys, extract the relevant entries from `~/master.bib`, and write them out to `references.bib`, allowing the rest of the typesetting process to proceed as normal.

The benefit of this is that your LaTeX document does not need to have any dependence on or reference to `~/master.bib`. This means you can maintain a single `master.bib`, while also maintaining each manuscript as its own independent self-contained package. You could, for example, send `manuscript.tex` and `references.bib` to a coauthor or publisher without needing to supply your entire `master.bib`, and `manuscript.tex` and `references.bib` can be kept under version control without any connection to `master.bib`.


Caveats
-------

Bibfish relies on [BibtexParser](https://github.com/sciunto-org/python-bibtexparser) to read and write .bib files. Although we have configured it in a relatively permissive fashion, please raise an issue if Bibfish has trouble reading your database or is producing unexpected output.


Contributing
------------

Bibfish is in an early stage of development, but I am very happy to receive bug reports and suggestions via the [GitHub Issues page](https://github.com/jwcarr/bibfish/issues). If you'd like to work on new features or fix stuff that's currently broken, please feel free to fork the repo and/or raise an issue to discuss details. Before sending a pull request, you should check that the unit tests pass using [Pytest](https://pytest.org):

```shell
pytest tests/
```

and run [Black](https://black.readthedocs.io) over the codebase to normalize the style:

```shell
black bibfish/
```
