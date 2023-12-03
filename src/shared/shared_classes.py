import os
import dataclasses
import regex as re
import pandas as pd
import json as json
from json import JSONEncoder
from string import Template
import unicodedata
from lxml import etree
from biblelib.word import BCVWPID, BCVID, fromusfm, fromosis
from greek_normalisation.utils import *
# import diff_match_patch as dmp_module


@dataclasses.dataclass
class Word:
    identifier: str
    alt_id: str
    text: str
    strongs: str
    gloss: str
    gloss2: str
    pos: str
    morph: str

@dataclasses.dataclass
class Verse:
    identifier: str
    book: str
    chapter: str
    verse: str
    usfm: str
    # the str is the Word.identifier so we can sort to ensure word order
    words: dict[str, Word] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Condition:
    """
    A conditional statement, as defined in the conditionals spreadsheet.
    """
    index: int
    reference: str
    english: str
    condition_class: str
    inverse: bool
    probability: str
    time_orientation: str
    illocutionary_force: str
    english_translations: str
    notes: str
    parallel_passages: str
    greek_protases: dict[str, str] = dataclasses.field(default_factory=dict)
    greek_apodoses: dict[str, str] = dataclasses.field(default_factory=dict)
    greek_protasis_words: dict[str, list] = dataclasses.field(default_factory=dict)
    greek_apodosis_words: dict[str, list] = dataclasses.field(default_factory=dict)

@dataclasses.dataclass
class NonCondition:
    """
    A non-conditional statement that uses a conditional conjuction (ει, εαν)
    """
    index: int
    reference: str
    english: str
    condition_class: str
    inverse: bool = False
    probability: list = dataclasses.field(default_factory=list)
    time_orientation: list = dataclasses.field(default_factory=list)
    illocutionary_force: list = dataclasses.field(default_factory=list)
    english_translations: str = ""
    notes: str = ""
    parallel_passages: str = ""
    greek_protases: dict[str, str] = dataclasses.field(default_factory=dict)
    greek_apodoses: dict[str, str] = dataclasses.field(default_factory=dict)
    greek_protasis_words: dict[str, list] = dataclasses.field(default_factory=dict)
    greek_apodosis_words: dict[str, list] = dataclasses.field(default_factory=dict)

# we need to make a custom encoder to handle the dataclass
class EntityDataEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

def remove_empty_elements(d):
    """recursively remove empty lists, empty dicts, or None elements from a dictionary"""
    # thank you, https://gist.github.com/nlohmann/c899442d8126917946580e7f84bf7ee7
    def empty(x):
        return x is None or x == {} or x == [] or x == ""

    if not isinstance(d, (dict, list)):
        return d
    elif isinstance(d, list):
        return [v for v in (remove_empty_elements(v) for v in d) if not empty(v)]
    else:
        return {k: v for k, v in ((k, remove_empty_elements(v)) for k, v in d.items()) if not empty(v)}


def expand_reference_range(key):
    t = Template('$chapter:$verse')
    chapter, verse = key.split(':')
    first, last = verse.split('-')
    return [t.substitute(chapter=chapter, verse=i) for i in range(int(first), int(last) + 1)]


def get_org_to_eng_map():
    # use copenhagen data to generate an ORG => ENG map
    org_to_eng_map = {}
    with open("C:/git/Copenhagen-Alliance/versification-specification/versification-mappings/standard-mappings/"
              "eng.json", "r") as read_file:
        eng = json.load(read_file)
        expanded = {}
        for eng_map in eng['mappedVerses']:
            if "-" in eng_map:
                org_map = eng['mappedVerses'][eng_map]
                keys = expand_reference_range(eng_map)
                vals = expand_reference_range(org_map)
                for i in range(0, len(keys)):
                    expanded[keys[i]] = vals[i]
        org_to_eng_map = {**eng['mappedVerses'], **expanded}

    return org_to_eng_map

def get_eng_to_org_map():
    # use copenhagen data to generate an ORG => ENG map
    erg_to_org_map = {}
    with open("C:/git/Copenhagen-Alliance/versification-specification/versification-mappings/standard-mappings/"
              "eng.json", "r") as read_file:
        eng = json.load(read_file)
        expanded = {}
        for eng_map in eng['mappedVerses']:
            if "-" in eng_map:
                org_map = eng['mappedVerses'][eng_map]
                keys = expand_reference_range(eng_map)
                vals = expand_reference_range(org_map)
                for i in range(0, len(keys)):
                    expanded[keys[i]] = vals[i]
        eng_to_org_map = {**expanded, **eng['mappedVerses']}

    return eng_to_org_map

