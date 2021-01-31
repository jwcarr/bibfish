bibfish
=======

`bibfish` generates a local BibTeX file from a central BibTeX database based on the citations found in a LaTeX file. This is useful if you want to maintain a single master BibTeX file and automatically generate a separate, independent BibTeX file for each manuscript you're working on. It is similar to [bibexport](https://www.ctan.org/tex-archive/biblio/bibtex/utils/bibexport/) and [makebib](https://gitlab.com/Verner/makebib), except `bibfish` is not dependent on any particular LaTeX tool and is therefore agnostic about your choice of bibliographic software (BibTeX vs. BibLaTeX, etc) or general typesetting pipeline.

`bibfish` can be run once if all you want to do is create a subset of your `master.bib` to send to the publisher. Alternatively, `bibfish` can be used as an integral part of your typesetting procedure, with an intended usage pattern like this:

1. Start a new LaTeX document and, when setting up the bibliography, point it to e.g. `references.bib` (no need to create this file; it will be generated automatically). For example, depending on how you set things up, you might have a line like `\bibliography{references.bib}` or `\addbibresource{references.bib}`.
2. Add any BibTeX entries you want to cite to your `master.bib` (stored e.g. in your home directory).
3. Cite some BibTeX entries in your LaTeX document using their citekeys as normal.
4. Before typesetting, run `bibfish` first; this will fish out the relevant entries from `master.bib` and place them in `references.bib`.
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

Each time you run this script, `bibfish` will search `manuscript.tex` for citekeys, extract the relevant entries from `~/master.bib`, and write them out to `references.bib`, allowing the rest of the typesetting process to proceed as normal.

The benefit of this is that your LaTeX document does not need to have any dependence on or reference to `~/master.bib`. This means you can maintain a single `master.bib`, while also maintaining each manuscript as its own independent self-contained package. You could, for example, send `manuscript.tex` and `references.bib` to a coauthor or publisher without needing to supply your entire `master.bib`, and `manuscript.tex` and `references.bib` can be kept under version control without any connection to `master.bib`.


Installation
------------

`bibfish` is written in Python and can be installed using pip:

```shell
pip install bibfish
```


Usage
-----

Once installed, `bibfish` may be used from the command line like this:

```shell
bibfish manuscript.tex ~/master.bib references.bib
```

By default, `bibfish` will not overwrite a local .bib file if it already exists. To override this behavior, use the `-f` option:

```shell
bibfish -f manuscript.tex ~/master.bib references.bib
```

By default, `bibfish` searches your manuscript for `\citet{}` and `\citep{}`. If you are using a different set of cite commands, you can specify them with the `--cc` option:

```shell
bibfish --cc "textcite,parencite,possessivecite" manuscript.tex ~/master.bib references.bib
```


Caveats
-------

I have not tested `bibfish` against any BibTeX file other than my own, and it will likely break if your `master.bib` is structured in a substantially different way. For reference, a typical entry in my `master.bib` looks like this:

```bibtex
@article{Carr:2020,
author = {Carr, Jon W and Smith, Kenny and Culbertson, Jennifer and Kirby, Simon},
title = {Simplicity and Informativeness in Semantic Category Systems},
journal = {Cognition},
year = {2020},
volume = {202},
pages = {Article 104289},
doi = {10.1016/j.cognition.2020.104289}
}
```

Note in particular that the first line of an entry should start with an `@` and the final line should contain a single `}`; everything between these two characters will be extracted and copied verbatim.


License
-------

`bibfish` is licensed under the terms of the MIT License.
