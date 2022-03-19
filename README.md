# ppcomp

Compare 2 files for [Distributed Proofreaders](https://www.pgdp.net).

## Introduction
Used to compare 2 files and generate a summary of the differences. Its goal is to look for discrepancies between the text and html versions produced at PGDP, ignoring many formatting and spacing differences.

The sources can be:
  - A post-processed text file.
  - A post-processed html file.
  - An unprocessed text file coming from the Px or Fx rounds.
  - A text or html file coming from an external source.

The text files are identified by the .txt extension, html files by the .htm or .html extension, and a Px or Fx file by its "projectID" prefix.

It applies various transformations according to program options before passing the files to the Linux program `dwdiff`. There does not seem to be any Windows equivalent of `dwdiff`.

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
| --suppress-proofers-notes    | Rounds    | Remove **\[\*\*proofreaders notes]**                         |
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
| --css-greek-title-plus       | HTML      | Use Greek transliteration from title attribute               |
| --simple-html                | HTML      | Process an html file and print the output (debug)            |

## Requirements

ppcomp needs python 3 (not 2) to run, as well as the following python packages:
  - lxml
  - tinycss
  - cssselect
  - html5lib (used by lxml)

And the following command line tool:
  - dwdiff


## Installation
To install on Linux (Debian or Ubuntu):
```bash
sudo apt-get install w3c-dtd-xhtml python3-lxml dwdiff
```

`tinycss` and `cssselect` are not present on these distributions yet for python 3.
Use pip to install them. First install pip for python3 if it's not already installed:

```bash
sudo apt-get install python3-pip
```

then install the missing packages:

```bash
pip3 install tinycss
pip3 install cssselect
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

Internally, ppcomp will transform both files to make them closer to each other. For instance, in the html version `<i>` and `</i>` will be transformed to "\_" so that will not generate a diff. Internally, a CSS transformation engine will take care of the html. The transformations to a text version are currently hardcoded.

Once both files are transformed, the diff happens (using `dwdiff`), then its output is transformed into html. This html result is then sent to the standard output where it can be redirected and finally loaded in a browser. There is a small notice at the top explaining the diffs.

## Footnotes
If the two versions have footnotes, but they are not placed in the same spot (i.e. after each paragraph for the text, and at the end of the book for the html), they can be extracted and compared separately:

```
--extract-footnotes
```

## Tuning
By default, there are a few reasonable rules applied to the html (See the definition of self.mycss in the source code). However, it may be necessary to go further in order to reduce the amount of noise.

Currently a few CSS targets are supported:
```
:before  -- add a content before the tag
:after   -- add a content after the tag
```

Some transformations are also supported:
```
text-transform  -- transform the content to uppercase, lowercase or title
_replace_with_attr -- replace the whole content with the value of an attribute
text-replace    -- replace a string inside a content with another
```

## Examples
Here are few command line arguments samples.

### Illustrations
If the diffs complain about a disppearing "Illustration" tag in the
html, add the following rule (adapt the CSS selector):

```
--css '.figcenter:before { content: "[Illustration: "; }'
--css '.figcenter:after { content: "]"; }'
--css '.figcenter:before { content: "[Illustration: "; }'
```

### Anchors
By default anchors are expected to be surrounded by brackets. If it is
not the case in the html, this can be easily fixed with the following:

```
--css '.fnanchor:before { content: "["; } .fnanchor:after { content: "]"; }'
```

### Small caps
Small caps can be transformed to look like the same in the text (upper
case). This can considerably reduce the noise in a document.

```
--css '.smcap {  text-transform:uppercase; }'
```

### Greek
By default, if there is some greek and the text version has
transliterration only (i.e. it's in latin1), and if the html also has
the transliteration in the title attribute, the following is applied:

```
--css 'body *[lang=grc] { _replace_with_attr: "title"; }'
--css 'body *[lang=grc]:before, body *[lang=grc]:after { content: "+"; }'
```

Something like `φαγέδαινα` would become `+phagedaina+`
instead before the comparison takes place.

### Footnotes
In many document, the semantic of a footnote is html is lost because
they are put at the end of the file and look like any other
paragraph. A future version will add some extensions to deal with
that.