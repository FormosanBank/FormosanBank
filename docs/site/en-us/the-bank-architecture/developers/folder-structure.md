---
icon: folder-open
---

# Folder structure

To maintain consistency and ensure smooth processing, FormosanBank follows a specific folder structure for organizing its corpora, raw data, processed files, and associated audio. This structure is crucial for efficient QC operations and for developers who want to follow the existing codebase or build on top of it.

### Corpus Organization

Each corpus is contained within its own folder, and inside each corpus folder, the following components are present:

* **Raw Data**: The original dataset before processing.
* **Processing Code**: Scripts used to convert raw data into the final structured corpus.
* **Documentation**: Includes README files and requirements files.
* **XML**: The processed corpus in XML format.
* **Audio**: The corresponding audio files aligned with the XML data.
* download_audio_data.sh: If and only if there is audio data, this script should contain the necessary code to retrieve the audio from HuggingFace.

Note that the GitHub repo does not contain the `Audio` file, since the Audio should be stored on HuggingFace.

### Structure of the `XML` Directory

The `XML` folder houses the processed corpus files. While there is some flexibility in how this directory is structured, a critical requirement is that it must contain a subdirectory named after the specific Formosan language.

#### Common Organizational Approaches:

1. **Directly by Language** (e.g., ILRDF\_Dicts)
   * `ILRDF/XML/Amis/`
   * `ILRDF/XML/Paiwan/`
   * `ILRDF/XML/Tsou/`
2. **By Topic** (e.g., ePark)
   * `ePark/XML/`ep1\_九階教材`/Amis`&#x20;
3. **By Speaker** (e.g., NTU Paiwan ASR)
   * `NTU_Paiwan_ASR/XML/Paiwan/`Belmira`/`

Regardless of the structure chosen, **every corpus must include a directory named after the Formosan language**. This can be a top-level directory or nested within another category. Even if a corpus contains only one language (e.g., NTU Paiwan ASR), a folder with the language name must be present for consistency.&#x20;

### Structure of the `Audio` Directory

For every `XML` directory, there exists a corresponding `Audio` directory that follows the same hierarchy.

*   If the path for XML files is:

    ```
    path/to/XML
    ```

    Then the equivalent path for audio files is:

    ```
    path/to/Audio
    ```

#### Mapping XML Files to Audio Files

The relationship between XML and audio files follows two main cases:

1. **Segmented Audio** (Multiple audio files per XML)
   * If an XML file contains multiple segments, a corresponding directory holds the segmented audio files.
   *   Example:

       ```
       ILRDF/XML/Amis/Amis.xml → ILRDF/Audio/Amis/Amis/
       ```

       * `ILRDF/Audio/Amis/Amis/` contains the audio files referenced in `ILRDF/XML/Amis/Amis.xml`.
2. **Unsegmented Audio** (Single audio file per XML)
   * If an XML file corresponds to a single audio file, the audio file is directly mapped to it.
   *   Example:

       ```
       NTU_Paiwan/XML/Paiwan/Belmira/02SC105-2_Belmira.xml → NTU_Paiwan/Audio/Paiwan/Belmira/[audio file]
       ```

### Importance of Following This Structure

This folder structure is integral to many of the quality control (QC) and processing scripts used in FormosanBank. Ensuring adherence to this format will allow for smooth execution of the existing code and prevent compatibility issues when extending or modifying the dataset.

By following this structure, developers and researchers can efficiently navigate, process, and expand upon the FormosanBank resources.
