# nt-conditionals
Data regarding conditional statements/clauses in the NT provided by Rachel and Mike Aubrey and CanIL (Steve Nicolle)

# License
This material is provided by the Canada Institute of Linguistics (CanIL) under a CC-BY-SA-4.0 license. 
More information about this license is available in the `LICENSE.md` file in this repository.

The JSON editions in the `/data` folder include phrases from the NA27 and the SBLGNT. The NA27 portions are minimal 
and considered fair use. The SBLGNT is available under a CC-BY-4.0 license, 
see [the LogosBible SBLGNT repository](https://github.com/LogosBible/SBLGNT) for more information and data.

# Documentation
The following documents were supplied with the data as documentation and explanation of the data. These are all in the `/docs` folder of this repo.

* `Conditionals in the Greek NT.pdf`: PDF of article about conditional statements in the Greek NT by Steve Nicolle.
* `Translating unless conditionals in the NT.pdf`: PDF of article detailing specific information on translating "unless" (εαν μη) statements in the Greek NT.
* `Categories used in the database.pdf`: PDF edition of supplied Word document that describes the vocabulary used in the data.

# Supplied Data
Rachel and Mike Aubrey supplied four files; two Excel spreadsheets and two PDFs. Another edition of the data, without Greek protasis or apodosis specified, is also availble. These are in the `data/raw` folder of this repo.

* `Conditionals in the Greek NT.pdf`: PDF of article about conditional statements in the Greek NT by Steve Nicolle.
* `Translating unless conditionals in the NT.pdf`: PDF of article detailing specific information on translating "unless" (εαν μη) statements in the Greek NT.
* `CanIL Analysis of NT Conditionals by book220831.xlsx`: Initial analysis by CanIL/Steve Nicolle
* `Database of NT Coditionals Unified with Greek Text.xlsx`: CanIL analysis with Greek text for protasis and apodosis directly specified and non-conditional uses removed. On Google Sheets: https://docs.google.com/spreadsheets/d/1c9O7WfxEICqYUk2w2S2kYFp1FqR2coNp/edit?usp=sharing&ouid=109636104918679310284&rtpof=true&sd=true 
* `Database of Non-conditional uses of ει and εαν-with Greek.xlsx`: Only non-conditional uses, with Greek text for protasis and apodosis directly specified. On Google Sheets: https://docs.google.com/spreadsheets/d/19TKF6ExTITYVM7Td8lGMEBr8Lje3HPtx/edit?usp=sharing&ouid=109636104918679310284&rtpof=true&sd=true

# Generated Data
Data has been generated representing the conditional statements for the NA27 edition of the Greek New Testament as well as the SBLGNT edition of the Greek New Testament.

* `data/json/nt-conditionals-na27.json`
* `data/json/nt-conditionals-sblgnt.json`
* `data/json/nt-non-conditionals-na27.json`
* `data/json/nt-non-conditionals-sblgnt.json`

Further, markdown forms of each JSON file have been generated and provided for easy visual reference.

* [`data/md/nt-conditionals-na27.md`](data/md/nt-conditionals-na27.md)
* [`data/md/nt-conditionals-sblgnt.md`](data/md/nt-conditionals-sblgnt.md)
* [`data/md/nt-non-conditionals-na27.md`](data/md/nt-non-conditionals-na27.md)
* [`data/md/nt-non-conditionals-sblgnt.md`](data/md/nt-non-conditionals-sblgnt.md)

# JSON Schema

The data from the Excel spreadsheets has been extracted and converted into a JSON format. The schema for this JSON is as follows:

<table>
<tr><td>property</td><td>type</td><td>value</td></tr>
<tr><td>index</td><td>int</td><td>integer providing order of spreadsheet, useful for sorting</td></tr>
<tr><td>reference</td><td>string</td><td>Bible reference as entered in the spreadsheet. Book names in this field use OSIS book names</td></tr>
<tr><td>english</td><td>string</td><td>English representing the entire conditional (or non-conditional) statement</td></tr>
<tr><td>inverse</td><td>bool</td><td>If `True` then the protasis and apodosis are in an inverted order (compared to default)</td></tr>
<tr><td>probability</td><td>list[string]</td><td>A word or two, following a prescribed vocabulary (see below), representing probability of condition evaluating as true</td></tr>
<tr><td>time_orientation</td><td>list[string]</td><td>A word or two, following a prescribed vocabulary (see below), representing the time orientation of the condition (or non-condition)</td></tr>
<tr><td>illocutionary_force</td><td>list[string]</td><td>A word or two, following a prescribed vocabulary (see below), providing information on the illocutionary force of the condition (or non-condition)</td></tr>
<tr><td>english_translations</td><td>string</td><td>Information about how English translations handle the condition (or non-condition)</td></tr>
<tr><td>notes</td><td>string</td><td>Discussion about the condition (or non-condition)</td></tr>
<tr><td>parallel_passages</td><td>string</td><td>Information about any relevant parallel passages</td></tr>
<tr><td>greek_protases</td><td>dict[str,str]</td><td>A dictionary listing each protasis with an identifier (e.g. `p1`)</td></tr>
<tr><td>greek_apodoses</td><td>dict[str,str]</td><td>A dictionary listing each apodosis with an identifier (e.g. `q1`)</td></tr>
<tr><td>greek_protasis_words</td><td>dict[str, list]</td><td>A dictionary that associates identifier (e.g. `p1`) with a list of word identifiers from Macula Greek representing the words of the protasis</td></tr>
<tr><td>greek_apodosis_words</td><td>dict[str, list]</td><td>A dictionary that associates identifier (e.g. `q1`) with a list of word identifiers from Macula Greek representing the words of the apodosis</td></tr>
</table>

# Field Vocabulary

The data uses several terms to describe aspects of probability, time orientation, and illocutionary force. These are 
listed below. More description of each field value is available in the word document `Categories used in the database.docx` 
found in the `data/raw` folder of this repository.

Occasionaly fields have an empty value (particularly in the "non-conditionals" data) or a value of "Not applicable".

## Vocabulary for `probability`

* Factual
* Very Likely
* Likely
* Neutral
* Unlikely
* Very Unlikely
* Non-factual

## Vocabulary for `time_orientation`

* Past
* Present
* Future
* Gnomic

## Vocabulary for `illocutionary_force`

* Argue
* Assert
* Command
* Encourage
* Exhort
* Mock
* Promise
* Rebuke
* Rebuke
* Request
* Warn