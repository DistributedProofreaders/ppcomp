import argparse
import os

from lxml import etree
from lxml.html import html5parser

"""
ppcomp.py - compare text from 2 files, ignoring html and formatting differences, for use by users
of Distributed Proofreaders (https://www.pgdp.net)

Applies various transformations according to program options before passing the files to the Linux
program dwdiff.

Copyright (C) 2012-2013 bibimbop at pgdp
Copyright 2019-2022 Robert Tonsing

Originally written as the standalone program comp_pp.py by bibimbop at PGDP as part of his PPTOOLS
program. It is used as part of the PP Workbench with permission.

Distributable under the GNU General Public License Version 3 or newer.
"""

PG_EBOOK_START1 = "*** START OF THE PROJECT GUTENBERG EBOOK"
PG_EBOOK_START2 = "*** START OF THIS PROJECT GUTENBERG EBOOK"
PG_EBOOK_END1 = "*** END OF THE PROJECT GUTENBERG EBOOK"
PG_EBOOK_END2 = "*** END OF THIS PROJECT GUTENBERG EBOOK"
PG_EBOOK_START_REGEX = r".*?\*\*\* START OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*(.*)"


class PgdpFile:
    """Base class: Store and process a DP text or html file
    Call order from PPComp.do_process():
        1. load()
        2. prepare()
        3. convert()
        4. extract_footnotes()
        5. transform()
    """

    def __init__(self, args):
        self.args = args
        self.basename = ""
        self.text = None  # file text
        self.text_lines = None  # list of file lines
        self.footnotes = ""  # footnotes, if extracted
        self.transform_func = []  # List of transforms to perform

    def load(self, filename):
        """Load a file (text or html)."""
        self.basename = os.path.basename(filename)
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                self.text = file.read()
        except UnicodeError:
            with open(filename, 'r', encoding='latin-1') as file:
                self.text = file.read()
        except FileNotFoundError as ex:
            raise IOError("Cannot load file: " + filename) from ex
        if len(self.text) < 10:
            raise SyntaxError("File is too short: " + filename)
        self.text_lines = self.text.splitlines()

    def strip_pg_boilerplate(self):
        """Remove the PG header and footer from the text if present."""
        pass

    def prepare(self):
        """Clean text in preparation for conversions"""
        # strip boilerplate
        # page markup, blank pages
        # block markup
        # replace italics, bold
        # proofers notes
        # split words
        # thought breaks
        # add/suppress illustrations, sidenotes, footnotes
        # html head
        # css transforms
        pass

    def convert(self):
        """Apply needed text conversions"""
        # handle universal ones here, particular ones in subclass,
        # comparisons (do_process) elsewhere
        for func in self.transform_func:
            self.text = func(self.text)
        pass

    def extract_footnotes(self):
        """Extract the footnotes"""
        pass


class PgdpFileText(PgdpFile):
    """Store and process a DP text file"""

    def __init__(self, args):
        super().__init__(args)
        self.from_pgdp_rounds = False

    def strip_pg_boilerplate(self):
        """Remove the PG header and footer from the text if present."""
        pass

    def prepare(self):
        """Clean text in preparation for conversions"""
        self.from_pgdp_rounds = self.basename.startswith('projectID')

    def convert(self):
        """Apply needed text conversions"""
        for func in self.transform_func:
            self.text = func(self.text)

    def extract_footnotes(self):
        """Extract the footnotes."""
        if not self.args.extract_footnotes:
            return


class PgdpFileHtml(PgdpFile):
    """Store and process a DP html file."""

    def __init__(self, args):
        super().__init__(args)
        self.tree = None

    def load(self, filename):
        # noinspection GrazieInspection
        """Load the file. If parsing succeeded, then self.tree is set, and parser.errors is []"""

        # noinspection PyProtectedMember,Pylint
        def remove_namespace():
            """Remove namespace URI in elements names
            "{http://www.w3.org/1999/xhtml}html" -> "html"
            """
            for elem in self.tree.iter():
                if not isinstance(elem, (etree._Comment, etree._ProcessingInstruction)):
                    elem.tag = etree.QName(elem).localname
            # noinspection Pylint
            etree.cleanup_namespaces(self.tree)  # Remove unused namespace declarations

        super().load(filename)
        parser = html5parser.HTMLParser()
        try:
            tree = html5parser.document_fromstring(self.text)
        except Exception as ex:
            raise SyntaxError("File cannot be parsed: " + filename) from ex

        if parser.errors and len(parser.errors):
            raise SyntaxError("Parsing errors in document: " + filename)

        self.tree = tree.getroottree()
        # Remove the namespace from the tags
        remove_namespace()

    def strip_pg_boilerplate(self):
        """Remove the PG header and footer from the text if present."""
        pass

    def prepare(self):
        """Clean text in preparation for conversions"""
        pass

    # noinspection Pylint
    def convert(self):
        """Apply needed text conversions"""
        # noinspection Pylint
        self.text = etree.XPath("string(/)")(self.tree)
        for func in self.transform_func:
            self.text = func(self.text)

    def extract_footnotes(self):
        """Extract the footnotes"""
        if not self.args.extract_footnotes:
            return


