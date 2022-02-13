class SourceFile():
    """Represent an HTML or text file in memory."""
    def __init__(self):
        pass

    def load_file(self, fname):
        """Load a file (text or html)"""
        pass

    # RT: html only.
    def load_xhtml(self, name):
        """Load an html/xhtml file"""
        pass


class PgdpFile(object):
    """Base class: Store and process a DP text or html file."""

    def __init__(self, args):
        pass

    def load(self, filename):
        """Load the file"""
        pass

    def process_args(self):
        """Process command line arguments"""
        pass

    def analyze(self):
        """Clean then analyse the contents of a file"""
        pass

    def extract_footnotes(self):
        """Extract the footnotes."""
        pass

    def transform(self):
        """Final transformation pass."""
        pass


class PgdpFileText(PgdpFile):
    """Store and process a DP text file."""

    def __init__(self, args):
        pass

    def load(self, filename):
        """Load the file"""
        pass

    # no process_args(self)

    def convert(self):
        """Remove markup from the text."""
        pass

    def analyze(self):
        """Clean then analyse the contents of a file. Decides if it is PP version, a DP
        version, ..."""
        pass

    def extract_footnotes(self):
        pass

    def transform(self):
        """Final cleanup."""
        pass

    # not in base
    def strip_pg_boilerplate(self):
        """Remove the PG header and footer from a text version if present."""
        pass

    # not in base
    def extract_footnotes_pgdp(self):
        """ Extract the footnotes from an F round
        Start with [Footnote ... and finish with ] at the end of a line
        """
        pass

    # not in base
    def extract_footnotes_pp(self):
        """Extract the footnotes from a PP text version"""
        pass


class PgdpFileHtml(PgdpFile):
    """Store and process a DP html file."""
    def __init__(self, args):
        pass

    def load(self, filename):
        """Load the file"""
        pass

    def process_args(self):
        """Load default CSS for transformations"""
        pass

    def convert(self):
        """Remove HTML and PGDP marker from the text."""
        pass

    def analyze(self):
        """Clean then analyse the content of a file."""
        pass

    def extract_footnotes(self):
        """Find footnotes, then remove them"""
        pass

    def transform(self):
        """Transform html into text. Do a final cleanup."""
        pass

    # not in base
    def text_apply(self, element, func):
        """Apply a function to every sub element's .text and .tail, and element's .text."""
        pass

