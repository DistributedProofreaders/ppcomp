""" Tests for ppcomp functions"""

import pytest
from ppcomp.ppcomp import *

myargs = ['fossilplants1.html',
          'fossilplants1.txt',
          '--css-bold', '=']


########## Text file ##########

def test_load_text_file():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('fossilplants1.txt')
    length = len(text_file.text.splitlines())
    assert length == 19645
    assert text_file.start_line == 0


def test_strip_pg_boilerplate():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('tower.txt')
    text_file.strip_pg_boilerplate()
    length = len(text_file.text.splitlines())
    assert length == 7898
    assert text_file.start_line == 29


def test_remove_thought_breaks():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('fossilplants1.txt')
    text_file.remove_thought_breaks()
    assert not re.search(r"\*\s+\*\s+\*\s+\*\s+\*", text_file.text)


def test_ignore_format():
    args = myargs + ['--ignore-format']
    text_file = PgdpFileText(load_args(args))
    text_file.load('fossilplants1.txt')
    text_file.ignore_format()
    assert -1 < text_file.text.find("His Einleitung")


def test_text_extract_footnotes_pp1():
    # [1] text text text
    args = myargs + ['--extract-footnotes']
    text_file = PgdpFileText(load_args(args))
    text_file.load('fossilplants1.txt')
    count = text_file.extract_footnotes_pp()
    length = len(text_file.footnotes)
    assert count == 932
    assert length == 56895


@pytest.mark.skip
def test_text_extract_footnotes_pp2():
    # Footnote 1:
    #
    #   text text text
    args = myargs + ['--extract-footnotes']
    text_file = PgdpFileText(load_args(args))
    text_file.load('footnotes2.txt')
    count = text_file.extract_footnotes_pp()
    length = len(text_file.footnotes)
    assert count == 119
    assert length == 23075


@pytest.mark.skip
def test_text_extract_footnotes_pp3():
    # ¹ See text text text
    args = myargs + ['--extract-footnotes']
    text_file = PgdpFileText(load_args(args))
    text_file.load('footnotes3.txt')
    count = text_file.extract_footnotes_pp()
    length = len(text_file.footnotes)
    assert count == 171
    assert length == 29898


######### Text file from rounds ##########

def test_load_pgdp_file():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c90be4f730d5.txt')
    length = len(text_file.text.splitlines())
    assert length == 9879
    assert text_file.start_line == 0


def test_remove_block_markup():
    markup = ['/*\n', '*/\n',
              '/#\n', '#/\n',
              '/P\n', 'P/\n',
              '/F\n', 'F/\n',
              '/X\n', 'X/\n']
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c90be4f730d5.txt')
    text_file.remove_block_markup()
    for txt in markup:
        assert -1 == text_file.text.find(txt)


def test_remove_paging():
    markup = ["-----File:", "[Blank Page]"]
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c90be4f730d5.txt')
    text_file.remove_paging()
    for txt in markup:
        assert -1 == text_file.text.find(txt)


def test_remove_formatting_ignore():
    markup = ['<i>', '</i>', '<b>', '</b>']
    args = myargs + ['--ignore-format']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c90be4f730d5.txt')
    text_file.remove_formatting()
    for txt in markup:
        assert -1 == text_file.text.find(txt)


def test_remove_formatting_no_ignore():
    markup = ['<i>', '</i>', '<b>', '</b>']
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c90be4f730d5.txt')
    text_file.remove_formatting()
    assert re.search(r"_((.|\n)+?)_", text_file.text)
    assert re.search(r"=((.|\n)+?)=", text_file.text)


def test_suppress_proofers_notes():
    args = myargs + ['--suppress-proofers-notes']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c90be4f730d5.txt')
    assert -1 < text_file.text.find("[** Did the day number [1?] not print?]")
    text_file.suppress_proofers_notes()
    assert -1 == text_file.text.find("[** Did the day number [1?] not print?]")


def test_regroup_split_words():
    args = myargs + ['--regroup-split-words']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c90be4f730d5.txt')
    text_file.remove_paging()
    text_file.regroup_split_words()
    # page marker between
    assert -1 == text_file.text.find("Con-*")
    # blank line between
    assert -1 == text_file.text.find("hush-*")
    # no line between
    assert -1 == text_file.text.find("north-*")
    # same line
    assert -1 < text_file.text.find("storehouses")


def test_suppress_footnote_tags():
    args = myargs + ['--suppress-footnote-tags']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c90be4f730d5.txt')
    text_file.suppress_footnote_tags()
    assert -1 == text_file.text.find("[Footnote")


def test_suppress_illustration_tags():
    args = myargs + ['--suppress-illustration-tags']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c90be4f730d5.txt')
    text_file.suppress_illustration_tags()
    assert -1 == text_file.text.find("[Illustration")


def test_suppress_sidenote_tags():
    args = myargs + ['--suppress-sidenote-tags']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c90be4f730d5.txt')
    text_file.suppress_sidenote_tags()
    assert -1 == text_file.text.find("[Sidenote:")


def test_text_extract_footnotes_pgdp():
    args = myargs + ['--extract-footnotes']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5cbe8b633145d.txt')
    text_file.extract_footnotes_pgdp()
    length = len(text_file.footnotes.splitlines())
    assert length == 86


########## HTML file ##########

def test_load_html_file():
    html_file = PgdpFileHtml(load_args(myargs))
    html_file.load('tower.htm')
    length = len(html_file.text.splitlines())
    assert length == 8963
    assert html_file.tree
    assert html_file.start_line == 276


