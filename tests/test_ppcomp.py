""" Tests for ppcomp functions"""

import pytest

from ppcomp.ppcomp import *

myargs = ['fossilplants1.html',
          'fossilplants1.txt']


########## Text file ##########

def test_load_text_file():
    pgdp_text_file = PgdpFileText(load_args(myargs))
    pgdp_text_file.load('fossilplants1.txt')
    length = len(pgdp_text_file.text.splitlines())
    assert length == 19647
    assert pgdp_text_file.start_line == 1


def test_cleanup_text_file():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('fossilplants1.txt')
    length = len(text_file.text.splitlines())
    assert length == 19647
    assert text_file.start_line == 1


########## Text file from rounds ##########

@pytest.mark.skip
def test_regroup_split_words():
    args = myargs + ['--regroup-split-words']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.regroup_split_words()


def test_suppress_proofers_notes():
    args = myargs + ['--suppress-proofers-notes']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.suppress_proofers_notes()
    assert not re.search(r"\[\*\*[^]]*?]", text_file.text)


def test_suppress_illustration_tags():
    args = myargs + ['--suppress-illustration-tags']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.suppress_illustration_tags()
    assert -1 == text_file.text.find("[Illustration")


@pytest.mark.skip
def test_remove_formatting():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c76226c51b6d.txt')
    length = len(text_file.text.splitlines())
    assert length == 20020
    text_file.remove_formatting()


@pytest.mark.skip
def test_ignore_format():
    args = myargs + ['--ignore-format']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c76226c51b6d.txt')
    length = len(text_file.text.splitlines())
    assert length == 20020
    text_file.ignore_format()


def test_suppress_sidenote_tags():
    args = myargs + ['--suppress-sidenote-tags']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.suppress_sidenote_tags()
    assert -1 == text_file.text.find("[Sidenote:")


@pytest.mark.skip
def test_suppress_footnote_tags():
    args = myargs + ['--suppress-footnote-tags']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.suppress_footnote_tags()
    assert -1 == text_file.text.find("[Footnote:")


@pytest.mark.skip
def test_remove_thought_breaks():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('fossilplants1.txt')
    length = len(text_file.text.splitlines())
    assert length == 20020
    text_file.remove_thought_breaks()
    assert -1 == text_file.text.find("*     *     *     *     *")


########## HTML file ##########

def test_load_html_file():
    html_file = PgdpFileHtml(load_args(myargs))
    html_file.load('fossilplants1.html')
    length = len(html_file.text.splitlines())
    assert length == 24190
    assert html_file.tree
    assert html_file.body_line == 606


def test_load_pgdp_file():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c76226c51b6d.txt')
    length = len(text_file.text.splitlines())
    assert length == 6970
    assert text_file.start_line == 1


@pytest.mark.skip
def test_remove_block_markup():
    markup = ["-----File:", "[Blank Page]",
              '/*\n', '*/\n',
              '/#\n', '#/\n',
              '/P\n', 'P/\n',
              '/F\n', 'F/\n',
              '/X\n', 'X/\n',
              '<i>', '</i>',
              '<b>', '</b>']
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.remove_block_markup()
    length = len(text_file.text.splitlines())
    for txt in markup:
        assert -1 == text_file.text.find(txt)
    with open('outfile.txt', 'w') as f:
        f.write(text_file.text)


def load_args(myargs):
    parser = argparse.ArgumentParser(description='Diff text document for PGDP PP.')
    parser.add_argument('filename', metavar='FILENAME', type=str,
                        help='input files', nargs=2)
    parser.add_argument('--ignore-case', action='store_true', default=False,
                        help='Ignore case when comparing')
    parser.add_argument('--extract-footnotes', action='store_true', default=False,
                        help='Extract and process footnotes separately')
    parser.add_argument('--suppress-footnote-tags', action='store_true', default=False,
                        help='TXT: Suppress "[Footnote ?:" marks')
    parser.add_argument('--suppress-illustration-tags', action='store_true', default=False,
                        help='TXT: Suppress "[Illustration:" marks')
    parser.add_argument('--suppress-sidenote-tags', action='store_true', default=False,
                        help='TXT: Suppress "[Sidenote:" marks')
    parser.add_argument('--ignore-format', action='store_true', default=False,
                        help='In Px/Fx versions, silence formatting differences')
    parser.add_argument('--suppress-proofers-notes', action='store_true', default=False,
                        help="In Px/Fx versions, remove [**proofreaders notes]")
    parser.add_argument('--regroup-split-words', action='store_true', default=False,
                        help="In Px/Fx versions, regroup split wo-* *rds")
    parser.add_argument('--txt-cleanup-type', type=str, default='b',
                        help="TXT: In Px/Fx versions, type of text cleaning -- (b)est effort,"
                             " (n)one, (p)roofers")
    parser.add_argument('--css-add-illustration', action='store_true', default=False,
                        help="HTML: add [Illustration ] tag")
    parser.add_argument('--css-add-sidenote', action='store_true', default=False,
                        help="HTML: add [Sidenote: ...]")
    parser.add_argument('--css-smcap', type=str, default=None,
                        help="HTML: Transform small caps into uppercase (U), lowercase (L) or"
                             " title case (T)")
    parser.add_argument('--css-bold', type=str, default=None,
                        help="HTML: Surround bold strings with this string")
    parser.add_argument('--css', type=str, default=[], action='append',
                        help="HTML: Insert transformation CSS")
    parser.add_argument('--css-no-default', action='store_true', default=False,
                        help="HTML: do not use default transformation CSS")
    parser.add_argument('--suppress-nbsp-num', action='store_true', default=False,
                        help="HTML: Suppress non-breakable spaces between numbers")
    parser.add_argument('--ignore-0-space', action='store_true', default=False,
                        help='HTML: suppress zero width space (U+200b)')
    parser.add_argument('--css-greek-title-plus', action='store_true', default=False,
                        help="HTML: use greek transliteration in title attribute")
    parser.add_argument('--simple-html', action='store_true', default=False,
                        help="HTML: Process the html file and print the output (debug)")
    return parser.parse_args(args=myargs)
