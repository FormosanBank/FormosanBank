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
* **Final\_XML**: The processed corpus in XML format.
* **Final\_Audio**: The corresponding audio files aligned with the XML data.

### Structure of the `Final_XML` Directory

The `Final_XML` folder houses the processed corpus files. While there is some flexibility in how this directory is structured, a critical requirement is that it must contain a subdirectory named after the specific Formosan language.

#### Common Organizational Approaches:

1. **Directly by Language** (e.g., ILRDF\_Dicts)
   * `ILRDF/Final_XML/Amis/`
   * `ILRDF/Final_XML/Paiwan/`
   * `ILRDF/Final_XML/Tsou/`
2. **By Topic** (e.g., ePark)
   * `ePark/Final_XML/`ep1\_九階教材`/Amis`&#x20;
3. **By Speaker** (e.g., NTU Paiwan ASR)
   * `NTU_Paiwan_ASR/Final_XML/Paiwan/`Belmira`/`

Regardless of the structure chosen, **every corpus must include a directory named after the Formosan language**. This can be a top-level directory or nested within another category. Even if a corpus contains only one language (e.g., NTU Paiwan ASR), a folder with the language name must be present for consistency.&#x20;

### Structure of the `Final_Audio` Directory

For every `Final_XML` directory, there exists a corresponding `Final_Audio` directory that follows the same hierarchy.

*   If the path for XML files is:

    ```
    path/to/Final_XML
    ```

    Then the equivalent path for audio files is:

    ```
    path/to/Final_Audio
    ```

#### Mapping XML Files to Audio Files

The relationship between XML and audio files follows two main cases:

1. **Segmented Audio** (Multiple audio files per XML)
   * If an XML file contains multiple segments, a corresponding directory holds the segmented audio files.
   *   Example:

       ```
       ILRDF/Final_XML/Amis/Amis.xml → ILRDF/Final_Audio/Amis/Amis/
       ```

       * `ILRDF/Final_Audio/Amis/Amis/` contains the audio files referenced in `ILRDF/Final_XML/Amis/Amis.xml`.
2. **Unsegmented Audio** (Single audio file per XML)
   * If an XML file corresponds to a single audio file, the audio file is directly mapped to it.
   *   Example:

       ```
       NTU_Paiwan/Final_XML/Paiwan/Belmira/02SC105-2_Belmira.xml → NTU_Paiwan/Final_Audio/Paiwan/Belmira/[audio file]
       ```

### Importance of Following This Structure

This folder structure is integral to many of the quality control (QC) and processing scripts used in FormosanBank. Ensuring adherence to this format will allow for smooth execution of the existing code and prevent compatibility issues when extending or modifying the dataset.

By following this structure, developers and researchers can efficiently navigate, process, and expand upon the FormosanBank resources.
