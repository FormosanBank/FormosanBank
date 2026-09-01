#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Name: eval_align.py
Description: The following code is taken from https://github.com/eleferrand/data_quality_eval/blob/main/eval_align.py

This is a script that apply two methods to evaluate audio transcription quality. The first method is based on 
CTC alignement where the posterior probablity alignement score serves as a way to evaluate the transcription.
The second method is based on phonetic transcription with Allosaurus.
Author: Éric Le Ferrand
Date: 2024-07-09
Version: 1.0
License: Boston College
Usage:
    Provide usage examples if necessary.

Dependencies:
    List any external libraries or dependencies here.

"""

import os
import torch
import torchaudio
from tqdm import tqdm
import re
import numpy as np
# from utils_CTC import get_trellis, backtrack
import unidecode
from allosaurus.app import read_recognizer
from Levenshtein import ratio
import argparse
import pickle
import random

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
chars_to_remove_regex = '[\(\)\_\,\?\.\!\-\;\:\"\“\%\‘\”\�\"\[\]\(\)\*=/@\+><\^]'
ischar = re.compile("[A-Za-zÀ-ÖØ-öø-ÿ]")

def dtw_distance(s1, s2):
    """
    Compute the DTW distance between two strings.

    Args:
        s1 (str): First string.
        s2 (str): Second string.

    Returns:
        int: DTW distance.
    """
    n, m = len(s1), len(s2)
    # Create a 2D matrix to store DTW distances
    dtw = [[float('inf')] * (m + 1) for _ in range(n + 1)]
    
    # Initialize the starting point
    dtw[0][0] = 0
    
    # Compute the DTW distance
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1  # Cost is 0 if characters match, 1 otherwise
            dtw[i][j] = cost + min(
                dtw[i - 1][j],     # Insertion
                dtw[i][j - 1],     # Deletion
                dtw[i - 1][j - 1]  # Match/Substitution
            )
    
    # Return the final DTW distance
    return 1/(1+dtw[n][m])

def rand_score(data, lang):
    for entry in tqdm(data):
        entry["score"] = (random.randint(0,100))/100
        
# def get_ctc_score(data, lang):
#     """
#     Take in argument a path to a folder that have a wav and text subfolder that contains respectively wav files and their corresponding
#     transcription

#     The function apply a CTC alignement between the wav and the texts using a pretrained English wav2vec model and return
#     alignement posterior probability 
#     """
#     torch.random.manual_seed(0)
#     bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
#     model = bundle.get_model().to(device)
#     labels = bundle.get_labels()

#     # for wav_name in tqdm(list(os.listdir(wav_path))):
#     for entry in tqdm(data):
#         wav_path = entry["ref"]
#         raw_text = entry["sentence"]
#         with torch.inference_mode():
#             waveform, _ = torchaudio.load(wav_path)
#             emissions, _ = model(waveform.to(device))
#             emissions = torch.log_softmax(emissions, dim=-1)
#         emission = emissions[0].cpu().detach()
#         clean_raw = unidecode.unidecode(raw_text)
#         transcript= "|"+"|".join(w for w in clean_raw.split())+"|"
#         transcript = transcript.upper()
#         transcript = re.sub(chars_to_remove_regex, '', transcript)
#         transcript = re.sub("\d+", "", transcript)
#         if len(transcript)>1:
#             dictionary = {c: i for i, c in enumerate(labels)}
#             tokens = [dictionary[c] for c in transcript]
#             trellis = get_trellis(emission, tokens)
#             path = backtrack(trellis, emission, tokens)
#             # print(path)
#             if path != None:
#                 ctc_score = np.mean([x.score for x in path])
#                 entry["score"] = ctc_score
#                 # print(ctc_score)
#             else:
#                 entry["score"] = ctc_score
            

def phone_align(data, lang):
    if os.path.isfile(f"{lang}.pkl"):
        with open(f"{lang}.pkl", "rb") as pfile:
            ipa = pickle.load(pfile)
    else:
        ipa = {}
    cache_changed = False
    model = read_recognizer()
    # for wav_name in tqdm(list(os.listdir(wav_path))):
    for entry in tqdm(data):
        wav_path = entry["ref"]
        raw_text = entry["sentence"]
        if wav_path in ipa:
            phone_transc = ipa[wav_path]
        else:
            phone_transc = model.recognize(wav_path)
            ipa[wav_path] = phone_transc
            cache_changed = True
        transcript = re.sub(chars_to_remove_regex, '', raw_text)
        
        if len(transcript)>1:
            phone_unicode = unidecode.unidecode(phone_transc)
            phone_stream = phone_unicode.replace(" ", "")
            transc_stream = transcript.replace(" ", "")
            orig = transc_stream
            transc_stream = unidecode.unidecode(transc_stream)
            transc_stream = re.sub("\d+", "", transc_stream)
            # print(phone_stream,"\t", transc_stream, orig)
            score = ratio(phone_stream.lower(), transc_stream.lower())
            entry["score"] = score

    # changed to only dump the pickle file if the cache has changed to avoid unnecessary writes
    if cache_changed:
        with open(f"{lang}.pkl", "wb") as pfile:
            pickle.dump(ipa, pfile)

def phone_align_dtw(data, lang):
    if os.path.isfile(f"{lang}.pkl"):
        with open(f"{lang}.pkl", "rb") as pfile:
            ipa = pickle.load(pfile)
    else:
        ipa = {}
    model = read_recognizer()
    # for wav_name in tqdm(list(os.listdir(wav_path))):
    for entry in tqdm(data):
        wav_path = entry["ref"]
        raw_text = entry["sentence"]
        if wav_path in ipa:
            phone_transc = ipa[wav_path]
        else:
            phone_transc = model.recognize(wav_path)
            ipa[wav_path] = phone_transc
        transcript = re.sub(chars_to_remove_regex, '', raw_text)
        
        if len(transcript)>1:
            phone_unicode = unidecode.unidecode(phone_transc)
            phone_stream = phone_unicode.replace(" ", "")
            transc_stream = transcript.replace(" ", "")
            orig = transc_stream
            transc_stream = unidecode.unidecode(transc_stream)
            transc_stream = re.sub("\d+", "", transc_stream)
            # print(phone_stream,"\t", transc_stream, orig)
            score = dtw_distance(phone_stream.lower(), transc_stream.lower())
            entry["score"] = score
            with open(f"{lang}.pkl", "wb") as pfile:
                pickle.dump(ipa, pfile)


def main():

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--lang", type=str, default="smp")

    #your data path should contain a train and test folders with inside a set of wavs and txts files
    args = parser.parse_args()
    lang = args.lang

    
    # alignement_score = get_ctc_score(f"/mmfs1/data/leferran/data/Pangloss/{lang}/")
    phone_align_score = phone_align(f"/mmfs1/data/leferran/data/Pangloss/{lang}/")
    with open(f"alignement_scores_{lang}.csv", mode="w", encoding="utf-8") as cfile:
        cfile.write("fileName,ctc_score,allo_score\n")
        for file_name in phone_align_score:
            cfile.write(f"{file_name},{alignement_score[file_name]},{phone_align_score[file_name]}\n")


if __name__ == "__main__":

    main()