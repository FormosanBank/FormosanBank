import csv
import ast
import os

def escape_markdown(text):
    """
    Wraps text in backticks to prevent Markdown from misinterpreting special characters.
    """
    return f'`{text}`'

def generate_mismatch(csv_filename, report_filename):
    with open(csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        issues_by_language = {}

        for row in reader:
            language = row['language']
            file_name = row['file_name']
            sentence_id = row['Sentence_id']
            formosan = row['Formosan']
            # en = row['En']
            ch = row['Ch']

            # Parse the Formosan, En, Ch columns into lists
            try:
                formosan_list = ast.literal_eval(formosan)
            except Exception as e:
                issue = {
                    'sentence_id': sentence_id,
                    'error': f"Error parsing Formosan field: {e}"
                }
                issues_by_language.setdefault(language, []).append(issue)
                continue

            # try:
            #     en_list = ast.literal_eval(en)
            # except Exception as e:
            #     issue = {
            #         'sentence_id': sentence_id,
            #         'error': f"Error parsing English gloss field: {e}"
            #     }
            #     issues_by_language.setdefault(language, []).append(issue)
            #     continue

            try:
                ch_list = ast.literal_eval(ch)
            except Exception as e:
                issue = {
                    'sentence_id': sentence_id,
                    'error': f"Error parsing Chinese gloss field: {e}"
                }
                issues_by_language.setdefault(language, []).append(issue)
                continue

            # Check if the counts match
            formosan_count = len(formosan_list)
            # en_count = len(en_list)
            ch_count = len(ch_list)

            # if formosan_count != en_count or formosan_count != ch_count:
            if formosan_count != ch_count:
                # Record the issue
                issue = {
                    'language': language,
                    'file_name': file_name,
                    'sentence_id': sentence_id,
                    'formosan_list': formosan_list,
                    # 'en_list': en_list,
                    'ch_list': ch_list,
                    'formosan_count': formosan_count,
                    # 'en_count': en_count,
                    'ch_count': ch_count
                }
                issues_by_language.setdefault(language, []).append(issue)

    # Generate the Markdown report
    with open(report_filename, 'w', encoding='utf-8') as report_file:
        report_file.write('# Discrepancy Report\n\n')

        if not issues_by_language:
            report_file.write('No discrepancies found.\n')
        else:
            for language, issues in issues_by_language.items():
                report_file.write(f'## Language: {language}\n\n')
                for issue in issues:
                    if 'error' in issue:
                        # Display parsing errors
                        report_file.write(f'**Sentence ID:** {issue["sentence_id"]}\n\n')
                        report_file.write(f'**Error:** {issue["error"]}\n\n')
                    else:
                        report_file.write(f'**File:** {issue["file_name"]}\n\n')
                        report_file.write(f'**Sentence ID:** {issue["sentence_id"]}\n\n')
                        report_file.write(f'**Formosan morphemes ({issue["formosan_count"]}):** {escape_markdown(issue["formosan_list"])}\n\n')
                        # report_file.write(f'**English glosses ({issue["en_count"]}):** {escape_markdown(issue["en_list"])}\n\n')
                        report_file.write(f'**Chinese glosses ({issue["ch_count"]}):** {escape_markdown(issue["ch_list"])}\n\n')

                    report_file.write('---\n\n')

    print(f'Report generated: {report_filename}')

# Example usage:
if __name__ == "__main__":
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    for item in ["Stories", "Grammar", "Sentences"]:
        generate_mismatch(
            os.path.join(curr_dir, "Final_XML", item, "mismatch_issues.csv"),
            os.path.join(curr_dir, "Final_XML", item, f"{item}_discrepancy_report.md")
    )