def load_greek_nt_lines(source_edition):
    print(f"Loading {source_edition}")
    return_lines = {}
    previous_verse_id = "40001001"
    current_verse_id = ""
    words = {}
    macula_nodes_dir = 'c:/git/Clear/macula-greek/' + source_edition + '/nodes/'
    if source_edition == "NA27":
        macula_nodes_dir = "c:/git/Clear/nestle-aland-syntax-trees/na27/nodes/"
    elif source_edition == "NA28":
        macula_nodes_dir = "c:/git/Clear/nestle-aland-syntax-trees/na28/nodes/"

    for filename in os.listdir(macula_nodes_dir):
        if filename.endswith(".xml"):
            print("Processing " + filename)
            macula_xml = etree.parse(macula_nodes_dir + filename)
            macula_root = macula_xml.getroot()
            for item in macula_root.xpath(".//*[local-name() = 'Node'][@xml:id]"):
                if item.attrib.__contains__("ref"):
                    # we good
                    bcv = fromusfm(re.sub(r"\![0-9]+$", "", item.attrib["ref"]))
                    current_verse_id = bcv.ID
                    if current_verse_id != previous_verse_id:
                        # we need to dump verse info.
                        previous_bcv = BCVID(previous_verse_id)
                        return_lines[previous_verse_id] = Verse(previous_verse_id, previous_bcv.book_ID, previous_bcv.chapter_ID,
                                                                previous_bcv.verse_ID, previous_bcv.to_usfm(), words)
                        previous_verse_id = current_verse_id
                        words = {}
                    # all I need is identifier and text.
                    identifier = item.attrib['{http://www.w3.org/XML/1998/namespace}id']
                    text = re.sub(r"\p{P}", "", item.text)
                    word = Word(identifier, "", text, "", "", "", "", "")
                    words[identifier] = word
            # last verse of XML file
            bcv = BCVID(current_verse_id)
            return_lines[current_verse_id] = Verse(current_verse_id, bcv.book_ID, bcv.chapter_ID,
                                                    bcv.verse_ID, bcv.to_usfm(), words)

    return return_lines


# since greek_normalisation does not have a function to strip breathing marks, I'm adding one here
def strip_breathing(s):
    return nfc("".join(
        cp for cp in nfd(s) if cp not in BREATHING
    ))


def get_verse_text(verse):
    return_text = ""
    # case-insensitive? strip accents?
    # note: may need to sort words by keys to ensure order
    word_keys = list(verse.words.keys())
    word_keys.sort()
    for word in word_keys:
        return_text += strip_breathing(strip_accents(verse.words[word].text)) + " "
    return nfkc(re.sub(r" +", " ", return_text.rstrip().lower()))


def get_word_ids(verse):
    word_ids = list(verse.words.keys())
    word_ids.sort()
    return word_ids


def match_greek_string(ref, greek_to_match, reference_text, reference_text_ids):
    matched_ids = []
    match = strip_breathing(strip_accents(re.sub(r"[\p{P}ʼ]", "",greek_to_match).strip().lower()))
    if re.search(match,reference_text):
        pre_match = re.sub(r"^(.*)(" + match + ").*$", r"\1", reference_text)
        pre_match_count = len(pre_match.split(' '))
        match_count = len(match.split(' '))
        matched_ids = reference_text_ids[(pre_match_count - 1):(pre_match_count - 1) + match_count]
        # print(f"{ref}: Matched '{greek_to_match}' in '{reference_text}'")
    else:
        print(f"{ref}: Could not match '{greek_to_match}' in '{reference_text}'")

    return matched_ids


