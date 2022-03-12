.. highlight:: css

==============================
ppcomp — comparing files easy
==============================


Introduction
------------

Comparing files is useful to ensure the various versions of a document
(text and HTML) are consistent, and have not deviated during
the PP phase.

This diff tool (ppcomp) is based on dwdiff. At the base, it compares
2 different text files while ignoring all the spacing differences.

To be able to compare an HTML file to another file (either text
or HTML), it file has to be transformed into a regular text
file without all the HTML tags.

Internally, ppcomp will transform both files to make them closer to
each other. This transformation is driven by a CSS like language,
using selectors, classes,... This CSS only affects the HTML file(s)
given as input.

ppcomp includes a default set of CSS to perform sane transformations
that follow DP usual PPing practices. For instance, **<i>...</i>** in the HTML
version will be transformed to **_..._** so that it will not generate a
diff with another file. That should be enough for a normal project,
without having to define some specialized CSS rules.


Handling of files
-----------------

Depending on certain criteria, the internal handling of files will be
different.

Files with names ending in *.HTML* or *.htm* are recognized as HTML
files. Files starting with *ProjectID* and ending with *.txt* will be
considered as files coming from the rounds (P1/2/3 or F1/2), and
other files ending with *.txt* are PPed text files. Files not
matching these criteria will be rejected.

The encoding is expected to be UTF-8.


Options
-------

Extract and process footnotes separately
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the two versions have footnotes, but they are not placed in the
same spot (i.e. after each paragraph for the text, and at the end of
the book for the HTML), they can be extracted and compared separately
with this option.

There is a best effort done with the files coming from the
rounds. However they are usually broken, thus finding all the
footnotes will fail, and the diff for the footnotes will not be done
at all.


Transform small caps
~~~~~~~~~~~~~~~~~~~~~~~~~~

Usually small caps in the text version are transformed to uppercase.
This transformation has to be done in the HTML too, so these sections
will not generate a diff.

The default is to do nothing. The options are *"Uppercase"*, *"Lowercase"*
and *"Title"*. *"Title"* means capitalizing the first letter of each word
*"Like This"*.


HTML: add [Sidenote: ...] tag
~~~~~~~~~~~~~~~~~~~~~~~~~

To use when the text version has "[Sidenote: ...]", and not the HTML.
This will add a "[Sidenote: ...]" in the HTML version, thus 
suppressing the diff.


HTML: add [Illustration: ...] tag
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similar to add [Sidenote: ...] tag.


Ignore case when comparing
~~~~~~~~~~~~~~~~~~~~~~~~~~

If there are too many unfixable case differences, use this option to
ignore them.


Suppress non-breakable spaces between numbers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some numbers can be written with an unbreakable space between them
(eg. 2_000). This removes them.


HTML: use greek transliteration in title attribute
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**OBSOLETE**. Current DP policy is to use Unicode Greek.


HTML: suppress zero width space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some HTML contains zero-width spaces. Select this to remove them.


HTML: do not use default transformation CSS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ppcomp include a set of relatively sane defaults, but they can create
issues with some documents. For instance **<i>** might be **+** instead of
the regular **_**. This option tells ppcomp to ignore that predefined
CSS. The downside is that more diffs may appear until a new
transformational CSS is in place.

There is a link on the diff page to see the existing default CSS. This
can be cut and pasted in the transformation CSS box, and adapted.


Transformational CSS
--------------------

This is what drives the transformation of the HTML to a usable text
version resembling the real text version produced by the PP.

For instance, here's how **<i>...</i>** is tranformed into **_..._**.
::

  i:before, i:after   { content: "_"; }

This tells ppcomp to insert an underscore before and after the string
delimited by the <i> tag. On the left side is the regular CSS selector. On
the right side is a more or less standard CSS 3 property/value, although
only a few are implemented.

The removal of page numbers is done with this::

  span[class^="pagenum"] { display: none }

This selects every span with a class starting with the string pagenum,
and suppresses it.


Selectors
~~~~~~~~~

Most CSS 3 selectors should be supported. See
http://www.w3schools.com/cssref/css_selectors.asp


Properties/Values
~~~~~~~~~~~~~~~~~

