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

The goal of FormosanBank is to eliminate this bottleneck, providing researchers, technology developers, educators, and community members with a central repository of critical linguistic data. Similar to CHILDES or Pangloss, FormosanBank is a corpus of corpora. Data [from different sources](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/corpora) are compiled and standardized. FormosanBank is also [FAIR](https://www.nature.com/articles/sdata201618): Findable, Accessible, Interoperable, and Reusable.

Currently, the corpus covers 17 languages, including 16 extant languages and one dormant language. In total, the current public corpus includes about 8.2 million words and 703 hours of audio. Much of it is translated into Mandarin, English, or both. A smaller portion includes morphosyntactic glosses. A detailed, generated breakdown can be found [here](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/corpora).

Learn more about the goals of FormosanBank and how it differs from other corpus projects [here](https://ai4commsci.gitbook.io/formosanbank/background/formosanbank).

## Rules of the Road

FormosanBank is a mixed-source repository, so there is no single blanket license for all corpus material. Public use is available for noncommercial research, education, cultural work, and language revitalization, subject to each corpus's source terms, the [Terms of Use](additional-resources/terms-of-use.md), and the [AI Use Addendum](additional-resources/ai-use-and-commercial-licensing.md). You *must cite the individual corpora as well as FormosanBank itself*. The required citation and rights notice are listed on each corpus page and in the XML. Commercial AI use requires prior written permission from FormosanBank and any applicable rights holders.

## Accessing and Using FormosanBank

FormosanBank is accessible through the [GitHub repository](https://github.com/FormosanBank/FormosanBank), with audio hosted by [HuggingFace](https://huggingface.co/FormosanBank).

The repository comes with many useful utility scripts, which are documented in these pages.

We strongly recommend you carefully read the documentation before using any data. For instance, not understanding the [XML format](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/formosanbank-xml-format) is likely to lead to wildly inaccurate results. (This has happened.) Similarly, while we have standardized what we can, there are non-trivial differences across corpora that you should be aware of, and which are documented on each corpus page.

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
* [Yuyang Liu](https://utsus.utaipei.edu.tw/p/412-1112-9295.php?Lang=en)

And [our many contributors](background/contributors.md).
