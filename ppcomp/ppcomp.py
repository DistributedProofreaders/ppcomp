import argparse

"""
ppcomp.py - compare text from 2 files, ignoring html and formatting differences, for use by users
of Distributed Profreaders (https://www.pgdp.net)

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
    """Base class: Store and process a DP text or html file"""

    def __init__(self, args):
        pass

    def load(self, filename):
        """Load the file"""
        pass

    def process_args(self):
        """Process command line arguments"""
        pass

    def convert(self):
        """Remove markup from the text"""
        pass

    def analyze(self):
        """Clean then analyse the contents of a file"""
        pass

    def extract_footnotes(self):
        """Extract the footnotes"""
        pass

    def transform(self):
        """Final transformation pass"""
        pass


class PgdpFileText(PgdpFile):
    """Store and process a DP text file"""

    def __init__(self, args):
        super().__init__(args)
        self.from_pgdp_rounds = False

    def load(self, filename):
        """Load the file"""
        pass

    def process_args(self):
        """Process command line arguments"""
        pass

    def convert(self):
        """Remove markup from the text"""
        pass

    def analyze(self):
        """Clean then analyse the contents of a file"""
        pass

    def extract_footnotes(self):
        """Extract the footnotes."""
        pass

    def transform(self):
        """Final transformation pass"""
        pass


class PgdpFileHtml(PgdpFile):
    """Store and process a DP html file."""

    def __init__(self, args):
        super().__init__(args)

    def load(self, filename):
        """Load the file"""
        pass

    def process_args(self):
        """Process command line arguments"""
        pass

    def convert(self):
        """Remove markup from the text"""
        pass

    def analyze(self):
        """Clean then analyse the content of a file"""
        pass

    def extract_footnotes(self):
        """Extract the footnotes"""
        pass

    def transform(self):
        """Final transformation pass"""
        pass


class PPComp:
    """Compare two files."""
    def __init__(self, args):
        self.args = args

    def compare_texts(self, text1, text2):
        """Compare two sources. We could have used the difflib module, but it's too slow:
           for line in difflib.unified_diff(f1.words, f2.words):
               print(line)
        Use dwdiff instead.
        """
        pass

    def do_process():
        """Main routine: load & process the files"""
        pass

    def create_html(self, files, text, footnotes):
        """Create the output html file"""
        pass

    def simple_html(self):
        """For debugging purposes. Transform the html and print the text output."""
        pass


######################################
# CSS used to display the diffs.
def diff_css():
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
        Deleted words that were in the first file but not in the second will appear <del>like this</del>.<br />
        Inserted words that were in the second file but not in the first will appear <ins>like this</ins>.
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
        _, html_content, fn1, fn2 = compare.do_process
        output_html(html_content, fn1, fn2)


if __name__ == '__main__':
    main()
