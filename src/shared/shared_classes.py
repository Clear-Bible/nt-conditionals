import os
import dataclasses
import json as json
from json import JSONEncoder
from string import Template


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
    probability: str = ""
    time_orientation: str = ""
    illocutionary_force: str = ""
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
