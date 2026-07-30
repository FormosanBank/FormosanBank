# 🤗 HuggingFace

FormosanBank hosts most associated audio under the [FormosanBank organization on Hugging Face](https://huggingface.co/FormosanBank). You can clone an individual dataset with Git LFS, or use the download scripts included with the public FormosanBank repository. See [Git LFS](https://git-lfs.com/) and the [Hugging Face repository documentation](https://huggingface.co/docs/hub/en/repositories-getting-started) for direct cloning.

Some large corpora are spread across multiple Hugging Face datasets or batches. Their corpus-level scripts discover or download the required datasets and merge them into the layout expected by the XML, which is safer than cloning one dataset by hand.

### Downloading Audio Files via Script

Each corpus with remotely hosted audio has a `download_audio_data.sh` script in its root directory. `run_audio_downloads.sh` in the FormosanBank root finds and runs all of those corpus-level scripts. The current scripts require the Hugging Face CLI and, depending on the corpus, Git LFS and `jq`.

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

Large corpora such as ePark and the ILRDF dictionaries are stored across multiple datasets or batches. The provided script handles these cases and merges the downloads into the proper FormosanBank folder structure.

***

By following these steps, you can efficiently download the necessary FormosanBank audio files for research and revitalization purposes.

## Creating New Corpora

If you create a new corpus that has audio on Hugging Face, include a `download_audio_data.sh` script. For consistency, use FormosanBank datasets and preserve the directory layout expected by the XML. If the corpus spans multiple datasets, use a stable prefix so the script can discover and merge every batch. See `Corpora/ePark/download_audio_data.sh` for an example.
