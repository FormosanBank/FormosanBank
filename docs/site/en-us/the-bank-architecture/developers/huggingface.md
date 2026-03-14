# 🤗 HuggingFace

FormosanBank has a comprehensive collection of audio files associated with its linguistic corpus, hosted on Hugging Face under the FormosanBank organization. These files are essential for linguistic research, language education, and preservation efforts.  The audio files are grouped in FormosanBank organization on huggingFace, which can be accessed from [here](https://huggingface.co/FormosanBank). HuggingFace was used due to its ease facilitation of open-access work and its comprehensive API tools. There are two ways to access the audio files via huggingFace. First method would be to simply clone the repo you're interested in. To do that, you will need to have git lfs (large file storage) installed. You can find more about git lfs [here](https://git-lfs.com/) and about cloning using https [here](https://huggingface.co/docs/hub/en/repositories-getting-started). The second option would be to use the provided Python script as part of FormosanBank codebase.&#x20;

Using the provided script provide a number of advantages. First off, due to huggingFace limit on the number of files per repo (100,000), audio files for some of the corpora, such as ePark, are spread over multiple repos. If you opt to clone the repos yourself, you will need to clone all the different repos of a specific corpus to get the audio data associated with it. Using the script would allow you to specify a language to get the audio files for, and it will automatically retrieve the files from the relevant repos. Additionally, the script provides the option to download all the audio files from across the different corpora for a specific language. The following sections provide step-by-step instructions on how to download the audio files efficiently.

### Downloading Audio Files via Script

Dedicated Bash script is available to facilitate downloading the audio files based on corpus or language. Each individual corpus that has associated data on HuggingFace should have a `download_audio_data.sh` script in its root directory. There is also a Bash script `run_audio_downloads.sh` in the root directory of FormosanBank that will find and run all the individual download scripts.

#### Running the Script

**1. Downloading by Corpus**

To download audio files based on a specific corpus, `cd` to the root directory of that corpus and use the following command:

```bash
./download_audio_data.sh
```

**2. Downloading all audio**

To download all audio for all corpora that have them, `cd` to the root directory of FormosanBank and use the following command:

```bash
./run_audio_downloads.sh
```

### Dealing with Large Corpora

Since Hugging Face imposes a directory limit of 10,000 files, some corpora (e.g., Rukai in ILRDF\_Dicts) are stored in batches. The script automatically handles these cases, merging the batches into the proper FormosanBank folder structure upon download.

***

By following these steps, you can efficiently download the necessary FormosanBank audio files for research and revitalization purposes.

## Creating New Corpora

If you create a new corpus that has audio on HuggingFace, you need to create a `download_audio_data.sh` script. In theory, this could work any way you want, but for consistency, it is best to use `git lfs` to download from a HuggingFace dataset within the FormosanBank organization. If you need multiple datasets (because the total amount of data is too much), it is recommended to give each one a prefix so that you can then automatically search for and download all datasets with that prefix. For an example, see `Corpora/ePark/download_audio_data.sh`.