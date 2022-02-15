# What ppcomp Does

## Usage:

| -h                           | Show usage                                                   |
| ---------------------------- | ------------------------------------------------------------ |
| --ignore-case                | ALL: Ignore case when comparing                              |
| --extract-footnotes          | ALL: Extract and process footnotes separately                |
| --suppress-footnote-tags     | TXT: Suppress [Footnote ?: ] marks                           |
| --suppress-illustration-tags | TXT: Suppress [Illustration: ] marks                         |
| --suppress-sidenote-tags     | TXT: Suppress [Sidenote: ] marks                             |
| --ignore-format              | TXT from the rounds: Silence formatting differences (<i>, <b>) |
| --suppress-proofers-notes    | TXT from the rounds: Remove [**proofreaders notes]           |
| --regroup-split-words        | TXT from the rounds: Regroup split wo-* *rds                 |
| --txt-cleanup-type TYPE      | TXT from the rounds: Type of text cleaning -- (b)est effort [default], (n)one, (p)roofers |
| --css-greek-title-plus       | HTML: use greek transliteration in title attribute **(Obsolete?)** |
| --css-add-illustration       | HTML: add [Illustration: ...] tags                           |
| --css-add-sidenote           | HTML: add [Sidenote: ...] tags                               |
| --suppress-nbsp-num          | HTML: Suppress non-breakable spaces between numbers (U+200b) (\&nbsp;, \&#160;) |
| --ignore-0-space             | HTML: suppress zero width space (U+200b)                     |
| --css-smcap TYPE             | HTML: Transform small caps into uppercase (U), lowercase (L) or title case (T) |
| --css-bold STR               | HTML: Surround bold strings with this string                 |
| --css CSS                    | HTML: Insert transformation CSS (can be multiple)            |
| --css-no-default             | HTML: do not use default transformation CSS                  |
| --simple-html                | HTML: Process an html file and print the output (debug)      |

## Actions for all files:

- Extract footnotes (option)
- Remove PG boilerplate
- "[oe]", "oe", "œ" ligature replacements **(Obsolete: should now treat same as 'æ', do nothing)**
- Character conversions - if one file has 1st char & other does not, convert
  - "’", "'"  # single close curly quote to straight
  - "‘", "'"  # single open curly quote to straight
  - '”', '"'  # double close curly quotes to straight
  - '“', '"'  # double open curly quotes to straight
  - "º", "o"  # ordinal o to letter o
  - "ª", "a"  # ordinal a to letter a
  - "–", "-"  # endash to regular dash
  - "—", "--" # emdash to double dashes
  - "½", "-1/2" **(Obsolete?)**
  - "¼", "-1/4" **(Obsolete?)**
  - "¾", "-3/4" **(Obsolete?)**
  - '⁄', '/'   # fraction slash
  - "′", "'"   # prime
  - "″", "''"  # double prime
  - "‴", "'''" # triple prime
  - "₀", "0"  # subscript 0
  - "₁", "1"  # subscript 1
  - "₂", "2"  # subscript 2
  - "₃", "3"  # subscript 3
  - "₄", "4"  # subscript 4
  - "₅", "5"  # subscript 5
  - "₆", "6"  # subscript 6
  - "₇", "7"  # subscript 7
  - "₈", "8"  # subscript 8
  - "₉", "9"  # subscript 9
  - "⁰", "0"  # superscript 0
  - "¹", "1"  # superscript 1
  - "²", "2"  # superscript 2
  - "³", "3"  # superscript 3
  - "⁴", "4"  # superscript 4
  - "⁵", "5"  # superscript 5
  - "⁶", "6"  # superscript 6
  - "⁷", "7"  # superscript 7
  - "⁸", "8"  # superscript 8
  - "⁹", "9"  # superscript 9
  - Superscripts: should handle Unicode or ^{} in text, Unicode or <sup> in html
  - Subscripts: should handle Unicode or _{} in text, Unicode or <sub> in html

## Actions for text files:

- Remove "[Illustration: ]" tags (option)
- Remove "[Sidenote: ]" tags (option)
- Remove "[Footnote: ]" tags (option)

## Actions for text files from rounds ("projectID...")

- Remove page numbers, [Blank page]
- If Silence formatting differences: remove "<i>" and "<b>", else replace with '_', '='
- Remove proofers notes (option)
- Regroup split words (option)
- Remove block markup
  - "/*", "*/",
  - "/#", "#/"
  - "/P", "P/"
  - "/F", "F/"
  - "/X", "X/"

## Actions for HTML files:

- Remove page numbers
- span[class^="pagenum"]
  - p[class^="pagenum"]
  - div[class^="pagenum"]
  - span[class^="pageno"]
  - p[class^="pageno"]
  - div[class^="pageno"]
  - p[class^="page"]
  - span[class^="pgnum"]
  - div[id^="Page_"]
- <i>, <em>, <cite> to ''
- <b> to '='
- <sup> to "^{}"
- <sub> to "_{}"
- Remove non-breakable spaces between numbers (option)
- Remove soft hyphen (U+00AD)
- Remove zero width space (U+200B)
- Add "[Illustration: ]" tags (option)
- Add "[Sidenote: ]" tags (option)
- Use Greek transliteration in title attribute **(Obsolete?)**

