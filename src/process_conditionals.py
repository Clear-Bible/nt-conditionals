import copy
from shared.shared_classes import *

git_dir = "c:/git/Clear/"
root_dir = f"{git_dir}nt-conditionals/"
data_dir = f"{root_dir}data/"
gnt_mappings_tsv = f"{git_dir}macula-greek/sources/Clear/mappings/mappings-GNT-stripped.tsv"
na27_to_sblgnt_map = load_gnt_mapping_data(gnt_mappings_tsv)

# background: https://towardsdatascience.com/read-data-from-google-sheets-into-pandas-without-the-google-sheets-api-5c468536550
# conditionals spreadsheet google doc id: 1c9O7WfxEICqYUk2w2S2kYFp1FqR2coNp
# conditionals spreadsheet sheet name: Conditionals
sheet_id = "1c9O7WfxEICqYUk2w2S2kYFp1FqR2coNp"
sheet_name = "Conditionals"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
print(f"Loading '{sheet_name}' from '{sheet_id}' from Google Sheets ... ")
conditionals_df = pd.read_csv(url, encoding='utf-8', keep_default_na=False)

# load a map of na27 -> SBLGNT word identifiers

# list of conditional objects
nt_conditionals = [] # this is NA27
nt_conditionals_sblgnt = []

for row in conditionals_df.index:
    # create a conditionals object from the row in the dataframe
    inverse = False
    if conditionals_df['Inv.'][row] == "x":
        inverse = True
    greek_protasis = re.sub(r" +", " ", conditionals_df['Protasis'][row])  # will need to support multiline
    greek_apodosis = re.sub(r" +", " ", conditionals_df['Greek Apodosis'][row])  # will need to support multiline
    condition = Condition(
        index = int(conditionals_df['Index'][row]),
        reference = conditionals_df['Reference'][row],
        english = conditionals_df['Scope of Conditional (ESV unless noted)'][row],
        condition_class = conditionals_df['Class'][row],
        inverse = inverse,
        probability = conditionals_df['Probability'][row],
        time_orientation = conditionals_df['Time Orientation'][row],
        illocutionary_force = conditionals_df['Illocutionary Force'][row],
        english_translations = conditionals_df['English Translations'][row],
        notes = conditionals_df['Notes'][row],
        parallel_passages = conditionals_df['Parallel passages'][row], # will need to identify refs
        greek_protases = {},
        greek_apodoses = {},
        greek_protasis_words = {},
        greek_apodosis_words = {}
    )
    if re.search(r"\.\.\.", greek_protasis):
        # we have a noncontiguous protasis
        protasis = re.sub(r"\s+\.\.\.\s+", " " + greek_apodosis.strip() + " ", greek_protasis)
        condition.greek_protases["p1d"] = protasis
        condition.greek_apodoses["q1"] = greek_apodosis
    elif re.search(r"\.\.\.", greek_apodosis):
        # we have a noncontiguous apodosis
        apodosis = re.sub(r"\s+\.\.\.\s+", " " + greek_protasis.strip() + " ", greek_apodosis)
        condition.greek_protases["p1"] = greek_protasis
        condition.greek_apodoses["q1d"] = apodosis
    elif re.search("<OR>", greek_protasis):
        protases = greek_protasis.split("<OR>")
        condition.greek_protases["p1or"] = protases[0]
        condition.greek_protases["p2or"] = protases[1]
        apodoses = greek_apodosis.split("<OR>")
        condition.greek_apodoses["q1or"] = apodoses[0]
        condition.greek_apodoses["q2or"] = apodoses[1]
    elif re.search("<>", greek_protasis):
        protases = greek_protasis.split("<>")
        condition.greek_protases["p1"] = protases[0]
        condition.greek_protases["p2"] = protases[1]
        if re.search("<>", greek_apodosis):
            apodoses = greek_apodosis.split("<>")
            condition.greek_apodoses["q1"] = apodoses[0]
            condition.greek_apodoses["q2"] = apodoses[1]
        else:
            condition.greek_apodoses["q1"] = greek_apodosis
    elif re.search("<>", greek_apodosis):
        apodoses = greek_apodosis.split("<>")
        condition.greek_apodoses["q1"] = apodoses[0]
        condition.greek_apodoses["q2"] = apodoses[1]
        condition.greek_protases["p1"] = greek_protasis
    else:
        condition.greek_protases["p1"] = greek_protasis
        condition.greek_apodoses["q1"] = greek_apodosis

    nt_conditionals.append(condition)

# ok, now cycle macula greek to create object representing the GNT (by verse?
# no NA27 TSV, so we have to do it by nodes.
na27_verses = load_greek_nt_lines("NA27")
sblgnt_verses = load_greek_nt_lines("SBLGNT")

# ok, now cycle conditionals and map the greek to words in macula
# need a function to parse the reference into a BCVWPID ... likely just map aubreys' book names to USFM
missed_matches = 0
total_attempts = 0


