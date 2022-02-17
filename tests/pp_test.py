import argparse

import pytest

from ppcomp.ppcomp import *

args = object

@pytest.fixture()
def pgdp_text_file(test_args):
    "Create a processed text file"
    return PgdpFileText(test_args)


@pytest.fixture()
def pgdp_html_file():
    "Create a processed html file"
    return PgdpFileHtml(test_args)


def test_load_text_file(pgdp_text_file):
    pgdp_text_file.load('fossilplants1.txt')
    length = len(pgdp_text_file.text.splitlines())
    assert pgdp_text_file.args.simple_html
    assert pgdp_text_file.args.css == ["css test", "css test2"]
    assert length == 19647


def test_prepare_text_file(pgdp_text_file):
    pgdp_text_file.load('fossilplants1.txt')
    length = len(pgdp_text_file.text.splitlines())
    assert length == 19647


@pytest.mark.skip
def test_prepare_pg_text_file(pgdp_text_file):
    pgdp_text_file.load('fossilplants1pg.txt')
    length = len(pgdp_text_file.text.splitlines())
    assert length > 19647
    pgdp_text_file.prepare()
    length = len(pgdp_text_file.text.splitlines())
    assert length == 19647


def test_load_html_file(pgdp_html_file):
    pgdp_html_file.load('fossilplants1.html')
    length = len(pgdp_html_file.text.splitlines())
    assert length == 24190
    assert pgdp_html_file.tree
    assert pgdp_html_file.body_line == 606


def test_load_pgdp_file(pgdp_text_file):
    pgdp_text_file.load('projectID123456.txt')
    length = len(pgdp_text_file.text.splitlines())
    assert length == 19647


@pytest.mark.skip
def test_prepare_pgdp_file(pgdp_text_file):
    pgdp_text_file.load('projectID123456.txt')
    pgdp_text_file.prepare()
    length = len(pgdp_text_file.text.splitlines())
    assert length == 19647


@pytest.fixture()
def test_args():
    myargs = ['fossilplants1.html',
              'fossilplants1.txt',
              '--simple-html',
              '--css', 'css test',
              '--css', 'css test2']
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
    args = parser.parse_args(args=myargs)
    return args
    #print(args)

    # filename = ['tests/fossilplants1.html', 'tests/fossilplants1.txt'],
    # ignore_case = False,
    # extract_footnotes = False,
    # suppress_footnote_tags = False,
    # suppress_illustration_tags = False,
    # suppress_sidenote_tags = False,
    # ignore_format = False,
    # suppress_proofers_notes = False,
    # regroup_split_words = False,
    # txt_cleanup_type = 'b',
    # css_add_illustration = False,
    # css_add_sidenote = False,
    # css_smcap = None,
    # css_bold = None,
    # css = [],
    # css_no_default = False,
    # suppress_nbsp_num = False,
    # ignore_0_space = False,
    # css_greek_title_plus = False,
    # simple_html = False)

