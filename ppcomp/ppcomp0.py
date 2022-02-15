#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
import subprocess
import tempfile

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
    """Base class: Store and process a DP text or html file."""
    def __init__(self, args):
        self.basename = ""
        self.text = None
        self.file_text = None
        self.char_text = None
        self.words = None
        self.args = args
        # œ ligature - has_oe_ligature and has_oe_dp are mutually exclusive
        self.has_oe_ligature = False  # the real thing
        self.has_oe_dp = False  # DP type: [oe]
        self.transform_func = []  # List of transforms to perform
        self.footnotes = ""  # Footnotes, if extracted
        self.start_line = 0  # First line of the text. This is where <body> is for html.

    def load_file(self, fname):
        """Load a file (text or html)."""
        self.basename = os.path.basename(fname)
        try:
            text = open(fname, 'r', encoding='utf-8').read()
        except UnicodeError:
            text = open(fname, 'r', encoding='latin-1').read()
        except FileNotFoundError:
            raise IOError("Cannot load file: " + fname)

        if len(text) < 10:
            raise SyntaxError("File is too short: " + fname)

        return text

    def load(self, filename):
        """Load the file"""
        pass

    def process_args(self):
        """Process command line arguments"""
        pass

    def convert(self):
        """Remove markup from the file"""
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
    """Store and process a DP text file."""

    def __init__(self, args):
        super().__init__(args)
        self.from_pgdp_rounds = False

    def load(self, filename):
        """Load the file"""
        self.file_text = self.load_file(filename).splitlines()
        self.from_pgdp_rounds = os.path.basename(self.basename).startswith('projectID')

    def process_args(self):
        if not self.from_pgdp_rounds:
            #self.strip_pg_boilerplate()
            pass

    def strip_pg_boilerplate(self):
        """Remove the PG header and footer from a text version if present."""
        new_text = []
        for lineno, line in enumerate(self.text, start=1):
            # Find the markers. Unfortunately PG lacks consistency
            if line.startswith((PG_EBOOK_START1, PG_EBOOK_START2)):
                new_text = []  # PG found, remove previous lines
                self.start_line = lineno
            elif line.startswith((PG_EBOOK_END1, PG_EBOOK_END2)):
                break  # ignore following lines
            else:
                new_text.append(line)
        self.text = new_text

    def analyze(self):
        """Clean then analyse the content of a file. Decides if it is PP version, a DP
        version, ..."""

        # Unsplit lines
        self.text = '\n'.join(self.file_text)

        # Keep a copy to search for characters
        self.char_text = self.text

        # Check for œ, or [oe]
        if self.text.find('œ') != -1 or self.text.find('Œ') != -1:
            self.has_oe_ligature = True
        elif self.text.find('[oe]') != -1 or self.text.find('[OE]') != -1:
            self.has_oe_dp = True

    def convert(self):
        """Remove markup from the text."""
        if self.args.txt_cleanup_type == "n":  # none
            return

        # Original text file from rounds?
        if self.from_pgdp_rounds:
            # Clean page numbers & blank pages
            self.text = re.sub(r"-----File: \w+.png.*", '', self.text)
            self.text = re.sub(r"\[Blank Page]", '', self.text)

            if self.args.txt_cleanup_type == "p":  # proofers, all done
                return

            # Remove block markup
            block_markup = ["/*", "*/",
                            "/#", "#/",
                            "/P", "P/",
                            "/F", "F/",
                            "/X", "X/"]
            for item in block_markup:
                self.text = self.text.replace("\n" + item + "\n", "\n\n")

            # Ignore or replace italics and bold html
            if self.args.ignore_format:  # "Silence formatting differences"
                for item in ["<i>", "</i>", "<b>", "</b>"]:
                    self.text = self.text.replace(item, "")
            else:
                for item in ["<i>", "</i>"]:
                    self.text = self.text.replace(item, "_")
                for item in ["<b>", "</b>"]:
                    self.text = self.text.replace(item, "=")

            # Remove other markup
            pgdp_markup = ["<.*?>"]
            if self.args.suppress_proofers_notes:
                pgdp_markup += r"\[\*\*[^]]*?\]"

            for item in pgdp_markup:
                self.text = re.sub(item, '', self.text)

            if self.args.regroup_split_words:
                word_splits = {r"(\w+)-\*(\n+)\*": r'\2\1',
                               r"(\w+)-\*_(\n\n)_\*": r"\2\1",
                               r"(\w+)-\*(\w+)": r"\1\2"}
                for item in word_splits:
                    self.text = re.sub(item, word_splits[item], self.text)

        else:  # Processed text file
            if self.args.ignore_format:
                self.text = self.text.replace("_", "")
                self.text = self.text.replace("=", "")

            # Remove thought breaks
            self.text = self.text.replace("*       *       *       *       *", "")
            self.text = self.text.replace("*     *     *     *     *", "")

        # Remove [Footnote, [Illustrations and [Sidenote tags
        if self.args.ignore_format or self.args.suppress_footnote_tags:
            self.text = re.sub(r"\[Footnote (\d+): ", r'\1 ', self.text)
            self.text = re.sub(r"\*\[Footnote: ", '', self.text)

        if self.args.ignore_format or self.args.suppress_illustration_tags:
            self.text = re.sub(r"\[Illustrations?:([^]]*?)]", r'\1', self.text, flags=re.MULTILINE)
            self.text = re.sub(r"\[Illustration]", '', self.text)

        if self.args.ignore_format or self.args.suppress_sidenote_tags:
            self.text = re.sub(r"\[Sidenote:([^]]*?)]", r'\1', self.text, flags=re.MULTILINE)

    def extract_footnotes(self):
        if self.from_pgdp_rounds:  # always [Footnote 1: text]
            self.extract_footnotes_pgdp()
        else:  # probably [1] text
            self.extract_footnotes_pp()

    def extract_footnotes_pp(self):
        """Extract the footnotes from a PP text version
        Convert to lines and back
        """
        # Call root function. Move it here
        text, footnotes = extract_footnotes_pp(self.text)

        # Rebuild text, now without footnotes
        self.text = '\n'.join(text)
        self.footnotes = '\n'.join(footnotes)

    def extract_footnotes_pgdp(self):
        """ Extract the footnotes from an F round
        Start with [Footnote ... and finish with ] at the end of a line
        """
        # Note: this is really dirty code. Should rewrite. Don't use current_fnote[0].
        in_footnote = False  # currently processing a footnote
        current_fnote = []  # keeping current footnote
        text = []  # new text without footnotes
        footnotes = []

        for line in self.text:
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

                # End of footnote?
                # We don't try to regroup yet
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

    def transform(self):
        """Final cleanup."""
        for func in self.transform_func:
            self.text = func(self.text)
        for func in self.transform_func:
            self.footnotes = func(self.footnotes)


