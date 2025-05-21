# 🤗 HuggingFace

FormosanBank has a comprehensive collection of audio files associated with its linguistic corpus, hosted on Hugging Face under the FormosanBank organization. These files are essential for linguistic research, language education, and preservation efforts.  The audio files are grouped in FormosanBank organization on huggingFace, which can be accessed from [here](https://huggingface.co/FormosanBank). HuggingFace was used due to its ease facilitation of open-access work and its comprehensive API tools. There are two ways to access the audio files via huggingFace. First method would be to simply clone the repo you're interested in. To do that, you will need to have git lfs (large file storage) installed. You can find more about git lfs [here](https://git-lfs.com/) and about cloning using https [here](https://huggingface.co/docs/hub/en/repositories-getting-started). The second option would be to use the provided Python script as part of FormosanBank codebase.&#x20;

Using the provided script provide a number of advantages. First off, due to huggingFace limit on the number of files per repo (100,000), audio files for some of the corpora, such as ePark, are spread over multiple repos. If you opt to clone the repos yourself, you will need to clone all the different repos of a specific corpus to get the audio data associated with it. Using the script would allow you to specify a language to get the audio files for, and it will automatically retrieve the files from the relevant repos. Additionally, the script provides the option to download all the audio files from across the different corpora for a specific language. The following sections provide step-by-step instructions on how to download the audio files efficiently.

### Downloading Audio Files via Script

A dedicated Python script is available to facilitate downloading the audio files based on corpus or language. The script, `retrieve_audio.py`, is located in the FormosanBank GitHub repository at:

[https://github.com/FormosanBank/FormosanBank/blob/main/QC/utilities/retrieve\_audio.py](https://github.com/FormosanBank/FormosanBank/blob/main/QC/utilities/retrieve_audio.py)

#### Running the Script

The script allows you to download audio files in two ways:

1. **By Corpus**: Downloads all audio files related to a specific corpus.&#x20;
2. **By Language**: Downloads all audio files for a specific language across corpora.

**1. Downloading by Corpus**

To download audio files based on a specific corpus, use the following command:

```bash
python QC/utilities/retrieve_audio.py by_corpus --XML_Path <path_to_XML_directory> --corpus <corpus_name> --languages <language_list>
```

**Required Arguments:**

* `--XML_Path`: Path to the directory containing the XML files associated with the corpus. Currently, it’s assumed that if you organize by\_corpus, you have the XML files of the desired corpus downloaded.
* `--corpus`: Name of the corpus (supported options at the moment are `ILRDF_Dicts`, `NTU_Paiwan_ASR`, `ePark`, `Whitehorn`).
* `--languages`: A list of languages to download for the specified corpus (or use `All` to download all available languages for that corpus; available languages per corpus can be found inside the script).

**Example:**

```bash
python QC/utilities/retrieve_audio.py by_corpus --XML_Path ../Whitehorn_Collection/Final_XML --corpus Whitehorn --languages All
```

**2. Downloading by Language**

To download audio files based on a specific language across multiple corpora, use:

```bash
python QC/utilities/retrieve_audio.py by_language --output_dir <output_directory> --languages <language_list>
```

**Required Arguments:**

* `--output_dir`: The directory where the downloaded audio files will be saved.
* `--languages`: The list of languages to download. Can be set to All.

**Example:**

```bash
python QC/utilities/retrieve_audio.py by_language --output_dir ./downloaded_audio --languages Amis
```

### Handling Download Interruptions

Due to the large number of files, the script may occasionally stop due to read-limit timeouts. However, it is designed to retrying until all the desired audio data is downloaded. If an interruption occurs to the script itself before it finishes running for any reason, simply re-run the command, and it will continue from the last completed point as huggingFace keeps track of which files were downloaded already. However, if you rerung the script after it finished running without interruptions, it will start the download from the beginning.

### Hugging Face Cache Considerations

* Files are first downloaded to the Hugging Face cache folder which is located at (`~/.cache/huggingface/hub`) on MacOS.
* The actual audio files are stored in the `blobs` directory within the cache, with filenames based on their SHA256 hash values.
* Once the script completes, it extracts and renames the downloaded files according to the symlink information in the snapshot directory.
* If a download is interrupted and not restarted, cached files may take up space—so periodically check and clear unnecessary cache data.

### Dealing with Large Corpora

Since Hugging Face imposes a directory limit of 10,000 files, some corpora (e.g., Rukai in ILRDF\_Dicts) are stored in batches. The script automatically handles these cases, merging the batches into the proper FormosanBank folder structure upon download.

***

By following these steps, you can efficiently download the necessary FormosanBank audio files for research and revitalization purposes.
