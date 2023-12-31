import regex as re
from shared.shared_classes import *


git_dir = "c:/git/Clear/"
root_dir = f"{git_dir}nt-conditionals/"
data_dir = f"{root_dir}data/json/"
output_dir = f"{root_dir}data/md/"
# gnt_edition = "NA27"
gnt_edition = "SBLGNT"

conditionals_json = f"{data_dir}nt-conditionals-{gnt_edition}.json"
non_conditionals_json = f"{data_dir}nt-non-conditionals-{gnt_edition}.json"


def render_as_markdown(condition, is_conditional):
    markdown = []
    markdown.append("\n")
    markdown.append(f"# {condition.reference}")
    markdown.append("\n")
    if condition.condition_class != "":
        markdown.append(f"* **Class:** {condition.condition_class}")
    elif is_conditional:
        markdown.append(f"* **Class:** None specified")
    if len(condition.probability) > 0:
        markdown.append(f"* **Probability:** {' / '.join(condition.probability)}")
    if len(condition.time_orientation) > 0:
        markdown.append(f"* **Time Orientation:** {' / '.join(condition.time_orientation)}")
    if len(condition.illocutionary_force) > 0:
        markdown.append(f"* **Illocutionary Force:** {' / '.join(condition.illocutionary_force)}")
    if condition.inverse:
        markdown.append(f"* **Inverse:** {condition.inverse}")

    markdown.append("\n")

    markdown.append(f"## English")
    english = re.sub(r"\n", "\n<br/>", condition.english)
    markdown.append(f"{english}")
    markdown.append("\n")
    # everything always has `.english_translations`, I hope.
    english_translations = re.sub(r"\n", "\n* ", condition.english_translations)
    markdown.append(f"* {english_translations}")
    markdown.append("\n")
    markdown.append(f"## Greek ({gnt_edition})")
    if condition.inverse:
        for apodosis in condition.greek_apodoses:
            markdown.append(f"* _{apodosis}_: {condition.greek_apodoses[apodosis]}")
        for protasis in condition.greek_protases:
            markdown.append(f"* _{protasis}_: {condition.greek_protases[protasis]}")
    else:
        for protasis in condition.greek_protases:
            markdown.append(f"* _{protasis}_: {condition.greek_protases[protasis]}")
        for apodosis in condition.greek_apodoses:
            markdown.append(f"* _{apodosis}_: {condition.greek_apodoses[apodosis]}")
    markdown.append("\n")

    if condition.notes != "":
        markdown.append(f"## Notes")
        notes = re.sub(r"\n", "\n\n", condition.notes)
        markdown.append(f"{notes}")
        markdown.append("\n")

    markdown.append(f"----------------")

    return "\n".join(markdown)


for file in [conditionals_json, non_conditionals_json]:
    output_file = file.replace("json", "md")
    is_conditional = True
    if re.search("non-", file):
        is_conditional = False
    with open(output_file, "w", encoding='utf-8') as outfile:
        with open(file, "r", encoding='utf-8') as infile:
            conditional_data_json = json.load(infile)
            for condition_data in conditional_data_json:
                condition = Condition(**condition_data)
                outfile.write(render_as_markdown(condition, is_conditional))

# that's it.