# move to PgdpFileText
def extract_footnotes_pp(pp_text):
    """Extract footnotes from a PP text file. text is iterable. Returns
    the text as an iterable, without the footnotes, and footnotes as a
    list of (footnote string id, line number of the start of the
    footnote, list of strings comprising the footnote).
    fn_regexes is a list of (regex, fn_type) that identify the beginning
    and end of a footnote. The fn_type is 1 when a ] terminates it, or
    2 when a new block terminates it.
    """
    # RT: Why is this different from extract_footnotes_pgdp, except
    # tidied would be "[1] text" instead of [Footnote 1: text]? 1st regex?

    # If the caller didn't give a list of regex to identify the
    # footnotes, build one, taking only the most common.
    all_regexes = [(r"(\s*)\[([\w-]+)\](.*)", 1),
                   (r"(\s*)\[Note (\d+):( .*|$)", 2),
                   (r"(      )Note (\d+):( .*|$)", 1)]
    regex_count = [0] * len(all_regexes)  # i.e. [0, 0, 0]

    for block, empty_lines in get_block(pp_text):
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

    for block, empty_lines in get_block(pp_text):
        # Is the block a new footnote?
        next_fn_type = 0
        if len(block):
            for (regex, fn_type) in fn_regexes:
                matches = re.match(regex, block[0])
                if matches:
                    if matches.group(2).startswith(("Illustration",
                                                    "Décoration",
                                                    "Décoration", "Bandeau",
                                                    "Logo", "Ornement")):
                        # An illustration, possibly inside a footnote. Treat
                        # as part of text or footnote.
                        continue

                    next_fn_type = fn_type
                    # next_fn_indent = matches.group(1) # unused

                    # Update first line of block, because we want the
                    # number outside.
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
                # Same indent or more. This is a continuation. Merge with
                # one empty line.
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

    return text, footnotes