def get_references(current_ref):
    references = []
    # trim letters off end, change references to OSIS-compatible
    current_ref = re.sub(r'[a-z]$', "", current_ref)
    current_ref = re.sub(r'^James', "Jas", current_ref)
    current_ref = re.sub(r'^([12]) *Pe', r'\1Pet', current_ref)
    current_ref = re.sub(r'^([123]) *Jn', r'\1John', current_ref)
    current_ref = re.sub(r'^([123])\s+', r'\1', current_ref)
    # deal with ranges, make a list
    if current_ref.__contains__("-"):
        # range
        base_ref = current_ref.split("-")[0]
        final_verse = int(current_ref.split("-")[1])
        base_bcv = fromosis(base_ref)
        current_verse = int(base_bcv.verse_ID)
        while current_verse <= final_verse:
            # zeropad current_verse
            references.append(base_bcv.book_ID + base_bcv.chapter_ID + str(current_verse).zfill(3))
            current_verse += 1
    else:
        base_bcv = fromosis(current_ref)
        references.append(base_bcv.book_ID + base_bcv.chapter_ID + base_bcv.verse_ID)
    return references


def load_gnt_mapping_data(gnt_mapping_tsv):
    # First step is to read the TSV with mapping into a pandas dataframe
    df = pd.read_csv(gnt_mapping_tsv, sep='\t', header=0, dtype=str, encoding='utf-8', keep_default_na=False)
    # get identifiers in order
    source_ids = "NA27_ID"
    target_ids = "SBLGNT_ID"

    # dictionary to map between macula_source and target_source
    macula_to_translation = {}
    for row in df.index:
        if df[source_ids][row] != '':
            if df[target_ids][row] != '':
                macula_to_translation[df[source_ids][row]] = df[target_ids][row]
                macula_to_translation["n" + df[source_ids][row]] = "n" + df[target_ids][row]
                # macula_to_translation[df[source_ids][row] + "1"] = df[target_ids][row] + "1"

    return macula_to_translation


def get_words_from_ids(sblgnt_word_ids, word_id_key, sblgnt_verses):
    if len(sblgnt_word_ids) == 0:
        return ""
    previous_verse = BCVWPID(re.sub(r"^n", "", sblgnt_word_ids[0])).to_bcvid
    sblgnt_words = sblgnt_verses[previous_verse].words
    words = []
    previous_word_index = 0
    bool_first_word = True
    for word_id in sblgnt_word_ids:
        current_verse = BCVWPID(re.sub(r"^n", "", word_id)).to_bcvid
        if current_verse != previous_verse:
            previous_verse = current_verse
            sblgnt_words = sblgnt_verses[current_verse].words

        current_word_index = int(BCVWPID(re.sub(r"^n", "", word_id)).word_ID)
        if (current_word_index - previous_word_index > 1) and not bool_first_word:
            if re.search(r"d$", word_id_key):
                words.append("…")
        previous_word_index = current_word_index
        bool_first_word = False

        # append the proper word
        words.append(sblgnt_words[word_id].text)

    return " ".join(words)


def update_condition_fields(condition, fields_to_check):
    if not fields_to_check["condition_class"].__contains__(condition.condition_class):
        fields_to_check["condition_class"][condition.condition_class] = 0
    fields_to_check["condition_class"][condition.condition_class] += 1
    for probability in condition.probability:
        if not fields_to_check["probability"].__contains__(probability):
            fields_to_check["probability"][probability] = 0
        fields_to_check["probability"][probability] += 1
    for time_orientation in condition.time_orientation:
        if not fields_to_check["time_orientation"].__contains__(time_orientation):
            fields_to_check["time_orientation"][time_orientation] = 0
        fields_to_check["time_orientation"][time_orientation] += 1
    for illocutionary_force in condition.illocutionary_force:
        if not fields_to_check["illocutionary_force"].__contains__(illocutionary_force):
            fields_to_check["illocutionary_force"][illocutionary_force] = 0
        fields_to_check["illocutionary_force"][illocutionary_force] += 1

    return fields_to_check


def de_discontigify_word_id_list(word_ids, references, verses):
    return_ids = []
    reference_text_ids = []
    for reference in references:
        reference_text_ids.extend(get_word_ids(verses[reference]))

    start_word_id = word_ids[0]
    end_word_id = word_ids[-1]

    in_range = False
    for word_id in reference_text_ids:
        if word_id == start_word_id:
            in_range = True
        if in_range:
            return_ids.append(word_id)
        if word_id == end_word_id:
            in_range = False

    return return_ids
