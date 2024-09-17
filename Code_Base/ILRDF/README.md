# EndangeredLanguageL3
A project for scraping the ILRDF dictionaries for sentence-translation-audio groups for the preservation of the Formosan languages.


## Navigation
### .PanglossXML
If you're at this repo, you're probably here for this. PanglossXML contains a folder for each tribe. Within those folders, there is an audio folder and 2 XML files.

`tribeName_filePaths.xml` is a XML file in the FormosanBank format that contains objects with 4 important attributes. It contains 1) the  original Formosan sentence, 2) its Chinese translation, 3) the path to the audio file that corresponds to the Formosan sentence, and 4) the URL from which the audio was found.

`tribeName.xml` is similar to the above, but it lacks the audio file paths.

The Audio folder contains all of the mp3 files that are referenced in `tribeName_filePaths.xml`. If you are planning to move around these files, it is important that the relative path between the Audio folder and the XML is preserved. Otherwise, you may need to edit the file paths within the XMLs as needed.


### .Meta
Contains depreciated and experimental code. They may be interesting for future reference. Otherwise, it is not used in any significant capacity.


### .PickleScrapes
Contains a folder for each tribe. Within it are scrapes from the ILRDF's API compressed and stored using python's built-in pickle module. There are two types of pickles stored in these subfolders -- `ckpt` and `fails`

`ckpt` pickles contain all of the API outputs in a dictionary format of `{input word into API: API response}`. Very notably, `ckpt` will contain some entries whose values are "FAIL" since the scraping code bunches up all of them together. Therefore, always check for FAILs when using the `ckpt` pickles and be wary that it already include all fails in the event that you need to calculate percentages / do math with the length of `ckpt`.

`fails` pickles contain all of the failed words in a list format of `[failword1, failword2, failword3, ...]` These words are considered fails because the API did not return a proper json object for processing.


### Tribe Folders (Amis, Atayal, ..., Yami)
In this codebase, these folders are chiefly used to contain the pdfs of their respective dictionaries for processing. 

They do contain some text files that may be of interest. This was when the project was primarily using regex techniques to extract text from the pdfs as opposed to the API method being used now.