class PgdpFileHtml(PgdpFile):
    """Store and process a DP html file."""
    def __init__(self, args):
        super().__init__(args)
        self.tree = None
        self.mycss = ""

    def load(self, filename):
        """Load the file
        If parsing succeeded, then self.tree is set, and parser.errors is [].
        """

        # noinspection PyProtectedMember,Pylint
        def remove_namespace(self):
            """Remove namespace URI in elements names
            "{http://www.w3.org/1999/xhtml}html" -> "html"
            """
            for elem in self.tree.iter():
                if not (isinstance(elem, etree._Comment)
                        or isinstance(elem, etree._ProcessingInstruction)):
                    elem.tag = etree.QName(elem).localname
            # Remove unused namespace declarations
            etree.cleanup_namespaces(self.tree)

        text = self.load_file(filename)

        parser = html5parser.HTMLParser()
        try:
            tree = html5parser.document_fromstring(text)
        except Exception as e:
            raise SyntaxError("File cannot be parsed: " + filename + repr(e))

        if len(parser.errors):
            if type(parser) == etree.HTMLParser:
                # HTML parser rejects tags with both id and filename (513 == DTD_ID_REDEFINED)
                parser.errors = [x for x in parser.errors
                                      if parser.errors[0].type != 513]
        if len(parser.errors):
            raise SyntaxError("Parsing errors in document: " + filename)

        self.tree = tree.getroottree()
        self.file_text = text.splitlines()

        # Remove the namespace from the tags
        remove_namespace(self)

        # Remove PG boilerplate. These are kept in a <pre> tag.
        # BUG: this doesn't save anything
        # RT: this has changed:
        # old: <pre save_image_to_download="true">
        #     <pre> at end
        # new: <body save_image_to_download="true">
        #   to <div>*** START OF THE PROJECT GUTENBERG EBOOK
        #   <div>*** END OF THE PROJECT GUTENBERG EBOOK

        # find = etree.XPath("//pre")
        # for element in find(self.tree):
        #     if element.text is None:
        #         continue
        #     text = element.text.strip()
        #     if re.match(PG_EBOOK_START_REGEX, text, flags=re.MULTILINE | re.DOTALL):
        #         self.clear_element(element)
        #     elif text.startswith(PG_EBOOK_END1):
        #         self.clear_element(element)

    def process_args(self):
        # Load default CSS for transformations
        if self.args.css_no_default is False:
            self.mycss = DEFAULT_TRANSFORM_CSS

        # Process command line arguments
        if self.args.css_smcap == 'U':
            self.mycss += ".smcap { text-transform:uppercase; }"
        elif self.args.css_smcap == 'L':
            self.mycss += ".smcap { text-transform:lowercase; }"
        elif self.args.css_smcap == 'T':
            self.mycss += ".smcap { text-transform:capitalize; }"

        if self.args.css_bold:
            self.mycss += "b:before, b:after { content: " + self.args.css_bold + "; }"

        if self.args.css_greek_title_plus:
            # greek: if there is a title, use it to replace the greek. */
            self.mycss += '*[lang=grc] { content: "+" attr(title) "+"; }'

        if self.args.css_add_illustration:
            for figclass in ['figcenter', 'figleft', 'figright']:
                self.mycss += '.' + figclass + ':before { content: "[Illustration: "; }'
                self.mycss += '.' + figclass + ':after { content: "]"; }'

        if self.args.css_add_sidenote:
            self.mycss += '.sidenote:before { content: "[Sidenote: "; }'
            self.mycss += '.sidenote:after { content: "]"; }'

        # --css can be present multiple times, so it's a list.
        for css in self.args.css:
            self.mycss += css

    def analyze(self):
        """Clean then analyse the content of a file."""
        # Empty the head - we only want the body
        self.tree.find('head').clear()

        # Remember which line <body> was.
        lineno = 0
        for line in self.file_text:
            if '<body' in line:
                break
            lineno = lineno + 1

        #        self.start_line = self.tree.find('body').sourceline - 2

        # Remove PG footer, 1st method
        clear_after = False
        for element in self.tree.find('body').iter():
            if clear_after:
                element.text = ""
                element.tail = ""
            elif element.tag == "p" and element.text and element.text.startswith(PG_EBOOK_END1):
                element.text = ""
                element.tail = ""
                clear_after = True

        # Remove PG header and footer, 2nd method
        find = etree.XPath("//pre")
        for element in find(self.tree):
            if element.text is None:
                continue

            text = element.text.strip()

            # Header - Remove everything until start of book.
            m = re.match(PG_EBOOK_START_REGEX, text, flags=re.MULTILINE | re.DOTALL)
            if m:
                # Found the header. Keep only the text after the start tag (usually the credits)
                element.text = m.group(1)
                continue

            if text.startswith(PG_EBOOK_END1) or text.startswith("End of Project Gutenberg"):
                self.clear_element(element)

        # Remove PG footer, 3rd method -- header and footer are normal html, not text in <pre> tag.
        try:
            # Look for one element
            (element,) = etree.XPath("//p[@id='pg-end-line']")(self.tree)
            while element is not None:
                self.clear_element(element)
                element = element.getnext()
        except ValueError:
            pass

        # Cleaning is done.

        # Transform html into text for character search.
        self.char_text = etree.XPath("normalize-space(/)")(self.tree)

        # HTML doc should have oelig by default.
        self.has_oe_ligature = True

    def convert(self):
        """Remove HTML and PGDP marker from the text."""
        escaped_unicode_re = re.compile(r"\\u[0-9a-fA-F]{4}")

        def text_apply(element, func):
            """Apply a function to every sub-element's .text and .tail, and element's .text"""
            if element.text:
                element.text = func(element.text)
            for sub in element.iter():
                if sub == element:
                    continue
                if sub.text:
                    sub.text = func(sub.text)
                if sub.tail:
                    sub.tail = func(sub.tail)

        def escaped_unicode(m):
            try:
                return bytes(m.group(0), 'utf8').decode('unicode-escape')
            except:
                return m.group(0)

        def new_content(element):
            """Process the "content:" property"""
            result = ""
            for token in val.value:
                if token.type == "STRING":
                    # e.g. { content: "xyz" }
                    result += escaped_unicode_re.sub(escaped_unicode, token.value)
                elif token.type == "FUNCTION":
                    if token.function_name == 'attr':
                        # e.g. { content: attr(title) }
                        result += element.attrib.get(token.content[0].value, "")
                elif token.type == "IDENT":
                    if token.value == "content":
                        # Identity, e.g. { content: content }
                        result += element.text
            return result

        # Process each rule from our transformation CSS
        stylesheet = tinycss.make_parser().parse_stylesheet(self.mycss)
        property_errors = []
        for rule in stylesheet.rules:
            # Extract values we care about
            f_transform = None
            f_replace_with_attr = None
            f_text_replace = None
            f_element_func = None
            f_move = None

            for val in rule.declarations:
                if val.name == 'content':
                    # result depends on element and pseudo elements.
                    pass
                elif val.name == "text-transform":
                    if len(val.value) != 1:
                        property_errors += [(val.line, val.column, val.name + " takes 1 argument")]
                    else:
                        v = val.value[0].value
                        if v == "uppercase":
                            def f_transform(x): return x.upper()
                        elif v == "lowercase":
                            def f_transform(x): return x.lower()
                        elif v == "capitalize":
                            def f_transform(x): return x.title()
                        else:
                            property_errors += [(val.line, val.column,
                                                 val.name + " accepts only 'uppercase',"
                                                            " 'lowercase' or 'capitalize'")]
                elif val.name == "_replace_with_attr":
                    def f_replace_with_attr(el): return el.attrib[val.value[0].value]
                elif val.name == "text-replace":
                    # Skip S (spaces) tokens.
                    values = [v for v in val.value if v.type != "S"]
                    if len(values) != 2:
                        property_errors += [(val.line, val.column, val.name
                                             + " takes 2 string arguments")]
                    else:
                        v1 = values[0].value
                        v2 = values[1].value
                        def f_text_replace(x): return x.replace(v1, v2)
                elif val.name == "display":
                    # Support display none only. So ignore "none" argument.
                    f_element_func = self.clear_element
                elif val.name == "_graft":
                    values = [v for v in val.value if v.type != "S"]
                    if len(values) < 1:
                        property_errors += [(val.line, val.column, val.name
                                             + " takes at least one argument")]
                        continue
                    f_move = []
                    for v in values:
                        print("[", v.value, "]")
                        if v.value == 'parent':
                            f_move.append(lambda el: el.getparent())
                        elif v.value == 'prev-sib':
                            f_move.append(lambda el: el.getprevious())
                        elif v.value == 'next-sib':
                            f_move.append(lambda el: el.getnext())
                        else:
                            property_errors += [(val.line, val.column, val.name
                                                 + " invalid value " + v.value)]
                            f_move = None
                            break

                    if not f_move:
                        continue
                else:
                    property_errors += [(val.line, val.column, "Unsupported property " + val.name)]
                    continue

                # Iterate through each selector in the rule
                for selector in cssselect.parse(rule.selector.as_css()):
                    pseudo_element = selector.pseudo_element
                    xpath = cssselect.HTMLTranslator().selector_to_xpath(selector)
                    find = etree.XPath(xpath)

                    # Find each matching element in the HTML document
                    for element in find(self.tree):
                        # Replace text with content of an attribute.
                        if f_replace_with_attr:
                            element.text = f_replace_with_attr(element)

                        if val.name == 'content':
                            v_content = new_content(element)
                            if pseudo_element == "before":
                                element.text = v_content + (element.text or '')  # opening tag
                            elif pseudo_element == "after":
                                element.tail = v_content + (element.tail or '')  # closing tag
                            else:
                                # Replace all content
                                element.text = new_content(element)

                        if f_transform:
                            text_apply(element, f_transform)

                        if f_text_replace:
                            text_apply(element, f_text_replace)

                        if f_element_func:
                            f_element_func(element)

                        if f_move:
                            parent = element.getparent()
                            new = element
                            for f in f_move:
                                new = f(new)

                            # Move the tail to the sibling or the parent
                            if element.tail:
                                sibling = element.getprevious()
                                if sibling:
                                    sibling.tail = (sibling.tail or "") + element.tail
                                else:
                                    parent.text = (parent.text or "") + element.tail
                                element.tail = None

                            # Prune and graft
                            parent.remove(element)
                            new.append(element)

        css_errors = ""
        if stylesheet.errors or property_errors:
            # There are transformation CSS errors. If the default css
            # is included, take the offset into account.
            i = 0
            if self.args.css_no_default is False:
                i = DEFAULT_TRANSFORM_CSS.count('\n')
            css_errors = "<div class='error-border bbox'><p>Error(s) in the" \
                         "  transformation CSS:</p><ul>"
            for err in stylesheet.errors:
                css_errors += "<li>{0},{1}: {2}</li>".format(err.line - i, err.column, err.reason)
            for err in property_errors:
                css_errors += "<li>{0},{1}: {2}</li>".format(err[0] - i, err[1], err[2])
            css_errors += "</ul>"

        return css_errors

    def extract_footnotes(self):
        """Find footnotes, then remove them"""

        def strip_note_tag(string, keep_num=False):
            """Remove note tag and only keep the number.  For instance
            "Note 123: lorem ipsum" becomes "123 lorem ipsum" or just
            "lorem ipsum".
            """
            for regex in [r"\s*\[([\w-]+)\](.*)",
                          r"\s*([\d]+)\s+(.*)",
                          r"\s*([\d]+):(.*)",
                          r"\s*Note ([\d]+):\s+(.*)"]:
                m = re.match(regex, string, re.DOTALL)
                if m:
                    break

            if m:
                if keep_num:
                    return m.group(1) + " " + m.group(2)
                else:
                    return m.group(2)
            else:
                # That may be bad
                return string

        if self.args.extract_footnotes:
            footnotes = []

            # Special case for PPers who do not keep the marking around
            # the whole footnote. They only mark the first paragraph.
            elements = etree.XPath("//div[@class='footnote']")(self.tree)
            if len(elements) == 1:
                element = elements[0]

                # Clean footnote number
                for el in element:
                    footnotes += [strip_note_tag(el.xpath("string()"))]

                # Remove the footnote from the main document
                element.getparent().remove(element)
            else:
                for find in ["//div[@id[starts-with(.,'FN_')]]",
                             "//p[a[@id[starts-with(.,'Footnote_')]]]",
                             "//div/p[span/a[@id[starts-with(.,'Footnote_')]]]",
                             "//div/p[span/a[@id[starts-with(.,'Footnote_')]]]",
                             "//p[@class='footnote']",
                             "//div[@class='footnote']"]:
                    for element in etree.XPath(find)(self.tree):
                        # Grab the text and remove the footnote number
                        footnotes += [strip_note_tag(element.xpath("string()"))]
                        # Remove the footnote from the main document
                        element.getparent().remove(element)

                    if len(self.footnotes):
                        # Found them. Stop now.
                        break

            self.footnotes = "\n".join(footnotes)

    def transform(self):
        """Transform html into text. Do a final cleanup."""
        self.text = etree.XPath("string(/)")(self.tree)

        # Apply transform function to the main text
        for func in self.transform_func:
            self.text = func(self.text)

        # Apply transform function to the footnotes
        for func in self.transform_func:
            self.footnotes = func(self.footnotes)

        # zero width space
        if self.args.ignore_0_space:
            self.text = self.text.replace(chr(0x200b), "")

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


