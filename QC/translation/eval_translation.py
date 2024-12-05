import pickle
import re
import numpy as np
import math
import xml.etree.ElementTree as ET
namespace = {'xml': 'http://www.w3.org/XML/1998/namespace'}

def log_odds(p):
    if p == 0:
        return float('-inf')  # log(0) is negative infinity
    elif p == 1:
        return float('inf')   # log(1) is positive infinity
    else:
        return math.log(p / (1 - p))
    
def strToDict(alignStr):
    given_string = alignStr.replace(" ", "")

    # Find all key-value pairs using regular expressions
    pairs = re.findall(r'(\w+)\s*\(\s*({[^{}]*})\s*\)', given_string)
    print(pairs)
    # Initialize an empty dictionary to store the result
    result_dict = {}

    # Iterate over the pairs and construct the dictionary
    for key, values in pairs:
        values_set = set(map(str, values.split()))

        values_set = re.sub("[{}]", "", list(values_set)[0])
        values_set = set(x for x in values_set)
        if key in result_dict:
            result_dict[key + "_2"] = values_set
        else:
            result_dict[key] = values_set

    return result_dict

with open("tmp/alignement_results.pkl", mode="rb") as pfile:
    align = pickle.load(pfile)
with open("tmp/amis_lex.pkl", mode="rb") as pfile:
    lexicon = pickle.load(pfile)

with open("EvalAlign.csv", mode="w", encoding="utf-8") as cfile:
    # gizascore is the likelihood score output by giza, alignSTD is the standard deviation of something output by giza, 
    # lexcheck is a score based on lexicon check and sizediff is a score based on the difference of size of the source
    #and target utterance.
    cfile.write("collection, xml, id, gizaScore, alignSTD, lexCheck, sizeDiff\n")
    for collection in align:
        print(collection)
        
        for i, sent in enumerate(align[collection]):
            tree = ET.parse("MT-xml-part-one/{}/{}".format(collection, sent["xml"]))
            root = tree.getroot()
            target_id = sent["id"]
            target_s_element = root.find(f'.//S[@id="{target_id}"]')
            print(sent)
            form_content = target_s_element.find('FORM').text
            translation_content = target_s_element.find('TRANSL[@xml:lang="en"]', namespaces=namespace).text
            terms = []
            knownTerms = 0
            amis_sent = re.sub(r'\([^()]*\)', '', sent["align"])
            amis_sent = amis_sent.replace("NULL", "")
            yesWord = 0
            small_set = {}
            aling_dict = strToDict(sent["align"])
            alignChaos = [len(aling_dict[x]) for x in aling_dict]
            print(aling_dict)
            print(np.std(alignChaos))
            print(alignChaos)
            Warning = ""
            # Check score based on punctuations.
            qutMarkEN = translation_content.count("?")
            qutMarkAM = form_content.count("?")
            exkMarkEN = translation_content.count("!")
            exkMarkAM = form_content.count("!")

            if qutMarkAM!=qutMarkEN or exkMarkEN!= exkMarkAM:
                Warning = True
            refs = []
            for elt in sent["english"].split():
                if elt in lexicon:
                    refs.append(elt)

                    knownTerms+=1
                    terms = terms+[x.replace("o", "u").lower() for x in lexicon[elt]]
                    small_set[elt] = lexicon[elt]
            terms = set(terms)
            for word in set(amis_sent.split()):
                if word.replace("o", "u").lower() in terms:
                    yesWord+=1
            if knownTerms!=0:
                lex_check = yesWord/knownTerms

                if knownTerms==1:
                    knownTerms+=1
                lex_check = lex_check * (1/math.sqrt(knownTerms))
                # print(lex_check)
                # lex_check = [math.log(p / (1 - p)) if p != 0 and p != 1 else (float('inf') if p == 1 else float('-inf')) for p in [lex_check]][0]

            else:
                lex_check = -1

            size_diff = len(amis_sent.split())/len(sent["english"].split())*100
            cfile.write("{},{},{},{},{},{},{},{}\n".format(collection, sent["xml"], sent["id"], float(sent["score"]), float(np.std(alignChaos)),float(lex_check), float(size_diff), Warning))