Text files with `stripped` in the title are from the original repository [here](https://github.com/Sarahyouuu/EndangeredLanguageL3) and contain the extracted text from the pdf dictionaries. The `.py` file also corresponds to the code that makes the `stripped` files.

The `no_br` file is a version of `stripped` but without brackets (parens, square brackets, etc.). The `no_br_no_te` similarly has no brackets, but also removes the text within the brackets.

These files may be of interest, but are far harder to work with than with the API.


### Python Notebooks
In the main repository are three ipynb files. These are `rescrape`, `xml-ify`, and `audioDL`. Together, all 3 were used in the listed order to obtain API responses, transform them into XML files, and then download the necessary audio files.


## Future Use
### Setup
If you plan to rerun this code, you will need a bit of setup. You will need the following: 

1. The pdf files of the dictionaries
2. An API key and endpoint
3. The python libraries specified in `requirements.txt`


For $1.$, the updated Formosan dictionaries should be placed in their respective folders in the main directory (e.g. the Amis dictionary does into the Amis folder). Also ensure that they are the only pdf files in the directory, since the `rescrape` code assumes that you only have 1 pdf in the directory. If there are old pdf files, either delete them or put them in a subfolder.


For $2.$, the API key and endpoint are both already provided. They will be key to using `rescrape` and are specified after the imports. Please make sure that you can call the API and get back a proper response before running the code. Please familiarize yourself with the basics of the `requests` if you need to check this step.

If it turns out that either the API key or the endpoint are invalid, you will have to contact the ILRDF in order to get the necessary information. Then, update `rescrape` to account for any new API info.

For $3.$, use pip to install from `requirements.txt`. The code was first ran on Python 3.11, so please be aware of this if you are running it far into the future.



### Notice for Code Execution 
You will need the aforementioned python notebooks in order to run the code. For all notebooks, please make sure that the first several cells are ran first before executing any code. This will ensure that the imports, static variables, and functions are all defined.

**Execution of all of the following code relies on your current situation, so please modify it to your needs and as you go. Please be aware of any changes as the slightest change (either to the API or to the code) can disrupt the process.**


### `rescrape`
Run this notebook first. The purpose of this notebook is to collect API calls and store them as pickles for later use. It does this by scraping text from the pdf dictionaries and extracting the words. It then makes a huge list of these words, then calls the API on each of them. It then saves all of the results (good or bad) using pickle.

If the new pdf dictionary files do not have a star icon next to word entries (★), then this notebook will not work. You will have to find another way to extract dictionary words. This is because the current dictionaries use the ★ char to note the frequency of words. The code takes advantage of this to find words to call on the API.

`rescrape` will collect API responses and put them into pickles, which you can learn more about above in the .PickleScrapes section. The code asks the API for json objects, though you can also ask for XML objects.

It is not advisable to run this code all in one go due to the risk of a network error, but it is possible. As an estimate, the code will take several days to run (~6 days) if ran all in one go and will need a good and constant internet connection to run effectively.

The current scraping loop relies on a currently commented-out cell with the variable `done` in order to run. Please uncomment the cell and run it so the scraping loop can run. Modify `done` as you go and make sure to rerun the cell. If a tribe name is in `done`, it will be skipped over during the execution process.

Additionally, if your code breaks mid-run, you will have to also use the additional `splittribe` and `last_ckpt` variables to continue the API scraping. Change `splittribe` to the tribe whose API run was interrupted. Change `last_ckpt` to the largest checkpoint (ckpt) saved in the .Pickle folder. If the scraping does break, you will have to use the code at the bottom to stitch the two results into a single pickle file. 

### `xml-ify`
After `rescrape`, run `xml-ify`. This will take the pickles and unpack them. The pickles for API calls are saved as ckpt with the format of `{word in dictionary: API call for that word}`. This code is fairly safe to run as-is, since there are no network operations. At maximum, it should take a minute or two to run.

This notebook will then begin to construct the final XML object that uses the FormosanBank formatting. Each API call has the potential for multiple word responses and each word respnose can have multiple sentences. The code looks at all words and all sentences and stitches them into the final XML. 

There is also a cell output that lists each tribe and 3 numbers associated with it. The numbers listed are in this order (from left to right):
1. Number of all API calls (fails included)
2. Number of entries in the final XML
3. Difference between 1. and 2.

If number in $3.$ is a positive number, that means that there are less entries in the final XML than words identified in the dictionary. A negative number means that more entries were obtained than expected. Negative numbers are preferred, and small positive numbers ($\leq 1000$) are also acceptable. Anything larger and there might be an error with the API.

### `audioDL`
Lastly, run `audioDL`. This code will primarily do 2 things:
1. Download the required audio.
2. Create the final XML, which will now have the filepaths listed.

Similar to `rescrape`, please take advantage of the `done` variable to break your job up into parts. I estimate that this code will take a few days to run (~2 days). Again, ensure that your network connection is good and that the device the code is running on is free to run for the entire run.

This code assumes all URLs link to the direct download for an mp3 file (which should be the case). If a download fails, you can run the bottommost cell to attempt to redownload it. If it turns out that there is an invalid file, you may want to consider pruning that result from the final XML.

**Note:** The final XML files use FormosanBank formatting, but due to the nature of the audio being on a per-sentence basis due to how the API works, the AUDIO tag will have URL and FILE attributes. The URL and FILE attributes are not specified in the FormosanBank format, but are unique to this repo's final data.

The final result is now an XML file that contains triplets of Formosan sentence, the translation, and audio file.

## QC
Multiple precautions were taken in order to ensure that the final XML is of usable quality.

### By-Hand
I selected a Formosan sentence in the pdf dictionaries and then checked for it in the final XML with ctrl-F. Many sentences were verified as being in the final XML and having the correct translation. Checking the audio file also generally seems to be accurate to the Formosan sentence.

Generally, most of the sentences were present and preserved (except for Truku, which is explained below).

### Via Code
The API calls ask for json objects, but there is a case wherein the API will return a json that indicates that it has failed. These are saved in the pickles folder in the fails, but also in the ckpts as `{failed word: "FAIL"}` (literally using the word "FAIL"). In these cases, they are not considered by subsequent code and are filtered out in the XML creation.

Of note, Truku has significant portions of it unavailable via API request. Of a total of ~31,000 entries, only ~4600 were of good quality. The reason for this is due to an API error (the specifics are  not currnently known), but its final quantity of ~4600 entries is comparable to other languages, so it is usable, though not fully explored. 

During XML creation, memoization was utilized to make sure that no clone sentences are present in the dictionary. Clones are somewhat expected since different words can have the same example sentence.

API entries were also required to have a URL to an audio file present. Therefore entries without audio files have been excluded from the final XML. This is also expected, since some words do not have example sentences (and thereby do not need audio).

Audio downloading also had a QC failsafe of redownloading failed entries. There was no need to prune the current batch of data, but if any audio fails were present / are found, these entries will be removed from the final XML. All audio files were also verified to have .mp3 endings and do have some associated data. 

## Credits
Usage of the ILRDF's data is allowed under the Creative Commons. 


Usage of the codebase follows the GNU GPL-3.0.
