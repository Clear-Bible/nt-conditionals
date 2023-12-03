import copy
from shared.shared_classes import *


git_dir = "c:/git/Clear/"
root_dir = f"{git_dir}nt-conditionals/"
data_dir = f"{root_dir}data/"
# load a map of na27 -> SBLGNT word identifiers
gnt_mappings_tsv = f"{git_dir}macula-greek/sources/Clear/mappings/mappings-GNT-stripped.tsv"
na27_to_sblgnt_map = load_gnt_mapping_data(gnt_mappings_tsv)

# background: https://towardsdatascience.com/read-data-from-google-sheets-into-pandas-without-the-google-sheets-api-5c468536550
# https://docs.google.com/spreadsheets/d/1ejNFQ4MK7kqdROPqIph5slBwpS2H5hDT/edit?usp=sharing&ouid=109636104918679310284&rtpof=true&sd=true
# non-conditionals spreadsheet google doc id: 1ejNFQ4MK7kqdROPqIph5slBwpS2H5hDT
# non-conditionals spreadsheet sheet name: Sheet 1
sheet_id = "1ejNFQ4MK7kqdROPqIph5slBwpS2H5hDT"
sheet_name = "Sheet 1"
# url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
print(f"Loading '{sheet_name}' from Google Sheets ... ")
non_conditionals_df = pd.read_csv(url, encoding='utf-8', keep_default_na=False)

# list of conditional objects
nt_non_conditionals_na27 = []
nt_non_conditionals_sblgnt = []

fields_to_check = {}
fields_to_check["condition_class"] = {}
fields_to_check["probability"] = {}
fields_to_check["time_orientation"] = {}
fields_to_check["illocutionary_force"] = {}


for row in non_conditionals_df.index:
    # create a conditionals object from the row in the dataframe
    inverse = False
    if non_conditionals_df['Inv.'][row] == "x":
        inverse = True
    greek_protasis = re.sub(r" +", " ", non_conditionals_df['Greek Protasis (p)'][row])
    greek_apodosis = re.sub(r" +", " ", non_conditionals_df['Greek Apodosis (q)'][row])
    if greek_apodosis == "–":
        greek_apodosis = ""
    non_condition = NonCondition(
        index = int(non_conditionals_df['Index'][row]),
        reference = non_conditionals_df['Reference'][row],
        english = non_conditionals_df['Non-conditional uses of εἰ and ἐὰν'][row],
        condition_class = non_conditionals_df['Class'][row],
        inverse = inverse,
        probability = re.split(r"\s*/\s*", non_conditionals_df['Probability'][row].strip()),
        time_orientation = re.split(r"\s*/\s*", non_conditionals_df['Time Orientation'][row].strip()),
        illocutionary_force = re.split(r"\s*/\s*", non_conditionals_df['Illocutionary Force'][row].strip()),
        english_translations = non_conditionals_df['English Translations'][row],
        notes = non_conditionals_df['Notes'][row],
        parallel_passages = non_conditionals_df['Parallel passages'][row], # will need to identify refs
        greek_protases = {},
        greek_apodoses = {},
        greek_protasis_words = {},
        greek_apodosis_words = {}
    )
    if re.search(r"\.\.\.", greek_protasis):
        # we have a noncontiguous protasis
        protasis = re.sub(r"\s*\.\.\.\s*", " " + greek_apodosis.strip() + " ", greek_protasis)
        non_condition.greek_protases["p1d"] = protasis
        non_condition.greek_apodoses["q1"] = greek_apodosis
    elif re.search(r"\.\.\.", greek_apodosis):
        # we have a noncontiguous apodosis
        apodosis = re.sub(r"\s*\.\.\.\s*", " " + greek_protasis.strip() + " ", greek_apodosis)
        non_condition.greek_protases["p1"] = greek_protasis
        non_condition.greek_apodoses["q1d"] = apodosis
    # elif re.search("<OR>", greek_protasis):
    #     protases = greek_protasis.split("<OR>")
    #     non_condition.greek_protases["p1or"] = protases[0]
    #     non_condition.greek_protases["p2or"] = protases[1]
    #     apodoses = greek_apodosis.split("<OR>")
    #     non_condition.greek_apodoses["q1or"] = apodoses[0]
    #     non_condition.greek_apodoses["q2or"] = apodoses[1]
    elif re.search("<>", greek_protasis):
        protases = greek_protasis.split("<>")
        p = 0
        for protasis in protases:
            p += 1
            non_condition.greek_protases["p" + str(p)] = protasis
        if re.search("<>", greek_apodosis):
            apodoses = greek_apodosis.split("<>")
            q = 0
            for apodosis in apodoses:
                q += 1
                non_condition.greek_apodoses["q" + str(q)] = apodosis
        else:
            non_condition.greek_apodoses["q1"] = greek_apodosis
    elif re.search("<>", greek_apodosis):
        apodoses = greek_apodosis.split("<>")
        q = 0
        for apodosis in apodoses:
            q += 1
            non_condition.greek_apodoses["q" + str(q)] = apodosis
        # because if protases had multiples, it would've been caught in the previous elif
        non_condition.greek_protases["p1"] = greek_protasis
    else:
        non_condition.greek_protases["p1"] = greek_protasis
        non_condition.greek_apodoses["q1"] = greek_apodosis

    # check fields to ensure we only have stuff we want/support/
    fields_to_check = update_condition_fields(non_condition, fields_to_check)

    nt_non_conditionals_na27.append(non_condition)