# only called by extract_footnotes_pp, move to PgdpFileText
def get_block(pp_text):
    """Generator to get a block of text, followed by the number of empty lines."""
    empty_lines = 0
    block = []

    for line in pp_text:
        if len(line):
            # One or more empty lines will stop a block
            if empty_lines:
                yield block, empty_lines
                block = []
                empty_lines = 0
            block += [line]
        else:
            empty_lines += 1

    yield block, empty_lines


DEFAULT_TRANSFORM_CSS = '''
        /* Italics */
        i:before, cite:before, em:before, abbr:before, dfn:before,
        i:after, cite:after, em:after, abbr:after, dfn:after      { content: "_"; }

        /* Bold */
        b:before, bold:before,
        b:after, bold:after         { content: "="; }

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


class PPComp(object):
    """Compare two files."""

    def __init__(self, args):
        self.args = args

    def compare_texts(self, text1, text2):
        """Compare two sources
        We could have used the difflib module, but it's too slow:
           for line in difflib.unified_diff(f1.words, f2.words):
               print(line)
        Use dwdiff instead.
        """
        with tempfile.NamedTemporaryFile(mode='wb') as temp1, \
                tempfile.NamedTemporaryFile(mode='wb') as temp2:
            temp1.write(text1.encode('utf-8'))
            temp2.write(text2.encode('utf-8'))
            temp1.flush()
            temp2.flush()
            repo_dir = os.environ.get("OPENSHIFT_DATA_DIR", "")
            if repo_dir:
                dwdiff_path = os.path.join(repo_dir, "bin", "dwdiff")
            else:
                dwdiff_path = "dwdiff"

            """
            -P Use punctuation characters as delimiters.
            -R Repeat the begin and end markers at the start and end of line if a change crosses a
               newline.
            -C 2 Show <num> lines of context before and after each changes.
            -L Show line numbers at the start of each line.
            """
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
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)
            # The output is raw, so we have to decode it to UTF-8, which is the default under Ubuntu
            return p.stdout.read().decode('utf-8')

    def create_html(self, files, text, footnotes):
        """Create the output html file"""

        def massage_input(text, start0, start1):
            # Massage the input
            newtext = text.replace("&", "&amp;")
            newtext = newtext.replace("<", "&lt;")
            newtext = newtext.replace(">", "&gt;")
            newtext = newtext.replace("]COMPPP_START_DEL[", "<del>")
            newtext = newtext.replace("]COMPPP_STOP_DEL[", "</del>")
            newtext = newtext.replace("]COMPPP_START_INS[", "<ins>")
            newtext = newtext.replace("]COMPPP_STOP_INS[", "</ins>")
            if newtext:
                newtext = "<hr /><pre>\n" + newtext
            newtext = newtext.replace("\n--\n", "\n</pre><hr /><pre>\n")
            newtext = re.sub(r"^\s*(\d+):(\d+)",
                          lambda m: "<span class='lineno'>{0} : {1}</span>".format(
                              int(m.group(1)) + start0,
                              int(m.group(2)) + start1),
                          newtext, flags=re.MULTILINE)
            if newtext:
                newtext += "</pre>\n"
            return newtext

        # Find the number of diff sections
        nb_diffs_text = 0
        if text:
            nb_diffs_text = len(re.findall("\n--\n", text)) + 1

        nb_diffs_footnotes = 0
        if footnotes:
            nb_diffs_footnotes = len(re.findall("\n--\n", footnotes or "")) + 1

        # Text, with correct (?) line numbers
        text = massage_input(text, files[0].start_line, files[1].start_line)

        # Footnotes - line numbers are meaningless right now. We could fix that.
        footnotes = massage_input(footnotes, 0, 0)

        html_content = "<div>"

        if nb_diffs_text == 0:
            html_content += "<p>There is no diff section in the main text.</p>"
        elif nb_diffs_text == 1:
            html_content += "<p>There is " + str(nb_diffs_text) \
                            + " diff section in the main text.</p>"
        else:
            html_content += "<p>There are " + str(nb_diffs_text) \
                            + " diff sections in the main text.</p>"

        if footnotes:
            html_content += "<p>Footnotes are diff'ed separately <a href='#footnotes'>here</a></p>"
            if nb_diffs_footnotes == 0:
                html_content += "<p>There is no diff section in the footnotes.</p>"
            elif nb_diffs_footnotes == 1:
                html_content += "<p>There is " + str(nb_diffs_footnotes) \
                                + " diff section in the footnotes.</p>"
            else:
                html_content += "<p>There are " + str(nb_diffs_footnotes) \
                                + " diff sections in the footnotes.</p>"
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

    @staticmethod
    def check_char(files, char_best, char_other):
        """Check whether each file has the 'best' character. If not, add a conversion request.
        This is used for instance if one version uses curly quotes while the other uses straight.
        In that case, we need to convert one into the other, to get a smaller diff.
        """
        finds_0 = files[0].char_text.find(char_best)
        finds_1 = files[1].char_text.find(char_best)
        if finds_0 >= 0 and finds_1 >= 0:  # Both have it
            return
        if finds_0 == -1 and finds_1 == -1:  # Neither has it
            return
        # Downgrade one version
        if finds_0 > 0:
            files[0].transform_func.append(lambda text: text.replace(char_best, char_other))
        else:
            files[1].transform_func.append(lambda text: text.replace(char_best, char_other))

    # RT: This should be obsolete, but maybe doesn't hurt for old files
    @staticmethod
    def check_oelig(files):
        """Similar to check_char, but for oe ligatures."""
        if files[0].has_oe_ligature and files[1].has_oe_ligature:
            pass
        elif files[0].has_oe_dp and files[1].has_oe_dp:
            pass
        elif files[0].has_oe_ligature and files[1].has_oe_dp:
            files[1].transform_func.append(lambda text: text.replace("[oe]", "œ"))
            files[1].transform_func.append(lambda text: text.replace("[OE]", "Œ"))
        elif files[1].has_oe_ligature and files[0].has_oe_dp:
            files[0].transform_func.append(lambda text: text.replace("[oe]", "œ"))
            files[0].transform_func.append(lambda text: text.replace("[OE]", "Œ"))
        else:
            if files[0].has_oe_ligature:
                files[0].transform_func.append(lambda text: text.replace("œ", "oe"))
                files[0].transform_func.append(lambda text: text.replace("Œ", "OE"))
            elif files[1].has_oe_ligature:
                files[1].transform_func.append(lambda text: text.replace("œ", "oe"))
                files[1].transform_func.append(lambda text: text.replace("Œ", "OE"))

            if files[0].has_oe_dp:
                files[0].transform_func.append(lambda text: text.replace("[oe]", "oe"))
                files[0].transform_func.append(lambda text: text.replace("[OE]", "OE"))
            elif files[1].has_oe_dp:
                files[1].transform_func.append(lambda text: text.replace("[oe]", "oe"))
                files[1].transform_func.append(lambda text: text.replace("[OE]", "OE"))

    @property
    def do_process(self):
        """Main routine: load & process the files"""
        files = [None, None]

        # Load files
        for i, fname in enumerate(self.args.filename):
            # Look for file type.
            if fname.lower().endswith(('.html', '.htm')):
                files[i] = PgdpFileHtml(self.args)
            else:
                files[i] = PgdpFileText(self.args)

            f = files[i]
            f.load(fname)
            f.process_args()
            f.analyze()

        # How to process oe ligature
        self.check_oelig(files)

        # How to process punctuation IF files don't match
        # Add more as needed
        self.check_char(files, "’", "'")  # close curly quote to straight
        self.check_char(files, "‘", "'")  # open curly quote to straight
        self.check_char(files, '”', '"')  # close curly quotes to straight
        self.check_char(files, '“', '"')  # open curly quotes to straight
        self.check_char(files, "º", "o")  # ordinal o to letter o
        self.check_char(files, "ª", "a")  # ordinal a to letter a
        self.check_char(files, "–", "-")  # ndash to regular dash
        self.check_char(files, "—", "--")  # mdash to regular dashes
        self.check_char(files, "½", "-1/2")
        self.check_char(files, "¼", "-1/4")
        self.check_char(files, "¾", "-3/4")
        self.check_char(files, '⁄', '/')  # fraction slash
        self.check_char(files, "′", "'")  # prime
        self.check_char(files, "″", "''")  # double prime
        self.check_char(files, "‴", "'''")  # triple prime
        self.check_char(files, "₀", "0")  # subscript 0
        self.check_char(files, "₁", "1")  # subscript 1
        self.check_char(files, "₂", "2")  # subscript 2
        self.check_char(files, "₃", "3")  # subscript 3
        self.check_char(files, "₄", "4")  # subscript 4
        self.check_char(files, "₅", "5")  # subscript 5
        self.check_char(files, "₆", "6")  # subscript 6
        self.check_char(files, "₇", "7")  # subscript 7
        self.check_char(files, "₈", "8")  # subscript 8
        self.check_char(files, "₉", "9")  # subscript 9
        self.check_char(files, "⁰", "0")  # superscript 0
        self.check_char(files, "¹", "1")  # superscript 1
        self.check_char(files, "²", "2")  # superscript 2
        self.check_char(files, "³", "3")  # superscript 3
        self.check_char(files, "⁴", "4")  # superscript 4
        self.check_char(files, "⁵", "5")  # superscript 5
        self.check_char(files, "⁶", "6")  # superscript 6
        self.check_char(files, "⁷", "7")  # superscript 7
        self.check_char(files, "⁸", "8")  # superscript 8
        self.check_char(files, "⁹", "9")  # superscript 9

        # RT: move to convert
        # Remove non-breakable spaces between numbers. For instance, a
        # text file could have 250000, and the html could have 250 000.
        if self.args.suppress_nbsp_num:
            def func(text): return re.sub(r"(\d)\u00A0(\d)", r"\1\2", text)
            files[0].transform_func.append(func)
            files[1].transform_func.append(func)

        # RT: move to convert
        # Suppress shy (soft hyphen)
        def func(text): return re.sub(r"\u00AD", r"", text)
        files[0].transform_func.append(func)
        files[1].transform_func.append(func)

        err_message = ""

        # Apply the various conversions
        for f in files:
            err_message += f.convert() or ""

        # Extract footnotes
        if self.args.extract_footnotes:
            for f in files:
                f.extract_footnotes()

        # Transform the final document into a diffable format
        for f in files:
            f.transform()

        # Compare the two versions
        main_diff = self.compare_texts(files[0].text, files[1].text)

        if self.args.extract_footnotes:
            fnotes_diff = self.compare_texts(files[0].footnotes, files[1].footnotes)
        else:
            fnotes_diff = ""

        html_content = self.create_html(files, main_diff, fnotes_diff)

        return html_content, files[0].basename, files[1].basename

    def simple_html(self):
        """For debugging purposes. Transform the html and print the text output."""
        fname = self.args.filename[0]
        if fname.lower().endswith(('.html', '.htm')):
            f = PgdpFileHtml(self.args)
        else:
            print("Error: not an html file")
            return

        f.load(fname)
        f.analyze()

        # Remove non-breakable spaces between numbers. For instance, a
        # text file could have 250000, and the html could have 250 000.
        if self.args.suppress_nbsp_num:
            def func(text): return re.sub(r"(\d)\u00A0(\d)", r"\1\2", text)
            f.transform_func.append(func)

        # Suppress shy (soft hyphen)
        def func(text): return re.sub(r"\u00AD", r"", text)
        f.transform_func.append(func)

        # Apply the various conversions
        f.convert()

        # Extract footnotes
        if self.args.extract_footnotes:
            f.extract_footnotes()

        # Transform the final document into a diffable format
        f.transform()

        print(f.text)


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

    x = PPComp(args)
    if args.simple_html:
        x.simple_html()
    else:
        html_content, fn1, fn2 = x.do_process
        output_html(html_content, fn1, fn2)


if __name__ == '__main__':
    main()
