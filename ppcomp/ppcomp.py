"""
ppcomp.py - compare text from 2 files, ignoring html and formatting differences, for use by users
of Distributed Proofreaders (https://www.pgdp.net)

Applies various transformations according to program options before passing the files to the Linux
program dwdiff.

Copyright (C) 2012-2013 bibimbop at pgdp
Copyright 2022 Robert Tonsing

Originally written as the standalone program comp_pp.py by bibimbop at PGDP as part of his PPTOOLS
program. It is used as part of the PP Workbench with permission.

Distributable under the GNU General Public License Version 3 or newer.
"""

import argparse
import os
import re
import subprocess
import tempfile
import warnings

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
    """Base class: Store and process a DP text or html file"""

    def __init__(self, args):
        self.args = args
        self.basename = ''
        self.text = ''  # file text
        self.start_line = 1  # line text started, before stripping boilerplate and/or head
        self.footnotes = ''  # footnotes text, if extracted

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
            raise FileNotFoundError("Cannot load file: " + filename) from ex
        if len(self.text) < 10:
            raise SyntaxError("File is too short: " + filename)

    def strip_pg_boilerplate(self):
        """Remove the PG header and footer from the text if present."""
        raise NotImplementedError("Override this method")

    def cleanup(self):
        """Remove tags from the file"""
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
        start_found = False
        for lineno, line in enumerate(self.text.splitlines(), start=1):
            # Find the markers. Unfortunately PG lacks consistency
            if line.startswith((PG_EBOOK_START1, PG_EBOOK_START2)):
                start_found = True
            if start_found and line.endswith("***"):  # may take multiple lines
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
        """Ignore or replace italics and bold html in file from rounds"""
        if self.args.ignore_format:
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
        """suppress proofers notes in file from rounds"""
        if self.args.suppress_proofers_notes:
            self.text = re.sub(r"\[\*\*[^]]*?]", '', self.text)

    def regroup_split_words(self):
        """Regroup split words, must run remove page markers 1st"""
        if self.args.regroup_split_words:
            word_splits = {r"(\w+)-\*(\n+)\*": r"\n\1",  # followed by 0 or more blank lines
                           r"(\w+)-\*(\w+)": r"\1\2"}  # same line
            for key, value in word_splits.items():
                self.text = re.sub(key, value, self.text)

    def ignore_format(self):
        """Remove italics and bold markers in proofed file"""
        if self.args.ignore_format:
            self.text = re.sub(r"_((.|\n)+?)_", r'\1', self.text)
            self.text = re.sub(r"=((.|\n)+?)=", r'\1', self.text)

    def remove_thought_breaks(self):
        """Remove thought breaks (5 spaced asterisks)"""
        self.text = re.sub(r"\*\s+\*\s+\*\s+\*\s+\*", '', self.text)

    def suppress_footnote_tags(self):
        """Remove footnote tags"""
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
        """Perform cleanup for this type of file"""
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
        if self.args.extract_footnotes:
            if from_pgdp_rounds:  # always [Footnote 1: text]
                self.extract_footnotes_pgdp()
            else:  # probably [1] text
                self.extract_footnotes_pp()
        else:
            self.suppress_footnote_tags()
        self.suppress_illustration_tags()
        self.suppress_sidenote_tags()

    def extract_footnotes_pgdp(self):
        """ Extract the footnotes from an F round
        Start with [Footnote ... and finish with ] at the end of a line
        """
        # Note: this is really dirty code. Should rewrite. Don't use current_fnote[0].
        in_footnote = False  # currently processing a footnote
        current_fnote = []  # keeping current footnote
        text = []  # new text without footnotes
        footnotes = []

        for line in self.text.splitlines():
            # New footnote?
            if "[Footnote" in line:
                in_footnote = True
                if "*[Footnote" in line:
                    # Join to previous - Remove the last from the existing footnotes.
                    line = line.replace("*[Footnote: ", "")
                    current_fnote, footnotes = footnotes[-1], footnotes[:-1]
                else:
                    line = re.sub(r"\[Footnote \d+: ", "", line)
                    current_fnote = [-1, ""]
            # Inside a footnote?
            if in_footnote:
                current_fnote[1] = "\n".join([current_fnote[1], line])
                # End of footnote? We don't try to regroup yet
                if line.endswith(']'):
                    current_fnote[1] = current_fnote[1][:-1]
                    footnotes.append(current_fnote)
                    in_footnote = False
                elif line.endswith("]*"):  # Footnote continuation
                    current_fnote[1] = current_fnote[1][:-2]
                    footnotes.append(current_fnote)
                    in_footnote = False
            else:
                text.append(line)

        # Rebuild text, now without footnotes
        self.text = '\n'.join(text)
        self.footnotes = "\n".join([x[1] for x in footnotes])

    def extract_footnotes_pp(self):
        """Extract footnotes from a PP text file. Text is iterable. Returns the text as an iterable,
        without the footnotes, and footnotes as a list of (footnote string id, line number of the
        start of the footnote, list of strings comprising the footnote). fn_regexes is a list of
        (regex, fn_type) that identify the beginning and end of a footnote. The fn_type is 1 when
        a ] terminates it, or 2 when a new block terminates it.
        """
        # RT: Why is this different from extract_footnotes_pgdp, except
        # tidied would be "[1] text" instead of [Footnote 1: text]? 1st regex?

        # If the caller didn't give a list of regex to identify the
        # footnotes, build one, taking only the most common.
        all_regexes = [(r"(\s*)\[([\w-]+)\](.*)", 1),
                       (r"(\s*)\[Note (\d+):( .*|$)", 2),
                       (r"(      )Note (\d+):( .*|$)", 1)]
        regex_count = [0] * len(all_regexes)  # i.e. [0, 0, 0]

        text_lines = self.text.splitlines()

        for block, empty_lines in self.get_block(text_lines):
            if not block or not len(block):
                continue
            for i, (regex, fn_type) in enumerate(all_regexes):
                matches = re.match(regex, block[0])
                if matches:
                    regex_count[i] += 1
                    break
        # Pick the regex with the most matches
        fn_regexes = [all_regexes[regex_count.index(max(regex_count))]]

        # Different types of footnote. 0 means not in footnote.
        cur_fn_type, cur_fn_indent = 0, 0
        footnotes = []
        text = []
        prev_block = None

        for block, empty_lines in self.get_block(text_lines):
            # Is the block a new footnote?
            next_fn_type = 0
            if len(block):
                for (regex, fn_type) in fn_regexes:
                    matches = re.match(regex, block[0])
                    if matches:
                        if matches.group(2).startswith(("Illustration", "Décoration",
                                                        "Bandeau", "Logo", "Ornement")):
                            # An illustration, possibly inside a footnote. Treat
                            # as part of text or footnote.
                            continue
                        next_fn_type = fn_type
                        # Update first line of block, because we want the number outside.
                        block[0] = matches.group(3)
                        break

            # Try to close previous footnote
            next_fn_indent = None
            if cur_fn_type:
                if next_fn_type:
                    # New block is footnote, so it ends the previous footnote
                    footnotes += prev_block + [""]
                    text += [""] * (len(prev_block) + 1)
                    cur_fn_type, cur_fn_indent = next_fn_type, next_fn_indent
                elif block[0].startswith(cur_fn_indent):
                    # Same indent or more. This is a continuation. Merge with one empty line.
                    block = prev_block + [""] + block
                else:
                    # End of footnote - current block is not a footnote
                    footnotes += prev_block + [""]
                    text += [""] * (len(prev_block) + 1)
                    cur_fn_type = 0
            if not cur_fn_type and next_fn_type:
                # Account for new footnote
                cur_fn_type, cur_fn_indent = next_fn_type, next_fn_indent
            if cur_fn_type and (empty_lines >= 2 or
                                (cur_fn_type == 2 and block[-1].endswith("]"))):
                # End of footnote
                if cur_fn_type == 2 and block[-1].endswith("]"):
                    # Remove terminal bracket
                    block[-1] = block[-1][:-1]
                footnotes += block
                text += [""] * (len(block))
                cur_fn_type = 0
                block = None
            if not cur_fn_type:
                # Add to text, with white lines
                text += (block or []) + [""] * empty_lines
                footnotes += [""] * (len(block or []) + empty_lines)

            prev_block = block
        # Rebuild text, now without footnotes
        self.text = '\n'.join(text)
        self.footnotes = '\n'.join(footnotes)

    @staticmethod
    def get_block(pp_text):
        """Generator to get a block of text, followed by the number of empty lines."""
        empty_lines = 0
        block = []
        for line in pp_text:
            if len(line):
                if empty_lines:  # one or more empty lines will stop a block
                    yield block, empty_lines
                    block = []
                    empty_lines = 0
                block += [line]
            else:
                empty_lines += 1
        yield block, empty_lines


