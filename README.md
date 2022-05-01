# ppcomp

Compare 2 files for [Distributed Proofreaders](https://www.pgdp.net) users.

## Introduction
Used to compare 2 files and generate a summary of the differences. Its goal is to look for discrepancies between the text and HTML versions produced at PGDP, ignoring many formatting and spacing differences.

The sources can be:
  - A post-processed text file.
  - A post-processed HTML file.
  - An unprocessed text file from the Px or Fx rounds.
  - A text or HTML file from an external source.

The text files are identified by the `.txt` extension, HTML files by the `.htm`, `.html`, or `.xhtml` extension, and a Px or Fx file by its `"projectID"` prefix.

It applies various transformations according to program options before passing the files to the Linux program `dwdiff`. There does not seem to be any Windows equivalent of `dwdiff`, it can only be run in a Windows Subsystem for Linux console.

## Usage
| Option                       | File type | Description                                                  |
| ---------------------------- | --------- | ------------------------------------------------------------ |
| -h                           |           | Show usage                                                   |
| --ignore-case                | All       | Ignore case when comparing                                   |
| --extract-footnotes          | All       | Extract and process footnotes separately                     |
| --suppress-footnote-tags     | Text      | Suppress **\[Footnote ?: ...]** marks                        |
| --suppress-illustration-tags | Text      | Suppress **\[Illustration: ...]** marks                      |
| --suppress-sidenote-tags     | Text      | Suppress **\[Sidenote: ]** marks                             |
| --ignore-format              | Rounds    | Silence formatting differences (**\<i>**, **\<b>**)          |
| --suppress-proofers-notes    | Rounds    | Suppress **\[\*\*proofreaders notes]**                       |
| --regroup-split-words        | Rounds    | Regroup split **wo-* *rds**                                  |
| --txt-cleanup-type *TYPE*    | Rounds    | Type of text cleaning -- (**b**)est effort \[default], (**n**)one, (**p**)roofers |
| --css-add-illustration       | HTML      | Add **\[Illustration: ...]** tags                            |
| --css-add-sidenote           | HTML      | Add **\[Sidenote: ...]** tags                                |
| --css-smcap *TYPE*           | HTML      | Transform small caps into uppercase (**U**), lowercase (**L**) or title case (**T**) |
| --css-bold *STR*             | HTML      | Surround bold strings with this string [default '**=**']     |
| --css *CSS*                  | HTML      | Insert custom transformation CSS (can be multiple)           |
| --css-no-default             | HTML      | Do not use default transformation CSS                        |
| --suppress-nbsp-num          | HTML      | Suppress non-breakable spaces (U+00A0) between numbers       |
| --ignore-0-space             | HTML      | Suppress zero width space (U+200B)                           |
| --css-greek-title-plus       | HTML      | Use Greek transliteration from the title attribute           |
| --simple-html                | HTML      | Process an html file and print the output (debug)            |

## Requirements

ppcomp needs python 3 (not 2) to run, as well as the following python packages:
  - lxml
  - tinycss
  - cssselect
  - html5lib (used by lxml)

And the following command-line tool:
  - dwdiff


## Installation
To install on Linux (Debian or Ubuntu):
```bash
sudo apt-get install dwdiff
```

Use pip to install the packages. First, install pip for python3 if it's not already installed:

```bash
sudo apt-get install python3-pip
```

then install the needed packages:

```bash
pip install tinycss
pip install cssselect
pip install lxml
pip install html5lib
```

## Usage
Comparing two files is easy:
```bash
./ppcomp/ppcomp.py file1.txt file2.html > result.html
```
or
```bash
python ppcomp/ppcomp.py file1.txt file2.html > result.html
```

Internally, ppcomp will transform both files to reduce insignificant differences. For instance, in the HTML version `<i>` and `</i>` will be transformed to "\_" so that will not generate a diff. Internally, a CSS transformation engine will take care of the HTML.

Once both files are transformed, the diff happens (using `dwdiff`), then its output is transformed into HTML. This HTML result is then sent to the standard output where it can be redirected and finally loaded into a browser. There is a small notification at the top explaining the diffs.

## Footnotes
If the two versions have footnotes, but they are not placed in the same spot (i.e., after each paragraph for the text, and at the end of the book for the HTML), they can be extracted and compared separately:

```
--extract-footnotes
```

Note that formatting of footnotes by processors varies widely, only a few variations are supported.

## Tuning

By default, a few reasonable rules are applied to the HTML (See the definition of DEFAULT_TRANSFORM_CSS in the source code). However, it may be necessary to go further to reduce the amount of noise.

Currently, a few CSS targets are supported:
```
::before  -- add content before the tag
::after   -- add content after the tag
```

Some transformations are also supported:
```
text-transform -- transform the content to uppercase, lowercase, or title case
_replace_with_attr -- replace the whole content with the value of an attribute
text-replace -- replace a string inside content with another
```

## --css Example
### Footnote Anchors
By default footnote anchors are expected to be surrounded by brackets. If it is not the case in the HTML, this can be easily fixed with the following:

```
--css '.fnanchor:before { content: "["; } .fnanchor:after { content: "]"; }'
```

## Footnote extraction styles supported

**html: class="footnote"**

```
<div class="footnote">
  <a id="Footnote_926" href="#FNanchor_926" class="label">[926]</a>
    Kidston (94), p. 250.
</div>
```

### Text output from formatting rounds (`"projectID"` prefix)

**[Footnote #: followed by 1 or more paragraphs, with end bracket, and possible `*[Footnote:` continuation blocks.**

```
[Footnote A: The pamphlet has been copied <i>in extenso</i>, and will be found in the Appendix.]
    
Normal paragraph.
    
*[Footnote: foootnote continued.]
```

### Text PP style 1

**[#] following empty line (to avoid normal bracketed text), 1 or more paragraphs ending with the next footnote or 2 empty lines.**

```
Paragraph text.
    
[926] Kidston (94), p. 250.

[927] Another footnote.

Another footnote paragraph.


Normal paragraph.
```

### Text PP style 2

**Footnote #: followed by 1 or more indented paragraphs, ending with the next footnote or unindented text.**

```
Paragraph text.

Footnote 1:

  The dates given here are those of the Russian calendar.

  Another footnote paragraph.

Normal paragraph.
```

### Text PP style 3

**Superscripted # followed by 1 or more indented paragraphs, ending with the next footnote or unindented text.**

```
¹ Cordier, "Mémoire sur les substances dites en masse,
    qui entrent dans la composition des Roches Volcaniques," Journ.
    de Physique, =83= (1816), 135, 285, and 352.

    See Appendix E.

Normal paragraph
```
