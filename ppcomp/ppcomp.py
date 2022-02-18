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

import argparse
import os
import re

import cssselect
import tinycss
from lxml import etree
from lxml.html import html5parser

PG_EBOOK_START1 = "*** START OF THE PROJECT GUTENBERG EBOOK"
PG_EBOOK_START2 = "*** START OF THIS PROJECT GUTENBERG EBOOK"
PG_EBOOK_END1 = "*** END OF THE PROJECT GUTENBERG EBOOK"
PG_EBOOK_END2 = "*** END OF THIS PROJECT GUTENBERG EBOOK"
PG_EBOOK_START_REGEX = r".*?\*\*\* START OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*(.*)"


class PgdpFile:
    """Base class: Store and process a DP text or html file
    Function order from PPComp.do_process():
        1. load()
        2. prepare()
        3. convert()
        4. extract_footnotes()
        5. transform()
    """

    def __init__(self, args):
        self.args = args
        self.basename = ''
        self.text = ''  # file text
        self.start_line = 0  # line text started, before stripping boilerplate and/or head
        self.footnotes = ''  # footnotes, if extracted
        self.transform_func = []  # List of transforms to perform

    def load(self, filename):
        """Load a file (text or html)
        Args:
            filename: file pathname
        Vars:
            self.text = contents of file
            self.basename = file base name
        Raises:
            IOError: unable to open file
            SyntaxError: file too short
        """
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
        self.start_line = 1

    def strip_pg_boilerplate(self):
        """Remove the PG header and footer from the text if present."""
        raise NotImplementedError("Override this method")

    def cleanup(self):
        """Remove tags from the file"""
        raise NotImplementedError("Override this method")

    def convert(self):
        """Apply needed text conversions"""
        # handle universal ones here, particular ones in subclass,
        # comparisons (do_process) elsewhere
        for func in self.transform_func:
            self.text = func(self.text)

    def extract_footnotes(self):
        """Extract the footnotes"""
        raise NotImplementedError("Override this method")


