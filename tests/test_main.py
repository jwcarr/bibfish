from pathlib import Path
from tempfile import TemporaryDirectory
import bibfish


TESTS_DIR = Path(__file__).parent


def test_main():
    with TemporaryDirectory() as temp_dir:
        output_bib_file = Path(temp_dir) / "output.bib"

        bibfish.main(
            manuscript_file=TESTS_DIR / "manuscript1.tex",
            master_bib_files=[TESTS_DIR / "bibfile1.bib", TESTS_DIR / "bibfile2.bib"],
            local_bib_file=output_bib_file,
            cite_commands=["textcite", "parencite", "possessivecite"],
            force_overwrite=True,
            drop_fields=["abstract"],
        )

        with open(output_bib_file) as file:
            lines = file.read().split("\n")

    with open(TESTS_DIR / "expected_output1.bib") as file:
        expected_lines = file.read().split("\n")

    for line, expected_line in zip(lines, expected_lines):
        assert line == expected_line
