# What ppcomp Does

## Usage:

| Option                       | File type | Description                                                               |
|------------------------------|----|---------------------------------------------------------------------------|
| -h                           |    | Show usage                                                                |
| --ignore-case                | All | Ignore case when comparing                                                |
| --extract-footnotes          | All | Extract and process footnotes separately                                  |
| --suppress-footnote-tags     | Txt | Suppress \[Footnote ?: ] marks                                            |
| --suppress-illustration-tags | Txt | Suppress \[Illustration: ] marks                                          |
| --suppress-sidenote-tags     | Txt | Suppress \[Sidenote: ] marks                                              |
| --ignore-format              | Rounds | Silence formatting differences (\<i>, \<b>)                               |
| --suppress-proofers-notes    | Rounds | Remove \[**proofreaders notes]                                            |
| --regroup-split-words        | Rounds | Regroup split wo-* *rds                                                   |
| --txt-cleanup-type TYPE      | Rounds | Type of text cleaning -- (b)est effort \[default], (n)one, (p)roofers     |
| --css-greek-title-plus       | HTML | Use greek transliteration in title attribute **(Obsolete?)**              |
| --css-add-illustration       | HTML | Add \[Illustration: ...] tags                                             |
| --css-add-sidenote           | HTML | Add \[Sidenote: ...] tags                                                 |
| --suppress-nbsp-num          | HTML | Suppress non-breakable spaces (U+00A0) between numbers |
| --ignore-0-space             | HTML | Suppress zero width space (U+200B)                                       |
| --css-smcap TYPE             | HTML | Transform small caps into uppercase (U), lowercase (L) or title case (T)  |
| --css-bold STR               | HTML | Surround bold strings with this string                                    |
| --css CSS                    | HTML | Insert transformation CSS (can be multiple)                               |
| --css-no-default             | HTML | Do not use default transformation CSS                                     |
| --simple-html                | HTML | Process an html file and print the output (debug)                         |

## Actions for all files:

- Remove PG boilerplate
- Extract footnotes (option)
- ~~"[oe]", "oe", "œ" ligature replacements~~ **(Obsolete: should now treat same as 'æ' - do nothing)**
- Character conversions - if one file has 1st char & other does not, convert:

| "Best"       | Plain            | Description                     |
| ------------ | ---------------- | ------------------------------- |
| ‘, ’         | '                | single curly quotes to straight |
| “, ”         | "                | double curly quotes to straight |
| º            | o                | ordinal o to letter o           |
| ª            | a                | ordinal a to letter a           |
| –            | -                | endash to regular dash          |
| —            | --               | emdash to double dash           |
| ⁄            | /                | fraction slash to slash         |
| ′            | '                | prime to single quote           |
| ″            | ''               | double prime to single quotes   |
| ‴            | '''              | triple prime to single quotes   |
| ₁, ₂, ₃, ... | 1, 2, 3,  ...    | subscript to number             |
| ¹, ², ³, ... | 1, 2, 3, ...     | superscript to number           |
| ½, ¼, ¾      | -1/2, -1/4, -3/4 | **(Obsolete, or add more?)**    |

## Actions for all text files:

- Remove "[Illustration: ]" tags (option)
- Remove "[Sidenote: ]" tags (option)
- Remove "[Footnote: ]" tags (option)

- Type of text cleaning:
  - (b)est effort \[default]: All
  - (n)one: Remove PG boilerplate only
  - (p)roofers: Remove page markers, "\[Blank page]" only

## Actions for text files from rounds ("projectID...")

- Remove page markers, "[Blank page]"
- If silence formatting differences: remove "\<i>" and "\<b>", else replace with '_', '='
- Remove proofers notes (option)
- Regroup split words (option) (works, but can't tell when hyphen should be kept)
- Remove block markup
  - "/\*", "\*/",
  - "/#", "#/"
  - "/P", "P/"
  - "/F", "F/"
  - "/X", "X/"

## Actions for processed text files:

- Remove thought breaks "*     *     *     *     *"
- If ignore format remove '_', '='

## Actions for HTML files:

- Remove page numbers
  - \<span class="pagenum"
  - \<span class="pageno"
  - \<span class="pgnum"
  - \<p class="pagenum"
  - \<p class="pageno"
  - \<p class="page"
  - \<div class="pagenum"
  - \<div class="pageno"
  - \<div id="Page_"
- Replace entities:
  - \&amp; to '&'
  - \&lt; to '<'
  - \&gt; to '>'
  - \&nbsp;, \&#160; to space **(New)**
  - \&mdash;, \&#151; to '--' **(New)**
- \<i>, \<em>, \<cite> to '_'

- \<b> to '='

- \<sup> to '^{}'

- \<sub> to '_{}'

- Remove non-breakable spaces (U+00A0) between numbers (option)

- Remove soft hyphen (U+00AD)

- Remove zero width space (U+200B) (option)

- Add "[Illustration: ]" tags (option)

- Add "[Sidenote: ]" tags (option)

- Use Greek transliteration in title attribute **(Obsolete?)**


## Proposed changes

- HTML5 parsing
- Update PG boilerplate removal
- Improve handling of superscripts and subscripts - Unicode/text markup/html markup
  - Superscripts should handle Unicode or ^{} in text, Unicode or \<sup> in html
  - Subscripts should handle Unicode or _{} in text, Unicode or \<sub> in html