class PgdpFileText(PgdpFile):
    """Store and process a DP text file"""

    def load(self, filename):
        """Load the file
        filename: filename to load
        """
        if not filename.lower().endswith('.txt'):
            raise SyntaxError("Not a text file: " + filename)
        super().load(filename)

    def strip_pg_boilerplate(self):
        """Remove the PG header and footer from the text if present."""
        new_text = []
        for lineno, line in enumerate(self.text.splitlines(), start=1):
            # Find the markers. Unfortunately PG lacks consistency
            if line.startswith((PG_EBOOK_START1, PG_EBOOK_START2)):
                new_text = []  # PG found, remove previous lines
                self.start_line = lineno + 1
            elif line.startswith((PG_EBOOK_END1, PG_EBOOK_END2)):
                break  # ignore following lines
            else:
                new_text.append(line)
        self.text = '\n'.join(new_text)

    def remove_paging(self):
        """Remove page markers & blank pages"""
        self.text = re.sub(r"-----File: \w+.png.*", '', self.text)
        self.text = self.text.replace("[Blank Page]", '')

    def remove_block_markup(self):
        """Remove block markup"""
        for markup in ['/*', '*/', '/#', '#/', '/P', 'P/', '/F', 'F/', '/X', 'X/']:
            self.text = self.text.replace('\n' + markup + '\n', '\n\n')

    def remove_formatting(self):
        """Ignore or replace italics and bold html"""
        if self.args.ignore_format:  # silence formatting differences
            for tag in ['<i>', '</i>', '<b>', '</b>']:
                self.text = self.text.replace(tag, '')
        else:
            for tag in ['<i>', '</i>']:
                self.text = self.text.replace(tag, '_')
            for tag in ['<b>', '</b>']:
                self.text = self.text.replace(tag, '=')
        # remove other markup
        self.text = re.sub('<.*?>', '', self.text)

    def suppress_proofers_notes(self):
        """suppress proofers notes"""
        if self.args.suppress_proofers_notes:
            self.text = re.sub(r"\[\*\*[^]]*?]", '', self.text)

    def regroup_split_words(self):
        """Regroup split words"""
        if self.args.regroup_split_words:
            word_splits = {r"(\w+)-\*(\n+)\*": r"\2\1",
                           r"(\w+)-\*_(\n\n)_\*": r"\2\1",
                           r"(\w+)-\*(\w+)": r"\1\2"}
            for key, value in word_splits.items():
                self.text = re.sub(key, value, self.text)

    def ignore_format(self):
        """Remove italics and bold markers"""
        # Todo: these can be perfectly valid characters, need to use regex
        if self.args.ignore_format:
            self.text = self.text.replace('_', '')
            self.text = self.text.replace('=', '')

    def remove_thought_breaks(self):
        """Remove thought breaks (5 spaced asterisks)"""
        self.text = re.sub(r"\*\s+\*\s+\*\s+\*\s+\*", '', self.text)

    def suppress_footnote_tags(self):
        """Remove footnote tags"""
        # Todo: doesn't handle internal ']'
        if self.args.ignore_format or self.args.suppress_footnote_tags:
            self.text = re.sub(r"\[Footnote (\d+): ([^]]*?)]", r"\1 \2", self.text,
                               flags=re.MULTILINE)
            self.text = re.sub(r"\*\[Footnote: ([^]]*?)]", r'\1', self.text, flags=re.MULTILINE)

    def suppress_illustration_tags(self):
        """Remove illustration tags"""
        if self.args.ignore_format or self.args.suppress_illustration_tags:
            self.text = re.sub(r"\[Illustration?: ([^]]*?)]", r'\1', self.text, flags=re.MULTILINE)
            self.text = self.text.replace("[Illustration]", '')

    def suppress_sidenote_tags(self):
        """Remove sidenote tags"""
        if self.args.ignore_format or self.args.suppress_sidenote_tags:
            self.text = re.sub(r"\[Sidenote:([^]]*?)]", r'\1', self.text, flags=re.MULTILINE)

    def cleanup(self):
        """Clean text in preparation for conversions"""
        from_pgdp_rounds = self.basename.startswith('projectID')
        if not from_pgdp_rounds:
            self.strip_pg_boilerplate()
        if self.args.txt_cleanup_type == 'n':  # none
            return

        if from_pgdp_rounds:
            # remove page markers & blank pages
            self.remove_paging()
            if self.args.txt_cleanup_type == 'p':  # proofers, all done
                return
            # else 'b' best effort
            self.remove_block_markup()
            self.remove_formatting()
            self.suppress_proofers_notes()
            self.regroup_split_words()
        else:  # processed text file
            self.ignore_format()
            self.remove_thought_breaks()

        # all text files
        self.suppress_footnote_tags()
        self.suppress_illustration_tags()
        self.suppress_sidenote_tags()

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
        self.body_line = 0  # line number of <body> tag
        self.mycss = ''

    def load(self, filename):
        """Load the file. If parsing succeeded, then self.tree is set, and parser.errors is []
        @param filename: filename to load
        """

        # noinspection PyProtectedMember,Pylint
        def remove_namespace():
            """Remove namespace URI in elements names
            "{http://www.w3.org/1999/xhtml}html" -> "html"
            """
            for elem in self.tree.iter():
                if not isinstance(elem, (etree._Comment, etree._ProcessingInstruction)):
                    elem.tag = etree.QName(elem).localname
            etree.cleanup_namespaces(self.tree)  # Remove unused namespace declarations

        if not filename.lower().endswith(('.html', '.htm')):
            raise SyntaxError("Not an html file: " + filename)
        super().load(filename)
        parser = html5parser.HTMLParser()
        try:
            tree = html5parser.document_fromstring(self.text)
        except Exception as ex:
            raise SyntaxError("File cannot be parsed: " + filename) from ex

        if parser.errors:
            raise SyntaxError("Parsing errors in document: " + filename)

        self.tree = tree.getroottree()
        # remove the namespace from the tags
        remove_namespace()
        # save line number of <body> tag - actual text start
        for lineno, line in enumerate(self.text.splitlines(), start=1):
            if '<body' in line:
                self.body_line = lineno
                break

    def strip_pg_boilerplate(self):
        """Remove the PG header and footer from the text if present."""
        new_text = []
        for lineno, line in enumerate(self.text.splitlines(), start=self.body_line):
            # Find the markers. Unfortunately PG lacks consistency
            if PG_EBOOK_START1 in line or PG_EBOOK_START2 in line:
                new_text = []  # PG found, remove previous lines
                self.start_line = lineno
            elif PG_EBOOK_END1 in line or PG_EBOOK_END2 in line:
                break  # ignore following lines
            else:
                new_text.append(line)
        self.text = '\n'.join(new_text)

    def css_smallcaps(self):
        """Transform small caps"""
        if self.args.css_smcap == 'U':
            self.mycss += ".smcap { text-transform:uppercase; }"
        elif self.args.css_smcap == 'L':
            self.mycss += ".smcap { text-transform:lowercase; }"
        elif self.args.css_smcap == 'T':
            self.mycss += ".smcap { text-transform:capitalize; }"

    def css_bold(self):
        """Surround bold strings with this string"""
        if self.args.css_bold:
            self.mycss += "b:before, b:after { content: " + self.args.css_bold + "; }"

    def css_illustration(self):
        """Add [Illustration: ...] markup"""
        if self.args.css_add_illustration:
            for figclass in ['figcenter', 'figleft', 'figright']:
                self.mycss += '.' + figclass + ':before { content: "[Illustration: "; }'
                self.mycss += '.' + figclass + ':after { content: "]"; }'

    def css_sidenote(self):
        """Add [Sidenote: ...] markup"""
        if self.args.css_add_sidenote:
            self.mycss += '.sidenote:before { content: "[Sidenote: "; }'
            self.mycss += '.sidenote:after { content: "]"; }'

    def css_custom_css(self):
        """--css can be present multiple times, so it's a list"""
        for css in self.args.css:
            self.mycss += css

    def cleanup(self):
        """Setup css transform rules, then process them against tree"""
        # empty the head - we only want the body
        self.tree.find('head').clear()

        # load default CSS for transformations
        if not self.args.css_no_default:
            self.mycss = DEFAULT_TRANSFORM_CSS
        self.css_smallcaps()
        self.css_bold()
        self.css_illustration()
        self.css_sidenote()
        self.css_custom_css()
        self.process_css(self.mycss)

    def convert(self):
        """Apply needed text conversions"""
        # noinspection Pylint
        self.text = etree.XPath("string(/)")(self.tree)
        for func in self.transform_func:
            self.text = func(self.text)

        # zero width space
        if self.args.ignore_0_space:
            self.text = self.text.replace(chr(0x200b), '')

    def process_css(self, mycss):
        """Process each rule from our transformation CSS"""
        stylesheet = tinycss.make_parser().parse_stylesheet(mycss)
        property_errors = []
        for rule in stylesheet.rules:
            # extract values we care about
            f_transform = None
            f_replace_with_attr = None
            f_text_replace = None
            f_element_func = None
            f_move = []

            for val in rule.declarations:
                if val.name == 'content':
                    # result depends on element and pseudo elements
                    pass
                elif val.name == "text-transform":
                    if len(val.value) != 1:
                        property_errors += [(val.line, val.column, val.name + " takes 1 argument")]
                    else:
                        value = val.value[0].value
                        if value == "uppercase":
                            f_transform = lambda x: x.upper()
                        elif value == "lowercase":
                            f_transform = lambda x: x.lower()
                        elif value == "capitalize":
                            f_transform = lambda x: x.title()
                        else:
                            property_errors += [(val.line, val.column,
                                                 val.name + " accepts only 'uppercase',"
                                                            " 'lowercase' or 'capitalize'")]
                elif val.name == "_replace_with_attr":
                    f_replace_with_attr = lambda el: el.attrib[val.value[0].value]
                elif val.name == "text-replace":
                    # skip S (spaces) tokens
                    values = [v for v in val.value if v.type != "S"]
                    if len(values) != 2:
                        property_errors += [(val.line, val.column, val.name
                                             + " takes 2 string arguments")]
                    else:
                        value1 = values[0].value
                        value2 = values[1].value
                        f_text_replace = lambda x: x.replace(value1, value2)
                elif val.name == "display":
                    # support display none only. So ignore "none" argument
                    f_element_func = PgdpFileHtml.clear_element
                elif val.name == "_graft":
                    values = [v for v in val.value if v.type != "S"]
                    if len(values) < 1:
                        property_errors += [(val.line, val.column, val.name
                                             + " takes at least one argument")]
                        continue
                    for value in values:
                        print("[", value.value, "]")
                        if value.value == 'parent':
                            f_move.append(lambda el: el.getparent())
                        elif value.value == 'prev-sib':
                            f_move.append(lambda el: el.getprevious())
                        elif value.value == 'next-sib':
                            f_move.append(lambda el: el.getnext())
                        else:
                            property_errors += [(val.line, val.column, val.name
                                                 + " invalid value " + value.value)]
                            f_move = None
                            break
                    if not f_move:
                        continue
                else:
                    property_errors += [(val.line, val.column, "Unsupported property " + val.name)]
                    continue

                # iterate through each selector in the rule
                for selector in cssselect.parse(rule.selector.as_css()):
                    pseudo_element = selector.pseudo_element
                    xpath = cssselect.HTMLTranslator().selector_to_xpath(selector)
                    find = etree.XPath(xpath)

                    # find each matching element in the HTML document
                    for element in find(self.tree):
                        # replace text with content of an attribute.
                        if f_replace_with_attr:
                            element.text = f_replace_with_attr(element)
                        if val.name == 'content':
                            v_content = self.new_content(element, val)
                            if pseudo_element == "before":
                                element.text = v_content + (element.text or '')  # opening tag
                            elif pseudo_element == "after":
                                element.tail = v_content + (element.tail or '')  # closing tag
                            else:  # replace all content
                                element.text = self.new_content(element, val)
                        if f_transform:
                            self.text_apply(element, f_transform)
                        if f_text_replace:
                            self.text_apply(element, f_text_replace)
                        if f_element_func:
                            f_element_func(element)
                        if f_move:
                            self.move_element(element, f_move)

        css_errors = ''
        if stylesheet.errors or property_errors:
            # There are transformation CSS errors. If the default css
            # is included, take the offset into account.
            i = 0
            if not self.args.css_no_default:
                i = DEFAULT_TRANSFORM_CSS.count('\n')
            css_errors = "<div class='error-border bbox'><p>Error(s) in the" \
                         "  transformation CSS:</p><ul>"
            for err in stylesheet.errors:
                css_errors += f"<li>{err.line - i},{err.column}: {err.reason}</li>"
            for err in property_errors:
                css_errors += f"<li>{err[0] - i},{err[1]}: {err[2]}</li>"
            css_errors += "</ul>"

        return css_errors

    @staticmethod
    def move_element(element, f_move):
        """Move element in tree"""
        parent = element.getparent()
        new = element
        for item in f_move:
            new = item(new)
        # move the tail to the sibling or the parent
        if element.tail:
            sibling = element.getprevious()
            if sibling:
                sibling.tail = (sibling.tail or '') + element.tail
            else:
                parent.text = (parent.text or '') + element.tail
            element.tail = None
        # prune and graft
        parent.remove(element)
        new.append(element)

    @staticmethod
    def new_content(elem, val):
        """Process the "content:" property"""

        def escaped_unicode(element):
            try:
                return bytes(element.group(0), 'utf8').decode('unicode-escape')
            except UnicodeDecodeError:
                return element.group(0)

        escaped_unicode_re = re.compile(r"\\u[0-9a-fA-F]{4}")
        result = ""
        for token in val.value:
            if token.type == "STRING":  # e.g. { content: "xyz" }
                result += escaped_unicode_re.sub(escaped_unicode, token.value)
            elif token.type == "FUNCTION":
                if token.function_name == 'attr':  # e.g. { content: attr(title) }
                    result += elem.attrib.get(token.content[0].value, "")
            elif token.type == "IDENT":
                if token.value == "content":  # identity, e.g. { content: content }
                    result += elem.text
        return result

    @staticmethod
    def text_apply(tree_elem, func):
        """Apply a function to every sub-element's .text and .tail, and element's .text"""
        if tree_elem.text:
            tree_elem.text = func(tree_elem.text)
        for sub in tree_elem.iter():
            if sub == tree_elem:
                continue
            if sub.text:
                sub.text = func(sub.text)
            if sub.tail:
                sub.tail = func(sub.tail)

    @staticmethod
    def clear_element(element):
        """In an XHTML tree, remove all sub-elements of a given element.
        We can't properly remove an XML element while traversing the tree. But we can clear it.
        Remove its text and children. However, the tail must be preserved because it points to
        the next element, so re-attach.
        """
        tail = element.tail
        element.clear()
        element.tail = tail

    def extract_footnotes(self):
        """Extract the footnotes"""
        if not self.args.extract_footnotes:
            return


