import pickle

# Load the citations_to_remove list from a pickle file
with open('citations_to_remove.pkl', 'rb') as fp:
    citations_to_remove = pickle.load(fp)

# Print the original list
print("Original citations_to_remove:", citations_to_remove)

# Append a new citation to the list
new_citation = ["vinecik ta katupu"]
citations_to_remove.extend(new_citation)

# Print the updated list
print("Updated citations_to_remove:", citations_to_remove)

# Save the updated list back to the pickle file
with open('citations_to_remove.pkl', 'wb') as fp:
    pickle.dump(citations_to_remove, fp)

