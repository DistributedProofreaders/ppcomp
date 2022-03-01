""" Tests for ppcomp functions"""

from ppcomp.ppcomp import *

myargs = ['fossilplants1.html',
          'fossilplants1.txt']


########## Text file ##########

def test_load_text_file():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('fossilplants1.txt')
    length = len(text_file.text.splitlines())
    assert length == 19649
    assert text_file.start_line == 1


def test_strip_pg_boilerplate():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('fossilplants1pg.txt')
    text_file.strip_pg_boilerplate()
    length = len(text_file.text.splitlines())
    assert length == 19647
    assert text_file.start_line == 27


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


########## Text file from rounds ##########

def test_load_pgdp_file():
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c76226c51b6d.txt')
    length = len(text_file.text.splitlines())
    assert length == 6972
    assert text_file.start_line == 1


def test_remove_block_markup():
    markup = ['/*\n', '*/\n',
              '/#\n', '#/\n',
              '/P\n', 'P/\n',
              '/F\n', 'F/\n',
              '/X\n', 'X/\n']
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.remove_block_markup()
    for txt in markup:
        assert -1 == text_file.text.find(txt)
#    with open('outfile.txt', 'w', encoding='utf-8') as f:
#        f.write(text_file.text)


def test_remove_paging():
    markup = ["-----File:", "[Blank Page]"]
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.remove_paging()
    for txt in markup:
        assert -1 == text_file.text.find(txt)


def test_remove_formatting():
    markup = ['<i>', '</i>', '<b>', '</b>']
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.remove_formatting()
    for txt in markup:
        assert -1 == text_file.text.find(txt)


def test_remove_formatting_ignore():
    markup = ['<i>', '</i>', '<b>', '</b>']
    args = myargs + ['--ignore-format']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.remove_formatting()
    for txt in markup:
        assert -1 == text_file.text.find(txt)


def test_remove_formatting_no_ignore():
    markup = ['<i>', '</i>', '<b>', '</b>']
    text_file = PgdpFileText(load_args(myargs))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.remove_formatting()
    assert re.search(r"_((.|\n)+?)_", text_file.text)


def test_suppress_proofers_notes():
    args = myargs + ['--suppress-proofers-notes']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.suppress_proofers_notes()
    assert -1 == text_file.text.find("[**probably speck,")


def test_regroup_split_words():
    args = myargs + ['--regroup-split-words']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.remove_paging()
    text_file.regroup_split_words()
    # page marker between
    assert -1 == text_file.text.find("fam-*")
    # blank line between
    assert -1 == text_file.text.find("break-*")
    # no line between
    assert -1 == text_file.text.find("three-*")
    # same line
    assert -1 < text_file.text.find("lightwood")


#@pytest.mark.skip
def test_suppress_footnote_tags():
    args = myargs + ['--suppress-footnote-tags']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.suppress_footnote_tags()
    assert -1 == text_file.text.find("[Footnote:")


def test_suppress_illustration_tags():
    args = myargs + ['--suppress-illustration-tags']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.suppress_illustration_tags()
    assert -1 == text_file.text.find("[Illustration")


def test_suppress_sidenote_tags():
    args = myargs + ['--suppress-sidenote-tags']
    text_file = PgdpFileText(load_args(args))
    text_file.load('projectID5c76226c51b6d.txt')
    text_file.suppress_sidenote_tags()
    assert -1 == text_file.text.find("[Sidenote:")


########## HTML file ##########

def test_load_html_file():
    html_file = PgdpFileHtml(load_args(myargs))
    html_file.load('fossilplants1.html')
    length = len(html_file.text.splitlines())
    assert length == 24192
    assert html_file.tree
    assert html_file.body_line == 611


def test_strip_pg_boilerplate_html():
    html_file = PgdpFileHtml(load_args(myargs))
    html_file.load('fossilplants1pg.html')
    html_file.strip_pg_boilerplate()
    length = len(html_file.text.splitlines())
    dumptree(html_file.tree)
    #assert length == 23581
    #assert html_file.start_line == 27


def test_remove_nbspaces():
    args = myargs + ['--suppress-nbsp-num']
    html_file = PgdpFileHtml(load_args(args))
    html_file.load('fossilplants1.html')
    html_file.remove_nbspaces()
    assert not re.search(r"(\d)\u00A0(\d)", html_file.text)


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
    assert length > 0
    with open('tmpoutfile.txt', 'w', encoding='utf-8') as f:
        f.write(html_file.footnotes)


########## Both files ##########

def test_check_characters():
    markup = ['<i>', '</i>', '<b>', '</b>']
    files = [None, None]
    files[0] = PgdpFileText(load_args(myargs))
    files[0].load('fossilplants1.txt')
    files[1] = PgdpFileHtml(load_args(myargs))
    files[1].load('fossilplants1.html')
    PPComp.check_characters(files)
    assert True


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