class PgdpFileHtml(PgdpFile):
    """Store and process a DP html file."""

    def __init__(self, args):
        super().__init__(args)
        self.tree = None
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
            for node in self.tree.iter():
                if not isinstance(node, (etree._Comment, etree._ProcessingInstruction)):
                    node.tag = etree.QName(node).localname
            etree.cleanup_namespaces(self.tree)  # Remove unused namespace declarations

        if not filename.lower().endswith(('.html', '.htm')):
            raise SyntaxError("Not an html file: " + filename)
        super().load(filename)
        # ignore warning caused by "xml:lang"
        warnings.filterwarnings("ignore", message='Coercing non-XML name: xml:lang')
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
                self.start_line = lineno + 1
                break

        # remove the head - we only want the body
        head = self.tree.find('head')
        if head is not None:
            head.getparent().remove(head)

    def strip_pg_boilerplate(self):
        """Remove the PG header and footer from the text if present."""
        if -1 == self.text.find(PG_EBOOK_START1):
            return
        # start: from <body to <div>*** START OF THE ...</div>
        # end: from <div>*** END OF THE ...</div> to </body
        start_found = False
        end_found = False
        for node in self.tree.find('body').iter():
            if node.tag == "div" and node.text and node.text.startswith(PG_EBOOK_START1):
                start_found = True
                node.text = ''
                node.tail = ''
            elif node.tag == 'div' and node.text and node.text.startswith(PG_EBOOK_END1):
                end_found = True
            if end_found or not start_found:
                node.text = ''
                node.tail = ''
        # we need the start line, html5parser does not save source line
        for lineno, line in enumerate(self.text.splitlines(), start=1):
            if PG_EBOOK_START1 in line:
                self.start_line = lineno + 1
                break


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
        if not self.args.css_bold:
            self.args.css_bold = '='
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

    def remove_nbspaces(self):
        """Remove non-breakable spaces between numbers. For instance, a
        text file could have 250000, and the html could have 250 000.
        """
        # Todo: &nbsp;, &#160;, &#x00A0;
        if self.args.suppress_nbsp_num:
            self.text = re.sub(r"(\d)\u00A0(\d)", r"\1\2", self.text)

    def remove_soft_hyphen(self):
        """Suppress shy (soft hyphen)"""
        # Todo: &#173;, &#x00AD;
        self.text = re.sub(r"\u00AD", r"", self.text)

    def cleanup(self):
        """Perform cleanup for this type of file - build up a list of CSS transform rules,
        process them against tree, then convert to text.
        """
        self.strip_pg_boilerplate()
        # load default CSS for transformations
        if not self.args.css_no_default:
            self.mycss = DEFAULT_TRANSFORM_CSS
        self.css_smallcaps()
        self.css_bold()
        self.css_illustration()
        self.css_sidenote()
        self.css_custom_css()
        self.process_css()  # process transformations

        self.extract_footnotes()

        # Transform html into text for character search.
        self.text = etree.XPath("string(/)")(self.tree)
        # removes line breaks
        # self.char_text = etree.XPath("normalize-space(/)")(self.tree)

        # text fixups
        self.remove_nbspaces()
        self.remove_soft_hyphen()

    @staticmethod
    def text_transform(val, errors: list):
        """Transform smcaps"""
        if len(val.value) != 1:
            errors += [(val.line, val.column, val.name + " takes 1 argument")]
        else:
            value = val.value[0].value
            if value == "uppercase":
                return lambda x: x.upper()
            if value == "lowercase":
                return lambda x: x.lower()
            if value == "capitalize":
                return lambda x: x.title()
            errors += [(val.line, val.column,
                        val.name + " accepts only 'uppercase', 'lowercase' or 'capitalize'")]
        return None

    @staticmethod
    def text_replace(val, errors: list):
        """Skip S (spaces) tokens"""
        values = [v for v in val.value if v.type != "S"]
        if len(values) != 2:
            errors += [(val.line, val.column, val.name + " takes 2 string arguments")]
            return None
        return lambda x: x.replace(values[0].value, values[1].value)

    @staticmethod
    def text_move(val, errors: list):
        """Move a node"""
        values = [v for v in val.value if v.type != "S"]
        if len(values) < 1:
            errors += [(val.line, val.column, val.name + " takes at least one argument")]
            return None
        f_move = []
        for value in values:
            if value.value == 'parent':
                f_move.append(lambda el: el.getparent())
            elif value.value == 'prev-sib':
                f_move.append(lambda el: el.getprevious())
            elif value.value == 'next-sib':
                f_move.append(lambda el: el.getnext())
            else:
                errors += [(val.line, val.column, val.name + " invalid value " + value.value)]
                f_move = None
                break
        return f_move

    def process_css(self):
        """Process each rule from our transformation CSS"""
        stylesheet = tinycss.make_parser().parse_stylesheet(self.mycss)
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
                    pass  # result depends on element and pseudo elements
                elif val.name == "text-transform":
                    f_transform = self.text_transform(val, property_errors)
                elif val.name == "_replace_with_attr":
                    def f_replace_with_attr(el):
                        return el.attrib[val.value[0].value]
                elif val.name == "text-replace":
                    f_text_replace = self.text_replace(val, property_errors)
                elif val.name == "display":
                    # support display none only. So ignore "none" argument
                    f_element_func = PgdpFileHtml.clear_element
                elif val.name == "_graft":
                    f_move = self.text_move(val, property_errors)
                else:
                    property_errors += [(val.line, val.column, "Unsupported property " + val.name)]
                    continue

                # iterate through each selector in the rule
                for selector in cssselect.parse(rule.selector.as_css()):
                    xpath = cssselect.HTMLTranslator().selector_to_xpath(selector)
                    find = etree.XPath(xpath)

                    # find each matching element in the HTML document
                    for element in find(self.tree):
                        # replace text with content of an attribute.
                        if f_replace_with_attr:
                            element.text = f_replace_with_attr(element)
                        if val.name == 'content':
                            v_content = self.new_content(element, val)
                            if selector.pseudo_element == "before":
                                element.text = v_content + (element.text or '')  # opening tag
                            elif selector.pseudo_element == "after":
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

        return self.css_errors(stylesheet.errors, property_errors)

    def css_errors(self, stylesheet_errors, property_errors):
        """Collect transformation CSS errors"""
        css_errors = ''
        if stylesheet_errors or property_errors:
            css_errors = "<div class='error-border bbox'><p>Error(s) in the" \
                         "  transformation CSS:</p><ul>"
            i = 0
            # if the default css is included, take the offset into account
            if not self.args.css_no_default:
                i = DEFAULT_TRANSFORM_CSS.count('\n')
            for err in stylesheet_errors:
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

        def strip_note_tag(string):
            """Remove note tag and number. "Note 123: lorem ipsum" becomes "lorem ipsum"."""
            for regex in [r"\s*\[([\w-]+)\](.*)",
                          r"\s*([\d]+)\s+(.*)",
                          r"\s*([\d]+):(.*)",
                          r"\s*Note ([\d]+):\s+(.*)"]:
                match = re.match(regex, string, re.DOTALL)
                if match:
                    return match.group(2)
            return string  # That may be bad

        if not self.args.extract_footnotes:
            return
        footnotes = []
        # Special case for PPers who do not keep the marking around
        # the whole footnote. They only mark the first paragraph.
        elements = etree.XPath("//div[@class='footnote']")(self.tree)
        if len(elements) == 1:
            element = elements[0]
            # Clean footnote number
            for node in element:
                footnotes += [strip_note_tag(node.xpath("string()"))]
            # Remove the footnote from the main document
            element.getparent().remove(element)
        else:
            for find in ["//div[@class='footnote']",
                         "//div[@id[starts-with(.,'FN_')]]",
                         "//p[a[@id[starts-with(.,'Footnote_')]]]",
                         "//div/p[span/a[@id[starts-with(.,'Footnote_')]]]",
                         "//p[@class='footnote']"]:
                for element in etree.XPath(find)(self.tree):
                    # Grab the text and remove the footnote number
                    footnotes += [strip_note_tag(element.xpath("string()"))]
                    # Remove the footnote from the main document
                    element.getparent().remove(element)
                if footnotes:  # found them, stop now
                    break
        # save as text string
        self.footnotes = "\n".join(footnotes)