for conditional in nt_conditionals:
    current_ref = conditional.reference.strip()
    # what about ranges? skip for now?
    references = get_references(current_ref)
    reference_text = ""
    reference_text_ids = []
    for reference in references:
        reference_text += get_verse_text(na27_verses[reference]) + " "
        reference_text_ids.extend(get_word_ids(na27_verses[reference]))
    # do we just do a diff here, and grab the match?
    protasis_word_ids = {}
    for protasis in conditional.greek_protases:
        protasis_word_ids[protasis] = match_greek_string(current_ref, conditional.greek_protases[protasis], reference_text, reference_text_ids)
        total_attempts += 1
        if len(protasis_word_ids[protasis]) == 0:
            missed_matches += 1
    conditional.greek_protasis_words = protasis_word_ids
    apodosis_word_ids = {}
    for apodosis in conditional.greek_apodoses:
        apodosis_word_ids[apodosis] = match_greek_string(current_ref, conditional.greek_apodoses[apodosis], reference_text, reference_text_ids)
        total_attempts += 1
        if len(apodosis_word_ids[apodosis]) == 0:
            missed_matches += 1
    conditional.greek_apodosis_words = apodosis_word_ids

    # ok, now find items with either p1d or q1d and clean them up
    if conditional.greek_protases.__contains__("p1d"):
        # we have a noncontiguous protasis
        protasis = conditional.greek_protases["p1d"]
        apodosis = conditional.greek_apodoses["q1"]
        protasis = re.sub(apodosis, "…", protasis)
        conditional.greek_protases["p1"] = protasis
        del conditional.greek_protases["p1d"]
        # ok, word ids.
        for id_to_remove in conditional.greek_apodosis_words["q1"]:
            conditional.greek_protasis_words["p1d"].remove(id_to_remove)
        conditional.greek_protasis_words["p1"] = conditional.greek_protasis_words["p1d"].copy()
        del conditional.greek_protasis_words["p1d"]

    elif conditional.greek_apodoses.__contains__("q1d"):
        # we have a noncontiguous apodosis
        apodosis = conditional.greek_apodoses["q1d"]
        protasis = conditional.greek_protases["p1"]
        apodosis = re.sub(protasis, "…", apodosis)
        conditional.greek_apodoses["q1"] = apodosis
        del conditional.greek_apodoses["q1d"]
        # ok, word ids.
        for id_to_remove in conditional.greek_protasis_words["p1"]:
            conditional.greek_apodosis_words["q1d"].remove(id_to_remove)
        conditional.greek_apodosis_words["q1"] = conditional.greek_apodosis_words["q1d"].copy()
        del conditional.greek_apodosis_words["q1d"]

    # map word level stuff to SBLGNT, repopulate prot & apod words based on word references
    # conditional_sblgnt = dataclasses.replace(conditional)
    conditional_sblgnt = copy.deepcopy(conditional)
    # map what we can.
    for protasis_word_id_key in conditional_sblgnt.greek_protasis_words:
        protasis_word_ids = conditional_sblgnt.greek_protasis_words[protasis_word_id_key]
        sblgnt_protasis_word_ids = []
        for na27_word in protasis_word_ids:
            if na27_to_sblgnt_map.__contains__(na27_word):
                sblgnt_protasis_word_ids.append(na27_to_sblgnt_map[na27_word])
            else:
                # uh ... what?
                print(f"{conditional_sblgnt.reference}:{conditional_sblgnt.index}{protasis_word_id_key}"
                      f": Could not map {na27_word} to SBLGNT")
        conditional_sblgnt.greek_protasis_words[protasis_word_id_key] = sblgnt_protasis_word_ids
        # next, assemble the phrase based on the word ids and populate
        protasis_phrase = get_words_from_ids(conditional_sblgnt.greek_protasis_words[protasis_word_id_key], sblgnt_verses)
        conditional_sblgnt.greek_protases[protasis_word_id_key] = protasis_phrase
    for apodosis_word_id_key in conditional_sblgnt.greek_apodosis_words:
        apodosis_word_ids = conditional_sblgnt.greek_apodosis_words[apodosis_word_id_key]
        sblgnt_apodosis_word_ids = []
        for na27_word in apodosis_word_ids:
            if na27_to_sblgnt_map.__contains__(na27_word):
                sblgnt_apodosis_word_ids.append(na27_to_sblgnt_map[na27_word])
            else:
                # uh ... what?
                print(f"{conditional_sblgnt.reference}:{conditional_sblgnt.index}{apodosis_word_id_key}"
                      f": Could not map {na27_word} to SBLGNT")
        conditional_sblgnt.greek_apodosis_words[apodosis_word_id_key] = sblgnt_apodosis_word_ids
        # next, assemble the phrase based on the word ids and populate
        apodosis_phrase = get_words_from_ids(conditional_sblgnt.greek_apodosis_words[apodosis_word_id_key], sblgnt_verses)
        conditional_sblgnt.greek_apodoses[apodosis_word_id_key] = apodosis_phrase

    # append it, we're done
    nt_conditionals_sblgnt.append(conditional_sblgnt)


# report.
print(f"Total attempts: {total_attempts}")
print(f"Missed {missed_matches} matches.")
print(f"Matched {total_attempts - missed_matches} matches.")

# dump it out to json
with open(f'{data_dir}nt-conditionals-na27.json', 'w', encoding='utf-8') as outfile:
    interim = json.dumps(nt_conditionals, indent=2, cls=EntityDataEncoder, ensure_ascii=False)
    cleaned_interim = json.loads(interim, object_hook=remove_empty_elements)
    json.dump(cleaned_interim, outfile, indent=2, ensure_ascii=False)

with open(f'{data_dir}nt-conditionals-sblgnt.json', 'w', encoding='utf-8') as outfile:
    interim = json.dumps(nt_conditionals_sblgnt, indent=2, cls=EntityDataEncoder, ensure_ascii=False)
    cleaned_interim = json.loads(interim, object_hook=remove_empty_elements)
    json.dump(cleaned_interim, outfile, indent=2, ensure_ascii=False)