class PPComp:
    """Compare two files."""

    def __init__(self, args):
        self.args = args

    def convert_both(self):
        """Apply various conversions to both files"""
        pass

    def compare_texts(self, text1, text2):
        """Compare two sources, using dwdiff"""
        pass

    def do_process(self):
        """Main routine: load & process the files
            1. load()
            2. prepare()
            3. convert()
            4. extract_footnotes()
        """
        pass

    def create_html(self, files, text, footnotes):
        """Create the output html file"""
        pass

    def simple_html(self):
        """For debugging purposes. Transform the html and print the text output."""
        if not self.args.filename[0].lower().endswith(('.html', '.htm')):
            print("Error: not an html file")
            return
        html_file = PgdpFileHtml(self.args)
        html_file.load(self.args.filename[0])
        html_file.prepare()
        html_file.convert()
        html_file.extract_footnotes()
        print(html_file.text)

    @staticmethod
    def check_char(files, char_best, char_other):
        """Check whether each file has the 'best' character. If not, add a conversion request.
        This is used for instance if one version uses curly quotes while the other uses straight.
        In that case, we need to convert one into the other, to get a smaller diff.
        """
        finds_0 = files[0].text.find(char_best)
        finds_1 = files[1].text.find(char_best)
        if finds_0 >= 0 and finds_1 >= 0:  # Both have it
            return
        if finds_0 == -1 and finds_1 == -1:  # Neither has it
            return
        # Downgrade one version
        if finds_0 > 0:
            files[0].transform_func.append(lambda text: text.replace(char_best, char_other))
        else:
            files[1].transform_func.append(lambda text: text.replace(char_best, char_other))


def diff_css():
    """CSS used to display the diffs"""
    return """
body {
    margin-left: 5%;
    margin-right: 5%;
}

del {
    text-decoration: none;
    border: 1px solid black;
    color: #700000 ;
    background-color: #f4f4f4;
    font-size: larger;
}
ins {
    text-decoration: none;
    border: 1px solid black;
    color: green;
    font-weight: bold;
    background-color: #f4f4f4;
    font-size: larger;
}
.lineno { margin-right: 3em; }
.sep4 { margin-top: 4em; }
.bbox { margin-left: auto;
    margin-right: auto;
    border: 1px dashed;
    padding: 0em 1em 0em 1em;
    background-color: #F0FFFF;
    width: 90%;
    max-width: 50em;
}
.center { text-align:center; }

/* Use a CSS counter to number each diff. */
body {
  counter-reset: diff;  /* set diff counter to 0 */
}
hr:before {
  counter-increment: diff; /* inc the diff counter ... */
  content: "Diff " counter(diff) ": "; /* ... and display it */
}

.error-border { border-style:double; border-color:red; border-width:15px; }
"""


# noinspection PyPep8
def html_usage(filename1, filename2):
    """Describe how to use the diffs"""
    # noinspection PyPep8
    return """
    <div class="bbox">
      <p class="center">— Note —</p>
      <p>
        The first number is the line number in the first file (""" + filename1 + """)<br />
        The second number is the line number in the second file (""" + filename2 + """)<br />
        Line numbers can sometimes be very approximate.
      </p>
      <p>
        Deleted words that were in the first file but not in the second will appear <del>like
         this</del>.<br />
        Inserted words that were in the second file but not in the first will appear <ins>like
         this</ins>.
      </p>
    </div>
    """


def output_html(html_content, filename1, filename2):
    """Outputs a complete HTML file"""
    print("""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
    <meta http-equiv="Content-Style-Type" content="text/css" />
    <title>
      Compare """ + filename1 + " and " + filename2 + """
    </title>
    <style type="text/css">
""")

    print(diff_css())

    print("""
    </style>
  </head>
<body>
""")
    print("<h1>" + filename1 + " and " + filename2 + "</h1>")
    print(html_usage(filename1, filename2))
    # print('<p>Custom CSS added on command line: ' + " ".join(args.css) + '</p>')
    print(html_content)
    print("""
  </body>
</html>
""")


def main():
    """Main program"""
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
    args = parser.parse_args()

    compare = PPComp(args)
    if args.simple_html:
        compare.simple_html()
    else:
        html_content, fn1, fn2 = compare.do_process
        output_html(html_content, fn1, fn2)


if __name__ == '__main__':
    main()