DEFAULT_TRANSFORM_CSS = '''
        /* Italics */
        i:before, cite:before, em:before,
        i:after, cite:after, em:after, { content: "_"; }

        /* Bold */
        b:before, bold:before,
        b:after, bold:after { content: "="; }

        /* line breaks with <br /> will be ignored by normalize-space().
         * Add a space in all of them to work around. */
        br:before { content: " "; }

        /* Add spaces around td tags. */
        td:before, td:after { content: " "; }

        /* Remove page numbers. It seems every PP has a different way. */
        span[class^="pagenum"],
        p[class^="pagenum"],
        div[class^="pagenum"],
        span[class^="pageno"],
        p[class^="pageno"],
        div[class^="pageno"],
        p[class^="page"],
        span[class^="pgnum"],
        div[id^="Page_"] { display: none }

        /* Superscripts, Subscripts */
        sup:before              { content: "^{"; }
        sub:before              { content: "_{"; }
        sup:after, sub:after    { content: "}"; }
    '''


class PPComp:
    """Compare two files."""

    def __init__(self, args):
        self.args = args

    def convert_both(self):
        """Apply various conversions to both files"""
        raise NotImplementedError("Method not implemented")

    def compare_texts(self, text1, text2):
        """Compare two sources, using dwdiff"""
        raise NotImplementedError("Method not implemented")

    def do_process(self):
        """Main routine: load & process the files
            1. load()
            2. prepare()
            3. convert()
            4. extract_footnotes()
        """
        raise NotImplementedError("Method not implemented")

    def create_html(self, files, text, footnotes):
        """Create the output html file"""
        raise NotImplementedError("Method not implemented")

    def simple_html(self):
        """Debugging only, transform the html and print the text output"""
        if not self.args.filename[0].lower().endswith(('.html', '.htm')):
            print("Error: 1st file must be an html file")
            return
        html_file = PgdpFileHtml(self.args)
        html_file.load(self.args.filename[0])
        html_file.cleanup()
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
