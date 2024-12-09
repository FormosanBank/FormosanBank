#!/bin/zsh

# Define your list of languages
languages=("Amis" "Atayal" "Paiwan" "Bunun" "Puyuma" "Rukai" "Tsou" "Saisiyat" "Yami"
        "Thao" "Kavalan" "Truku" "Sakizaya" "Seediq" "Saaroa" "Kanakanavu")

Loop over each language and run the command
for lang in "${languages[@]}"; do
    echo "Processing language: $lang"
    python orthography/orthography_compare.py \
        --o_info_1 "./orthography/extract_logs/${lang}_ILRDF_Dicts" \
        --o_info_2 "./orthography/extract_logs/${lang}_ePark"
done

# corpus="Presidential_Apologies"

# for lang in "${languages[@]}"; do
#     echo "extracting orth info for language in $corpus language: $lang"
#     python orthography/orthography_extract.py \
#         --language "${lang}" \
#         --corpus "${corpus}"  \
#         --corpora_path "../Corpora"
# done