# ok, now cycle macula greek to create object representing the GNT (by verse?
# no NA27 TSV, so we have to do it by nodes.
na27_verses = load_greek_nt_lines("NA27")
sblgnt_verses = load_greek_nt_lines("SBLGNT")

# ok, now cycle conditionals and map the greek to words in macula
# need a function to parse the reference into a BCVWPID ... likely just map aubreys' book names to USFM
missed_matches = 0
total_attempts = 0


for non_conditional in nt_non_conditionals_na27:
    current_ref = non_conditional.reference.strip()
    references = get_references(current_ref)
    reference_text = ""
    reference_text_ids = []
    for reference in references:
        reference_text += get_verse_text(na27_verses[reference]) + " "
        reference_text_ids.extend(get_word_ids(na27_verses[reference]))
    # do we just do a diff here, and grab the match?
    protasis_word_ids = {}
    for protasis in non_conditional.greek_protases:
        protasis_word_ids[protasis] = match_greek_string(current_ref, non_conditional.greek_protases[protasis], reference_text, reference_text_ids)
        total_attempts += 1
        if len(protasis_word_ids[protasis]) == 0:
            missed_matches += 1
    non_conditional.greek_protasis_words = protasis_word_ids
    apodosis_word_ids = {}
    for apodosis in non_conditional.greek_apodoses:
        apodosis_word_ids[apodosis] = match_greek_string(current_ref, non_conditional.greek_apodoses[apodosis], reference_text, reference_text_ids)
        total_attempts += 1
        if len(apodosis_word_ids[apodosis]) == 0:
            missed_matches += 1
    non_conditional.greek_apodosis_words = apodosis_word_ids

    # ok, now find items with either p1d or q1d and clean them up
    if non_conditional.greek_protases.__contains__("p1d"):
        # we have a noncontiguous protasis
        protasis = non_conditional.greek_protases["p1d"]
        apodosis = non_conditional.greek_apodoses["q1"]
        protasis = re.sub(apodosis, "…", protasis)
        non_conditional.greek_protases["p1"] = protasis
        del non_conditional.greek_protases["p1d"]
        # ok, word ids.
        for id_to_remove in non_conditional.greek_apodosis_words["q1"]:
            non_conditional.greek_protasis_words["p1d"].remove(id_to_remove)
        non_conditional.greek_protasis_words["p1"] = non_conditional.greek_protasis_words["p1d"].copy()
        del non_conditional.greek_protasis_words["p1d"]
    elif non_conditional.greek_apodoses.__contains__("q1d"):
        # we have a noncontiguous apodosis
        apodosis = non_conditional.greek_apodoses["q1d"]
        protasis = non_conditional.greek_protases["p1"]
        apodosis = re.sub(protasis, "…", apodosis)
        non_conditional.greek_apodoses["q1"] = apodosis
        del non_conditional.greek_apodoses["q1d"]
        # ok, word ids.
        for id_to_remove in non_conditional.greek_protasis_words["p1"]:
            non_conditional.greek_apodosis_words["q1d"].remove(id_to_remove)
        non_conditional.greek_apodosis_words["q1"] = non_conditional.greek_apodosis_words["q1d"].copy()
        del non_conditional.greek_apodosis_words["q1d"]

    # map word level stuff to SBLGNT, repopulate prot & apod words based on word references
    # conditional_sblgnt = dataclasses.replace(conditional)
    non_conditional_sblgnt = copy.deepcopy(non_conditional)
    # map what we can.
    for protasis_word_id_key in non_conditional_sblgnt.greek_protasis_words:
        protasis_word_ids = non_conditional_sblgnt.greek_protasis_words[protasis_word_id_key]
        sblgnt_protasis_word_ids = []
        for na27_word in protasis_word_ids:
            if na27_to_sblgnt_map.__contains__(na27_word):
                sblgnt_protasis_word_ids.append(na27_to_sblgnt_map[na27_word])
            else:
                # uh ... what?
                print(f"{non_conditional_sblgnt.reference}:{non_conditional_sblgnt.index}{protasis_word_id_key}"
                      f": Could not map {na27_word} to SBLGNT")
        non_conditional_sblgnt.greek_protasis_words[protasis_word_id_key] = sblgnt_protasis_word_ids
        # next, assemble the phrase based on the word ids and populate
        protasis_phrase = get_words_from_ids(non_conditional_sblgnt.greek_protasis_words[protasis_word_id_key], sblgnt_verses)
        non_conditional_sblgnt.greek_protases[protasis_word_id_key] = protasis_phrase
    for apodosis_word_id_key in non_conditional_sblgnt.greek_apodosis_words:
        apodosis_word_ids = non_conditional_sblgnt.greek_apodosis_words[apodosis_word_id_key]
        sblgnt_apodosis_word_ids = []
        for na27_word in apodosis_word_ids:
            if na27_to_sblgnt_map.__contains__(na27_word):
                sblgnt_apodosis_word_ids.append(na27_to_sblgnt_map[na27_word])
            else:
                # uh ... what?
                print(f"{non_conditional_sblgnt.reference}:{non_conditional_sblgnt.index}{apodosis_word_id_key}"
                      f": Could not map {na27_word} to SBLGNT")
        non_conditional_sblgnt.greek_apodosis_words[apodosis_word_id_key] = sblgnt_apodosis_word_ids
        # next, assemble the phrase based on the word ids and populate
        apodosis_phrase = get_words_from_ids(non_conditional_sblgnt.greek_apodosis_words[apodosis_word_id_key], sblgnt_verses)
        non_conditional_sblgnt.greek_apodoses[apodosis_word_id_key] = apodosis_phrase

    # append it, we're done
    nt_non_conditionals_sblgnt.append(non_conditional_sblgnt)


# report.
print(f"Total attempts: {total_attempts}")
print(f"Missed {missed_matches} matches.")
print(f"Matched {total_attempts - missed_matches} matches.")

# dump it out to json
with open(f'{data_dir}nt-non-conditionals-na27.json', 'w', encoding='utf-8') as outfile:
    interim = json.dumps(nt_non_conditionals_na27, indent=2, cls=EntityDataEncoder, ensure_ascii=False)
    cleaned_interim = json.loads(interim, object_hook=remove_empty_elements)
    json.dump(cleaned_interim, outfile, indent=2, ensure_ascii=False)

with open(f'{data_dir}nt-non-conditionals-sblgnt.json', 'w', encoding='utf-8') as outfile:
    interim = json.dumps(nt_non_conditionals_sblgnt, indent=2, cls=EntityDataEncoder, ensure_ascii=False)
    cleaned_interim = json.loads(interim, object_hook=remove_empty_elements)
    json.dump(cleaned_interim, outfile, indent=2, ensure_ascii=False)


# report on field content for review
for field in fields_to_check:
    print(f"{field}:")
    for value in fields_to_check[field]:
        print(f"\t{value}: {fields_to_check[field][value]}")