DEFAULT_TRANSFORM_CSS = '''
        /* Italics */
        i:before, cite:before, em:before,
        i:after, cite:after, em:after { content: "_"; }

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

    def do_process(self):
        """Main routine: load & process the files"""
        files = [None, None]
        for i, fname in enumerate(self.args.filename):
            if fname.lower().endswith(('.html', '.htm')):
                files[i] = PgdpFileHtml(self.args)
            else:
                files[i] = PgdpFileText(self.args)
            files[i].load(fname)
            files[i].cleanup()  # perform cleanup for each type of file

        # perform common cleanup for both files
        self.check_characters(files)

        # Compare the two versions
        main_diff = self.compare_texts(files[0].text, files[1].text)
        if self.args.extract_footnotes:
            fnotes_diff = self.compare_texts(files[0].footnotes, files[1].footnotes)
        else:
            fnotes_diff = ""
        html_content = self.create_html(files, main_diff, fnotes_diff)
        return html_content, files[0].basename, files[1].basename

    def compare_texts(self, text1, text2):
        """Compare two sources, using dwdiff"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as temp1, \
                tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as temp2:
            temp1.write(text1)
            temp2.write(text2)
            temp1.flush()
            temp2.flush()
            repo_dir = os.environ.get("OPENSHIFT_DATA_DIR", "")
            if repo_dir:
                dwdiff_path = os.path.join(repo_dir, "bin", "dwdiff")
            else:
                dwdiff_path = "dwdiff"

            # -P Use punctuation characters as delimiters.
            # -R Repeat the begin and end markers at the start and end of line if a change crosses
            #    a newline.
            # -C 2 Show <num> lines of context before and after each changes.
            # -L Show line numbers at the start of each line.
            cmd = [dwdiff_path,
                   "-P",
                   "-R",
                   "-C 2",
                   "-L",
                   "-w ]COMPPP_START_DEL[",
                   "-x ]COMPPP_STOP_DEL[",
                   "-y ]COMPPP_START_INS[",
                   "-z ]COMPPP_STOP_INS["]
            if self.args.ignore_case:
                cmd += ["--ignore-case"]
            cmd += [temp1.name, temp2.name]

            # This shouldn't be needed if openshift was utf8 by default.
            env = os.environ.copy()
            env["LANG"] = "en_US.UTF-8"
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env) as process:
                return process.stdout.read().decode('utf-8')

    def create_html(self, files, text, footnotes):
        """Create the output html file"""

        def massage_input(txt, start0, start1):
            # Massage the input
            replacements = {"&": "&amp;",
                            "<": "&lt;",
                            ">": "&gt;",
                            "]COMPPP_START_DEL[": "<del>",
                            "]COMPPP_STOP_DEL[": "</del>",
                            "]COMPPP_START_INS[": "<ins>",
                            "]COMPPP_STOP_INS[": "</ins>"}
            newtext = txt
            for key, value in replacements.items():
                newtext = newtext.replace(key, value)
            if newtext:
                newtext = "<hr /><pre>\n" + newtext
            newtext = newtext.replace("\n--\n", "\n</pre><hr /><pre>\n")
            newtext = re.sub(r"^\s*(\d+):(\d+)",
                             lambda m: "<span class='lineno'>{0} : {1}</span>".format(
                                 int(m.group(1)) + start0, int(m.group(2)) + start1),
                             newtext, flags=re.MULTILINE)
            if newtext:
                newtext += "</pre>\n"
            return newtext

        # Find the number of diff sections
        nb_diffs_text = 0
        if text:
            nb_diffs_text = len(re.findall("\n--\n", text)) + 1
            # Text, with correct (?) line numbers
            text = massage_input(text, files[0].start_line, files[1].start_line)
        html_content = "<div>"
        if nb_diffs_text == 0:
            html_content += "<p>There is no diff section in the main text.</p>"
        elif nb_diffs_text == 1:
            html_content += "<p>There is 1 diff section in the main text.</p>"
        else:
            html_content += f"<p>There are {nb_diffs_text} diff sections in the main text.</p>"

        if footnotes:
            nb_diffs_footnotes = len(re.findall("\n--\n", footnotes or "")) + 1
            # Footnotes - line numbers are meaningless right now. We could fix that.
            footnotes = massage_input(footnotes, 0, 0)
            html_content += "<p>Footnotes are diff'ed separately <a href='#footnotes'>here</a></p>"
            if nb_diffs_footnotes == 0:
                html_content += "<p>There is no diff section in the footnotes.</p>"
            elif nb_diffs_footnotes == 1:
                html_content += "<p>There is 1 diff section in the footnotes.</p>"
            else:
                html_content += f"<p>There are {nb_diffs_footnotes}" \
                                " diff sections in the footnotes.</p>"
        else:
            if self.args.extract_footnotes:
                html_content += "<p>There is no diff section in the footnotes.</p>"

        if nb_diffs_text:
            html_content += "<h2 class='sep4'>Main text</h2>"
            html_content += text
        if footnotes:
            html_content += "<h2 id='footnotes' class='sep4'>Footnotes</h2>"
            html_content += "<pre class='sep4'>"
            html_content += footnotes
            html_content += "</pre>"
        html_content += "</div>"
        return html_content

    def simple_html(self):
        """Debugging only, transform the html and print the text output"""
        if not self.args.filename[0].lower().endswith(('.html', '.htm')):
            print("Error: 1st file must be an html file")
            return
        html_file = PgdpFileHtml(self.args)
        html_file.load(self.args.filename[0])
        html_file.cleanup()
        print(html_file.text)
        with open('outhtml.txt', 'w', encoding='utf-8') as file:
            file.write(html_file.text)

    @staticmethod
    def check_characters(files):
        """Check whether each file has the 'best' character. If not, add a conversion request.
        This is used for instance if one version uses curly quotes while the other uses straight.
        In that case, we need to convert one into the other, to get a smaller diff.
        """
        character_checks = {
            '’': "'",  # close curly quote to straight
            '‘': "'",  # open curly quote to straight
            '”': '"',  # close curly quotes to straight
            '“': '"',  # open curly quotes to straight
            'º': 'o',  # ordinal o to letter o
            'ª': 'a',  # ordinal a to letter a
            '–': '-',  # ndash to regular dash
            '—': '--',  # mdash to regular dashes
            '½': '-1/2',
            '¼': '-1/4',
            '¾': '-3/4',
            '⁄': '/',  # fraction slash
            '′': "'",  # prime
            '″': "''",  # double prime
            '‴': "'''",  # triple prime
            '₀': '0',  # subscript 0
            '₁': '1',  # subscript 1
            '₂': '2',  # subscript 2
            '₃': '3',  # subscript 3
            '₄': '4',  # subscript 4
            '₅': '5',  # subscript 5
            '₆': '6',  # subscript 6
            '₇': '7',  # subscript 7
            '₈': '8',  # subscript 8
            '₉': '9',  # subscript 9
            '⁰': '0',  # superscript 0
            '¹': '1',  # superscript 1
            '²': '2',  # superscript 2
            '³': '3',  # superscript 3
            '⁴': '4',  # superscript 4
            '⁵': '5',  # superscript 5
            '⁶': '6',  # superscript 6
            '⁷': '7',  # superscript 7
            '⁸': '8',  # superscript 8
            '⁹': '9'  # superscript 9
        }

        for char_best, char_other in character_checks.items():
            finds_0 = files[0].text.find(char_best)
            finds_1 = files[1].text.find(char_best)
            # Todo: should apply to footnotes too
            if finds_0 >= 0 and finds_1 >= 0:  # Both have it
                continue
            if finds_0 == -1 and finds_1 == -1:  # Neither has it
                continue
            # Downgrade one version
            if finds_0 >= 0:
                files[0].text.replace(char_best, char_other)
            else:
                files[1].text.replace(char_best, char_other)


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
                        help="HTML: Process just the html file and print the output (debug)")
    args = parser.parse_args()

    if args.extract_footnotes and args.suppress_footnote_tags:
        raise SyntaxError("Cannot use both --extract-footnotes and --suppress-footnote-tags")

    compare = PPComp(args)
    if args.simple_html:
        compare.simple_html()
    else:
        html_content, file1, file2 = compare.do_process()
        output_html(html_content, file1, file2)


def dumptree(tree):
    """Save tree for debug"""
    with open('tmptree.txt', 'w', encoding='utf-8') as file:
        for node in tree.iter():
            if node.text:
                file.write(node.tag + ': ' + node.text + '\n')
            else:
                file.write(node.tag + '\n')


if __name__ == '__main__':
    main()
