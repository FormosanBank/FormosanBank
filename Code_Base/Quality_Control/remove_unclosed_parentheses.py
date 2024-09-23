def remove_unclosed_parentheses(text):
    # This will hold indices of open parentheses
    stack = []
    # Convert text to a list of characters for easier manipulation
    text_list = list(text)

    # Iterate through the text
    for i, char in enumerate(text_list):
        if char == '(':
            # Store the index of the open parenthesis
            stack.append(i)
        elif char == ')':
            if stack:
                # If there's an open parenthesis to match, pop it from the stack
                stack.pop()
            else:
                # If there's no matching open parenthesis, remove this closing one
                text_list[i] = ''

    # At the end of the loop, any remaining indices in the stack are unmatched '('
    while stack:
        text_list[stack.pop()] = ''

    # Join the list back into a string and return the cleaned text
    return ''.join(text_list)

def clean_xml_string(input_file, output_file):
    # Read the XML file as a string
    with open(input_file, 'r', encoding='utf-8') as file:
        xml_content = file.read()

    # Remove unclosed parentheses
    cleaned_content = remove_unclosed_parentheses(xml_content)

    # Write the cleaned content back to a new file
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(cleaned_content)

# Example usage
input_file = "../../XML_Final/Amis/Glosbe_Dict/Amis_Glosbe.xml"  # Replace with your input XML file path
output_file = "../../XML_Final/Amis/Glosbe_Dict/Amis_Glosbe_cleaned.xml"  # Replace with your output XML file path

clean_xml_string(input_file, output_file)

print(f"Unclosed parentheses removed and saved to {output_file}.")