def test_load_html5_file():
    html_file = PgdpFileHtml(load_args(myargs))
    html_file.load('fossilplants1.html')
    length = len(html_file.text.splitlines())
    assert length == 24192
    assert html_file.tree
    assert html_file.start_line == 609


def test_load_html5_bom_file():
    html_file = PgdpFileHtml(load_args(myargs))
    html_file.load('fossilplants1bom.html')
    length = len(html_file.text.splitlines())
    assert length == 85
    assert html_file.tree
    assert html_file.start_line == 67


def test_strip_pg_boilerplate_html():
    html_file = PgdpFileHtml(load_args(myargs))
    html_file.load('tower.htm')
    html_file.strip_pg_boilerplate()
    length = len(html_file.text.splitlines())
    assert length == 8963
    assert html_file.start_line == 308


def test_css_bold():
    args = myargs + ['--css-bold', '~']
    html_file = PgdpFileHtml(load_args(args))
    html_file.load('fossilplants1.html')
    html_file.cleanup()
    assert 0 <= html_file.text.find('~')


def test_remove_nbspaces():
    args = myargs + ['--suppress-nbsp-num']
    html_file = PgdpFileHtml(load_args(args))
    html_file.load('fossilplants1.html')
    html_file.remove_nbspaces()
    assert not re.search(r"(\d)\u00A0(\d)", html_file.text)
    assert 0 <= html_file.text.find("2885")


def test_remove_soft_hyphen():
    html_file = PgdpFileHtml(load_args(myargs))
    html_file.load('fossilplants1.html')
    html_file.remove_soft_hyphen()
    assert not re.search(r"\u00AD", html_file.text)


def test_text_transform():
    html_file = PgdpFileHtml(load_args(myargs))
    html_file.load('fossilplants1.html')
    html_file.mycss += ".smcap { text-transform:uppercase; }"
    html_file.process_css()
    assert True


def test_html_extract_footnotes():
    args = myargs + ['--extract-footnotes']
    html_file = PgdpFileHtml(load_args(args))
    html_file.load('fossilplants1.html')
    html_file.extract_footnotes()
    length = len(html_file.footnotes.splitlines())
    assert length == 2093


def test_add_illustration_tags():
    args = myargs + ['--css-add-illustration']
    html_file = PgdpFileHtml(load_args(args))
    html_file.load('fossilplants1.html')
    html_file.cleanup()
    assert -1 < html_file.text.find("[Illustration")


def test_add_sidenote_tags():
    args = myargs + ['--css-add-sidenote']
    html_file = PgdpFileHtml(load_args(args))
    html_file.load('fossilplants1.html')
    html_file.cleanup()
    assert -1 < html_file.text.find("[Sidenote")


def test_convert_smcaps_upper():
    args = myargs + ['--css-smcap', 'U']
    html_file = PgdpFileHtml(load_args(args))
    html_file.load('fossilplants1.html')
    html_file.cleanup()
    assert -1 < html_file.text.find("BIOLOGICAL SERIES")


def test_convert_smcaps_lower():
    args = myargs + ['--css-smcap', 'L']
    html_file = PgdpFileHtml(load_args(args))
    html_file.load('fossilplants1.html')
    html_file.cleanup()
    assert -1 < html_file.text.find("biological series")


def test_add_css():
    args = myargs + ['--css', 'span[class^="antiqua"]:before { content: "~" }',
                     '--css', 'span[class^="antiqua"]:after { content: "~" }']
    html_file = PgdpFileHtml(load_args(args))
    html_file.load('fossilplants1.html')
    html_file.cleanup()
    assert -1 < html_file.text.find('~Cambridge Natural Science Manuals.~')


def test_no_default_css():
    args = myargs + ['--css-no-default']
    html_file = PgdpFileHtml(load_args(args))
    html_file.load('fossilplants1.html')
    html_file.cleanup()
    assert -1 == html_file.text.find('_')


def test_superscript_to_unicode():
    x = to_superscript('123ab')
    assert x == '¹²³ᵃᵇ'
    x = to_superscript('3')
    assert x == '³'


def test_subscript_to_unicode():
    x = to_subscript('123')
    assert x == '₁₂₃'
    x = to_subscript('3')
    assert x == '₃'


def test_superscript_match():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c90be4f730d5.txt')
    assert -1 < text_file.text.find('(XVI.^{th} Century')
    assert -1 < text_file.text.find("S.^t John's Chapel")
    text_file.superscripts()
    assert -1 == text_file.text.find('(XVI.^{th} Century')
    assert -1 == text_file.text.find("S.^t John's Chapel")
    assert -1 < text_file.text.find('(XVI.ᵗʰ Century')
    assert -1 < text_file.text.find("S.ᵗ John's Chapel")


def test_subscript_match():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c90be4f730d5.txt')
    assert -1 < text_file.text.find("(XVI_{th} Century.)")
    text_file.subscripts()
    assert -1 == text_file.text.find("(XVI_{th} Century")
    assert -1 < text_file.text.find("(XVIₜₕ Century.)")


########## Both files ##########

def test_check_characters():
    files = [None, None]
    files[0] = PgdpFileText(load_args(myargs))
    files[0].load('fossilplants1.txt')
    files[1] = PgdpFileText(load_args(myargs))
    files[1].load('projectIDfossilplants1.txt')
    PPComp.check_characters(files)
    assert files[0].text == files[1].text


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