Only a limited set of properties make sense for ppcomp. Some are from
CSS, some are new.


content
.......

Insert some content in a tag. Used on the element, or in conjonction
with the **:before** and **:after** pseudo selectors. If no
pseudo-element is used, then the existing content is replaced.

Supports multiple parameters, such as a string, the *attr()* function
(insert the content of the attribute), *content* (the identity,
ie. the original content).

The original content is only the first string in the HTML until either
the closing of the matched element or the opening of a sub
element. For instance, if the matched HTML is
*"<span>abc<i>def</i></span>", then the content is only *abc*.

For instance::

  br:before { content: " "; }

  *[lang=grc] { content: "+" attr(title) "+"; }

  .dumb { content: "abc" attr(title) "def" content; }


The *"use greek transliteration in title attribute"* option is
implemented with this::

  *[lang=grc] { content: "+" attr(title) "+"; }


text-transform
..............

Transform the content inside the selected tags. The options are:

  * "uppercase":  *Lorem ipsum dolor*  -->  *LOREM IPSUM DOLOR*
  * "lowercase":  *Lorem ipsum dolor*  -->  *lorem ipsum dolor*
  * "capitalize": *Lorem ipsum dolor*  -->  *Lorem Ipsum Dolor*

For instance::

  .smcap { text-transform:uppercase; }


_replace_with_attr
..................

**OBSOLETE**. Use *content* instead.


display
.......

How to display some content. Right now only "none" is supported, which
simply suppresses the content.

For instance::

  span[class^="pagenum"] { display: none }


text-replace
............

Replaces the first string with the second. All instances will be
replaced.

For instance, to replace a divide symbol with a slash::

  p { text-replace: "⁄" "/"; }

With "1⁄2 + 1⁄2 = 1", this will result in "1/2 + 1/2 = 1".

It is also possible to use unicode numbers (with 2 backslashes)::

  p { text-replace: "Z" "\\u1234"; }
  [id^=Footnote_]:before { content: "\\u200C"; }

_graft
......

Prune and graft an element to another element. The element to graft to
is relative to the element to prune. The path to the new position is
created with 3 parameters:

  * parent: a parent
  * prev-sib: the previous sibling
  * next-sib: the next sibling

The path can be as long as necessary. For instance, the following CSS
will move all span elements with the class "sidenote" to the 2nd
previous sibling of the parent::

  span.sidenote { _graft: parent prev-sib prev-sib; }

For every element, ppcomp will find the parent, then its previous
sibling, then its previous sibling. It will detach the element and
attach it to this new element.

The elements must exist; i.e. all the elements in the path, for all
element matching the selector, must exist.


Expectations in default transformational CSS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Footnotes
.........

In many documents, the semantic of a footnote in HTML is lost because
they are put at the end of the file and look like any other
paragraph. Ideally, a document should include each footnote in a tag,
for instance a div with a footnote class. If this is not present,
ppcomp cannot find the end of the footnote, and sometimes not even
the start.


Page numbers
............

The default CSS includes several selectors to strip the page numbers::

  span[class^="pagenum"] { display: none }
  p[class^="pagenum"] { display: none }
  p[class^="page"] { display: none }
  span[class^="pgnum"] { display: none }
  div[id^="Page\_"] { display: none }
  div[class^="pagenum"] { display: none }


Italics
.......

Italics are surrounded by underscores. Same for em, cite, abbr, ...


Some CSS examples
~~~~~~~~~~~~~~~~~


Anchors
.......

By default anchors are expected to be surrounded by brackets. If it is
not the case in the HTML, this can be easily fixed with the following::

  .fnanchor:before { content: "["; } .fnanchor:after { content: "]"; }


Miscellaneous
.............

Just a few more CSS examples::

  sup:before { content:"^"; } /* 1<sup>st</sup> --> 1^st */
  table[summary="Table of Cases"] td[class="lt"]:after { content: ","; }
  li { text-replace: "--" "—"; }
  h4:before, h4:after { content: "_"; }
  a[id^=FNanchor_]:before { content: "[" } a[id^=FNanchor_]:after{ content: "]" }
  span[lang]:before { content: "_" }
