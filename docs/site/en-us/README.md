---
icon: hand-wave
cover: https://gitbookio.github.io/onboarding-template-images/header.png
coverY: 0
layout:
  cover:
    visible: true
    size: full
  title:
    visible: true
  description:
    visible: false
  tableOfContents:
    visible: true
  outline:
    visible: true
  pagination:
    visible: true
---

# Welcome

Welcome to FormosanBank, a large-scale data-driven project dedicated to the preservation and revitalization of the indigenous languages of Taiwan. These languages, which form a significant part of the Austronesian language family, are endangered, with some facing the risk of extinction. 

The Taiwanese indigenous languages are possessed of a remarkable number of corpora, particularly by comparison to other "under-resourced" languages. However, these materials are typically difficult to find, in a bewildering variety of formats, and rarely in machine-readable formats. Thus, while in aggregate a substantial corpus exists, in practice researchers and technology developers are restricted in what they can actually use.

The goal of FormosanBank is to eliminate this bottleneck, providing researchers, technology developers, educators, and community members with a central repository of critical linguistic data. Similar to CHILDES or Pangloss, FormosanBank is a corpus of corpora. Data [from different sources](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/corpora) are compiled and standardized. FormosanBank is also [FAIR](https://www.nature.com/articles/sdata201618): Free, Accessible, Interoperable, and Reusable. 

Currently, the corpus covers 17 languages to date, including 16 extant languages and 1 dormant language. In total, the corpus includes 7.3 million tokens and 700 hours of audio. Much of it is translated into Mandarin, English, or both. A smaller portion includes morphosyntactic glosses, typically on the order of 10k-20k sentences per language. A detailed breakdown can be found [here](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/corpora).

Learn more about the goals of FormosanBank and how it differs from other corpus projects [here](https://ai4commsci.gitbook.io/formosanbank/background/formosanbank).

## Rules of the Road

FormosanBank is free to use and copy, but you *must cite the individual corpora as well as FormosanBank itself*. The required citation is listed on the page for the corpus, as well as in the XML files themselves. Respecting the copyright owners is not just required by law, but ensures people continue to contribute their work so that all of us may benefit. Note that while some corpora are licensed for commercial use, most are not. The license is listed on the page for each corpus and in each XML file. If you wish to license materials for commercial use, we can help you reach out to the copyright owners. 

## Accessing and Using FormosanBank

FormosanBank is accessible through the [GitHub repository](https://github.com/FormosanBank/FormosanBank), with audio hosted by [HuggingFace](https://huggingface.co/FormosanBank).

The repository comes with many useful utility scripts, which are documented in these pages.

We strongly recommend you carefully read the documentation before using any data. For instance, not undestanding the [XML format](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/formosanbank-xml-format) is likely to lead to wildly inaccurate results. (This has happened.) Similarly, while we have standardized what we can, there are non-trivial differences across corpora that you should be aware of, and which are documented on each corpus page. 

A good place to start is the [overview page](https://ai4commsci.gitbook.io/formosanbank/background/formosanbank).

## Participants and Contributors

The large-scale nature of FormosanBank would not have been possible without the collaborative efforts of numerous individuals and organizations.&#x20;

Principal Investigators

* [Joshua Hartshorne](https://www.mghihp.edu/ihp-directory/joshua-hartshorne)
* [Emily Prud'hommeaux](https://cs.bc.edu/~prudhome/)
* [Li-May Sung](https://drive.google.com/file/d/1pkqbvFYHUydbiGRhPIgkBigkh2hpSCYi/view)

Advisory Board

* [Chuan-Jie Lin](https://cse.ntou.edu.tw/p/412-1063-7780.php?Lang=en)
* [Damián Blasi](https://www.damianblasi.org/)
* Xuan Ruan
* Ūi-iū Kán
* [Yuyang Liu](https://ced.utaipei.edu.tw/teacher/info?id=100103)

And [our many contributors](https://ai4commsci.gitbook.io/formosanbank/additional-resources/contributors).
