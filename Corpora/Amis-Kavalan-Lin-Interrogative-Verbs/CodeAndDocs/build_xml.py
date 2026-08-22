#!/usr/bin/env python3
"""Build FormosanBank XML from Lin 2015 Amis/Kavalan numbered examples.

The source PDF has a usable text layer, but the article interleaves positive
examples, starred/marginal contrasts, theoretical trees, and non-target
examples. This builder keeps a page-checked static extraction list and writes
audit reports so the extraction decisions are reproducible.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from xml.dom import minidom
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
XML_ROOT = ROOT / "XML"
ACCEPTED_TSV = ROOT / "CodeAndDocs" / "extracted_examples.tsv"
EXCLUDED_TSV = ROOT / "CodeAndDocs" / "excluded_source_units.tsv"
SUMMARY_MD = ROOT / "CodeAndDocs" / "extraction_summary.md"
ALIGNMENT_OMISSIONS_TSV = ROOT / "CodeAndDocs" / "alignment_omissions.tsv"

XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)

CITATION = (
    "Lin, Dong-yi. 2015. The syntactic derivations of interrogative verbs in "
    "Amis and Kavalan. In Elizabeth Zeitoun, Stacy F. Teng, and Joy J. Wu "
    "(eds.), New Advances in Formosan Linguistics, 253-289. Asia-Pacific "
    "Linguistics."
)
BIBTEX = (
    "@incollection{lin2015AmisKavalanInterrogativeVerbs,"
    "title={The syntactic derivations of interrogative verbs in Amis and Kavalan},"
    "author={Lin, Dong-yi},"
    "booktitle={New Advances in Formosan Linguistics},"
    "editor={Zeitoun, Elizabeth and Teng, Stacy F. and Wu, Joy J.},"
    "pages={253--289},"
    "publisher={Asia-Pacific Linguistics},"
    "year={2015}}"
)
SOURCE = (
    "Basecamp card 8262349071; PDF attachment "
    "lin_2015_amis_kavalan_interrogative_verbs.pdf; ANU Open Research item "
    "249b6de8-c40b-4e66-8198-dfeedfc380bf"
)
COPYRIGHT = "CC BY 4.0 via ANU Open Research repository and Basecamp card 8262349071"

LANGUAGES = {
    "Amis": {
        "xml_lang": "ami",
        "dialect": "Xiuguluan",
        "glottocode": "nat1254",
        "source_dialect": "Central Amis, Changpin village, Taitung County",
    },
    "Kavalan": {
        "xml_lang": "ckv",
        "dialect": "Kavalan",
        "glottocode": "kava1241",
        "source_dialect": "Hsinshe Kavalan, Hsinshe village, Hualien County",
    },
}


@dataclass(frozen=True)
class Example:
    language: str
    source_id: str
    printed_page: int
    form: str
    gloss: str
    translation: str
    note: str = ""
    printed_form: str = ""
    printed_translation: str = ""

    @property
    def pdf_page(self) -> int:
        return self.printed_page - 252

    @property
    def printed(self) -> str:
        return self.printed_form or self.form

    @property
    def published_translation(self) -> str:
        return self.printed_translation or self.translation

    @property
    def language_info(self) -> dict[str, str]:
        return LANGUAGES[self.language]


@dataclass(frozen=True)
class ExcludedSourceUnit:
    source_label: str
    source_id: str
    printed_page: int
    raw_form: str
    reason: str

    @property
    def pdf_page(self) -> int:
        return self.printed_page - 252


@dataclass(frozen=True)
class FormVariant:
    id_suffix: str
    label: str
    form: str
    aligned_form: str
    gloss: str


EXAMPLES = [
    Example("Amis", "1a", 254, "mi-maan ci panay?", "AV-do.what NCM PN", "What is Panay doing?"),
    Example("Amis", "1b", 254, "na maan-en isu k-u-ra wacu?", "PST do.what-PV 2SG.ERG ABS-CN-that dog", "What did you do to that dog?"),
    Example("Kavalan", "2a", 254, "qumuni=isu tangi?", "<AV>do.what=2SG.ABS just.now", "What were you doing just now?", "infix brackets collapsed in emitted form", "q‹um›uni=isu tangi?"),
    Example("Kavalan", "2b", 254, "quni-an na wasu ya saku 'nay?", "do.what-PV ERG dog ABS cat that", "What does the dog do to that cat?", "typographic apostrophe normalized in emitted form", "quni-an na wasu ya saku ’nay?"),
    Example("Kavalan", "2c", 254, "quni-an-su m-kala ya sunis a yau?", "do.how-PV-2SG.ERG AV-find ABS child LNK that", "How do you find that child?"),
    Example("Kavalan", "3a", 254, "tanian-an-su ya kelisiw-su?", "where-PV-2SG.ERG ABS money-2SG.GEN", "Where do you put your money?"),
    Example("Kavalan", "4a", 255, "tanian qman=isu tu babuy?", "where <AV>eat=2SG.ABS OBL pig", "Where do you eat pork?", "infix brackets collapsed in emitted form", "tanian q‹m›an=isu tu babuy?"),
    Example("Kavalan", "4b", 255, "tanian tanuz-an na tuliq ya wasu?", "where chase-PV ERG bee ABS dog", "Where do the bees chase the dog?"),
    Example("Kavalan", "4c", 255, "tanuz-an na tuliq ya wasu tanian?", "chase-PV ERG bee ABS dog where", "Where do the bees chase the dog?"),
    Example("Amis", "5a", 255, "icuwa-en isu k-u payci?", "where-PV 2SG.ERG ABS-CN money", "Where do you put the money?"),
    Example("Amis", "6a", 256, "mi-sni' t-u nanum i takid.", "AV-pour OBL-CN water PREP cup", "Somebody pours water into the cup.", "typographic apostrophe normalized in emitted form", "mi-sni’ t-u nanum i takid."),
    Example("Amis", "6b", 256, "mi-nanum=ho kaku.", "AV-drink=IPFV 1SG.ABS", "I am still drinking water."),
    Example("Kavalan", "7b", 257, "quni-an-su ya sunis-ku?", "do.what-PV-2SG.ERG ABS child-1SG.GEN", "What did you do to my child?"),
    Example("Amis", "8b", 257, "ma-maan cingra?", "AV-what.happen 3SG.ABS", "What happened to him?"),
    Example("Amis", "10a", 259, "mi-nanum ci aki t-u nanum.", "AV-water NCM PN OBL-CN water", "Aki is going to drink water. Aki is drinking water.", "slash-separated English alternatives split into two sentences", printed_translation="Aki is going to drink water./Aki is drinking water."),
    Example("Amis", "10b", 259, "mi-palu ci sawmah ci mayaw-an.", "AV-beat NCM PN NCM PN-OBL", "Sawmah is going to beat Mayaw. Sawmah is beating Mayaw.", "slash-separated English alternatives split into two sentences", printed_translation="Sawmah is going to beat Mayaw./Sawmah is beating Mayaw."),
    Example("Amis", "11a", 259, "ma-adah=tu kaku.", "AV-recover=PFV 1SG.ABS", "I have recovered from illness.", "parenthetical English wording flattened", printed_translation="I have recovered (from illness)."),
    Example("Amis", "11b", 259, "ma-ruhem=tu k-u pawli.", "AV-ripe=PFV ABS-CN banana", "The banana is ripe just now.", "parenthetical English wording flattened", printed_translation="The banana is ripe (just now)."),
    Example("Amis", "14a", 260, "tuni'-en aku ku ti'ti' aca.", "soft-PV 1SG.ERG ABS meat a.little", "I will tenderise only the meat.", "source q normalized to apostrophe for Amis XML; source footnote correction applied to emitted translation", "tuniq-en aku ku ti’ti’ aca.", "I will tenderise the meat a little."),
    Example("Amis", "15a", 260, "ranam-en=ho.", "breakfast-PV=IPFV", "Eat the same thing for the breakfast again!"),
    Example("Amis", "15b", 261, "mi-nanum=ho ci panay t-u sayta.", "AV-water=IPFV NCM PN OBL-CN soda", "Panay is still drinking soda."),
    Example("Amis", "19a", 262, "ka-kuma'en-an ni ofad t-u 'epah k-u luma aku.", "KA-<UM>eat-LA ERG PN OBL-CN wine ABS-CN house 1SG.GEN", "Ofad drinks wine at my place. My place is where Ofad drinks wine.", "infix brackets collapsed and typographic apostrophe normalized in emitted form", "ka-k‹um›a’en-an ni ofad t-u ’epah k-u luma aku.", "Ofad drinks (wine) at my place. (My place is where Ofad drinks (wine).)"),
    Example("Amis", "19b", 263, "mi-cikay-an ni ofad i pitilidan k-u cudad.", "MI-run-LA ERG PN PREP school ABS-CN book", "Ofad runs to school to get the book. The book is what Ofad runs to school to get.", printed_translation="Ofad runs to school to get the book (for the book). (The book is what Ofad runs to school to get)."),
    Example("Amis", "19c", 263, "sa-ka-kuma'en ni ofad t-u futing k-u alapit.", "IA-KA-<UM>eat ERG PN OBL-CN fish ABS-CN chopsticks", "Ofad eats fish with the chopsticks. The chopsticks are what Ofad uses to eat fish.", "infix brackets collapsed and typographic apostrophe normalized in emitted form", "sa-ka-k‹um›a’en ni ofad t-u futing k-u alapit.", "Ofad eats fish with the chopsticks. (The chopsticks are what Ofad uses to eat fish.)"),
    Example("Amis", "20", 263, "ma-talaw ci lekal t-u maan?", "AV-afraid NCM PN OBL-CN what", "What is Lekal afraid of?"),
    Example("Kavalan", "21a", 264, "sabiqbiq=ti ya zanum 'nay.", "boil=PFV ABS water that", "The water has boiled.", "typographic apostrophe normalized in emitted form", "sabiqbiq=ti ya zanum ’nay."),
    Example("Kavalan", "21c", 264, "pa-sabiqbiq=ti=iku tu zanum.", "CAUS-boil=PFV=1SG.ABS OBL water", "I boiled water. I had the water boiled.", printed_translation="I boiled water. (I had the water boiled.)"),
    Example("Kavalan", "21d", 264, "sabiqbiq-an-ku ya zanum 'nay.", "boil-PV-1SG.ERG ABS water that", "I boiled the water.", "typographic apostrophe normalized in emitted form", "sabiqbiq-an-ku ya zanum ’nay."),
    Example("Kavalan", "23b", 265, "qaynep-an-ku ya qaynepan.", "sleep-PV-1SG.ERG ABS bed", "I slept in the bed."),
    Example("Kavalan", "23c", 265, "tmalumbi ta-liab-an na takan ya sunis a yau.", "<AV>hide LOC-underside-LOC GEN table ABS child LNK that", "The child hides under the table.", "infix brackets collapsed in emitted form", "t‹m›alumbi ta-liab-an na takan ya sunis a yau."),
    Example("Kavalan", "23e", 266, "talumbi-an na sunis a yau ta-liab-an na takan ya tina-na.", "hide-PV ERG child LNK that LOC-underside-LOC GEN table ABS mother-3GEN", "The child hides under the table from his mother."),
    Example("Kavalan", "24a", 266, "naquni-an-su ya sunis a yau?", "do.what-PV-2SG.ERG ABS child LNK that", "What do you do to that child?", "expanded optional na- prefix from printed form", "(na)quni-an-su ya sunis a yau?"),
    Example("Kavalan", "24b", 266, "naquni-an-su m-kala ya sunis a yau?", "do.how-PV-2SG.ERG AV-find ABS child LNK that", "How do you find that child?", "expanded optional na- prefix from printed form", "(na)quni-an-su m-kala ya sunis a yau?"),
    Example("Amis", "25b", 266, "na maan-en ni panay mi-padang kisu?", "PST do.how-PV ERG PN AV-help 2SG.ABS", "How did Panay help you?"),
    Example("Kavalan", "29a", 268, "tanuz-an na tuliq tanian ya wasu?", "chase-PV ERG bee where ABS dog", "Where do the bees chase the dog?"),
    Example("Amis", "30a", 268, "kuma'en kisu t-u hemay icuwa?", "<AV>eat 2SG.ABS OBL-CN rice where", "Where do you eat?", "infix brackets collapsed and typographic apostrophe normalized in emitted form", "k‹um›a’en kisu t-u hemay icuwa?"),
    Example("Amis", "30b", 268, "icuwa kuma'en kisu t-u hemay?", "where <AV>eat 2SG.ABS OBL-CN rice", "Where do you eat?", "infix brackets collapsed and typographic apostrophe normalized in emitted form", "icuwa k‹um›a’en kisu t-u hemay?"),
    Example("Kavalan", "37", 271, "tanian-an ni abas m-Rupu ya adam 'nay?", "where-PV ERG PN AV-shut ABS bird that", "Where does Abas shut the bird?", "typographic apostrophe normalized in emitted form", "tanian-an ni abas m-Rupu ya adam ’nay?"),
    Example("Amis", "38", 271, "icuwa-en isu mi-na'ang k-u riku'?", "where-PV 2SG.ERG AV-pack ABS-CN clothes", "Where do you pack the clothes?", "typographic apostrophes normalized in emitted form", "icuwa-en isu mi-na’ang k-u riku’?"),
    Example("Kavalan", "41a", 272, "kin-tani-an-su=pa pmukun ya sunis?", "HUM-how.many-PV-2SG.ERG=FUT <AV>beat ABS child", "How many children will you beat?", "infix brackets collapsed in emitted form", "kin-tani-an-su=pa p‹m›ukun ya sunis?"),
    Example("Kavalan", "41b", 272, "u-tani-an na wasu qmaRat ya saku?", "NHUM-how.many-PV ERG dog <AV>take ABS cat", "How many cats does the dog bite?", "infix brackets collapsed in emitted form; published gloss 'take' retained despite its semantic mismatch", "u-tani-an na wasu q‹m›aRat ya saku?"),
    Example("Amis", "42a", 273, "pina-en ni ofad k-u paysu?", "how.many-PV ERG PN ABS-CN money", "How much money does Ofad want or take?", "slash-separated English alternative flattened", printed_translation="How much money does Ofad want/take?"),
    Example("Amis", "42b", 273, "pa-pina-en isu mi-lawup k-u wawa?", "HUM-how.many-PV 2SG.ERG AV-chase ABS-CN child", "How many children will you chase?"),
    Example("Kavalan", "43", 273, "u-tani ya ni-ala-su tu kelisiw?", "NHUM-how.many ABS PFV-take-2SG.GEN OBL money", "How much money did you take?", printed_translation="How much money did you take? (Lit. The money that you took is how much?)"),
    Example("Amis", "44", 273, "pina k-u mi-ala-an ni utay a payci?", "how.many ABS-CN MI-take-LA ERG PN LNK money", "How much money did Utay take?", printed_translation="How much money did Utay take? (Lit. The money that Utay took is how much?)"),
    Example("Kavalan", "48a", 276, "tazian-an-ku ya kelisiw-ku.", "here-PV-1SG.ERG put ABS money-1SG.GEN", "I put my money here.", "optional secondary verb pizi retained from the printed form and gloss", "tazian-an-ku (pizi) ya kelisiw-ku."),
    Example("Kavalan", "48b", 276, "tawian-an-ku ya kelisiw-ku.", "there-PV-1SG.ERG put ABS money-1SG.GEN", "I put my money there.", "optional secondary verb pizi retained from the printed form and gloss", "tawian-an-ku (pizi) ya kelisiw-ku."),
    Example("Amis", "49a", 276, "itini-en ni panay k-u payci.", "here-PV ERG PN put ABS-CN money", "Panay put the money here.", "optional secondary verb pateli retained from the printed form and gloss", "itini-en ni panay (pateli) k-u payci."),
    Example("Amis", "49b", 276, "itiraw-en ni panay k-u payci.", "there-PV ERG PN put ABS-CN money", "Panay put the money there.", "optional secondary verb pateli retained from the printed form and gloss", "itiraw-en ni panay (pateli) k-u payci."),
    Example("Kavalan", "52a", 277, "nayau-an-ku.", "that.way-PV-1SG.ERG", "I do it in that way."),
    Example("Kavalan", "52b", 277, "nayau-an-na ya sunis-na.", "that.way-PV-3ERG ABS child-3SG.GEN", "He treats his child in that way."),
    Example("Kavalan", "52c", 277, "paqanas-an-ku tmayta ya sudad.", "slow-PV-1SG.ERG <AV>see ABS book", "I read the book slowly.", "infix brackets collapsed in emitted form", "paqanas-an-ku t‹m›ayta ya sudad."),
    Example("Amis", "53", 277, "ha'en-en k-u kamay.", "this.way-PV ABS-CN hand", "Make your hand like this!", "typographic apostrophe normalized in emitted form", "ha’en-en k-u kamay."),
    Example("Kavalan", "54a", 278, "qumni tayta-an-su ya ti-buya?", "when see-PV-2SG.ERG ABS NCM-PN", "When do you see Buya?"),
    Example("Kavalan", "54c", 279, "mana ala-an-su ya kelisiw-ku?", "why take-PV-2SG.ERG ABS money-1SG.GEN", "Why do you take my money?"),
    Example("Amis", "55a", 279, "ihakuwa ma-alaw isu ci panay?", "when PV-see 2SG.ERG NCM PN", "When do you see Panay?"),
    Example("Amis", "55c", 279, "naw ma-ulah ci panay ci lekal-an?", "why AV-like NCM PN NCM PN-OBL", "Why does Panay like Lekal?"),
    Example("Kavalan", "56a", 280, "sudad zau", "book this", "this book"),
    Example("Kavalan", "56b", 280, "zau=ay sudad", "this=REL book", "this book"),
    Example("Kavalan", "56c", 280, "sudad zaku", "book 1SG.POSS", "my book"),
    Example("Kavalan", "56d", 280, "zaku=ay sudad", "1SG.POSS=REL book", "my book"),
    Example("Amis", "57b", 280, "cmikay k-u-ni a wawa.", "<AV>run ABS-CN-this LNK child", "This child is running.", "infix brackets collapsed and optional linker expanded in emitted form", "c‹m›ikay k-u-ni (a) wawa."),
    Example("Amis", "57c", 280, "wacu nu maku", "dog GEN 1SG.POSS", "my dog"),
    Example("Amis", "57d", 280, "nu maku a wacu", "GEN 1SG.POSS LNK dog", "my dog", "expanded optional genitive marker from printed form", "(nu) maku a wacu"),
    Example("Kavalan", "59a", 281, "mayni=ay sunis ya tayta-an ni imuy?", "which=REL child ABS see-PV ERG PN", "Which child does Imuy see?", "removed source square brackets from emitted form", "[mayni=ay sunis] ya tayta-an ni imuy?", "Which child does Imuy see? (Lit. ‘The person that Imuy sees is which child?’)"),
    Example("Kavalan", "59b", 281, "zanitiana=ay kelisiw ya ala-an=ay ni utay?", "whose=REL money ABS take-PV=REL ERG PN", "Whose money does Utay take?", "removed source square brackets from emitted form", "[zanitiana=ay kelisiw] ya ala-an=ay ni utay?", "Whose money does Utay take? (Lit. ‘The stuff that Utay takes is whose money?’)"),
    Example("Amis", "60a", 281, "icuwaay a wacu k-u ka-ulah-an isu?", "which LNK dog ABS-CN KA-like-LA 2SG.ERG", "Which dog do you like?", "removed source square brackets from emitted form", "[icuwaay a wacu] k-u ka-ulah-an isu?", "Which dog do you like? (Lit. ‘What you like is which dog?’)"),
    Example("Amis", "60b", 281, "nima a wacu k-u mi-kalat-ay t-u pusi aku?", "whose LNK dog ABS-CN AV-bite-FAC OBL-CN cat 1SG.GEN", "Whose dog bites my cat?", "removed source square brackets from emitted form", "[nima a wacu] k-u mi-kalat-ay t-u pusi aku?", "Whose dog bites my cat? (Lit. The thing that bites my cat is whose dog?)"),
    Example("Kavalan", "3b", 255, "* tanian-an-su q‹m›an tu/ya babuy?", "where-PV-2SG.ERG <AV>eat OBL/ABS pig", "Where do you eat pork?", "Source marks this example ungrammatical and labels the translation as intended."),
    Example("Kavalan", "7a", 257, "q‹um›uni=isu tangi?", "<AV>do.what=2SG.ABS just.now", "What were you doing just now?", "Independently printed repetition of example 2a."),
    Example("Amis", "8a", 257, "mi-maan ci panay?", "AV-do.what NCM PN", "What is Panay doing?", "Independently printed repetition of example 1a."),
    Example("Amis", "8c", 257, "na maan-en isu k-u-ra wacu?", "PST do.what-PV 2SG.ERG ABS-CN-that dog", "What did you do to that dog?", "Independently printed repetition of example 1b."),
    Example("Amis", "14b", 260, "* tuniq-en nu kuwaq ku ti’ti’ aca.", "soft-PV ERG papaya ABS meat a.little", "", "Source marks this example ungrammatical and supplies no translation."),
    Example("Amis", "18a", 262, "* mi-nanum-en", "", "", "Source presents this as an ungrammatical word form without gloss or translation."),
    Example("Amis", "18b", 262, "* ma-ruhem-en", "", "", "Source presents this as an ungrammatical word form without gloss or translation."),
    Example("Kavalan", "21b", 264, "* sabiqbiq=ti=iku tu zanum.", "boil=PFV=1SG.ABS OBL water", "", "Source marks this example ungrammatical and supplies no translation."),
    Example("Kavalan", "23a", 265, "? maynep=iku tu qaynepan.", "sleep.AV=1SG.ABS OBL bed", "I am sleeping in a bed.", "Source marks this example marginal and labels the translation as intended."),
    Example("Kavalan", "23d", 265, "? t‹m›alumbi ta-liab-an na takan ya sunis a yau tu tina-na.", "<AV>hide LOC-underside-LOC GEN table ABS child LNK that OBL mother-3GEN", "The child hides under the table from his mother.", "Source marks this example marginal and labels the translation as intended."),
    Example("Amis", "25a", 266, "na maan-en isu k-u-ra wacu?", "PST do.what-PV 2SG.ERG ABS-CN-that dog", "What did you do to that dog?", "Independently printed repetition of example 1b."),
    Example("Kavalan", "27a", 267, "tanian-an-su ya kelisiw-su?", "where-PV-2SG.ERG ABS money-2SG.GEN", "Where do you put your money?", "Independently printed repetition of example 3a."),
    Example("Kavalan", "27b", 267, "* tanian-an-su q‹m›an tu/ya babuy?", "where-PV-2SG.ERG <AV>eat OBL/ABS pig", "Where do you eat pork?", "Exact repetition of example 3b; the source does not label it as repeated."),
    Example("Amis", "28a", 268, "icuwa-en isu k-u payci?", "where-PV 2SG.ERG ABS-CN money", "Where do you put the money?", "Independently printed repetition of example 5a."),
    Example("Amis", "28b", 268, "* icuwa-en isu mi-saosi k-u cudad?", "where-PV 2SG.ERG AV-read ABS-CN book", "Where do you read the book?", "Source marks this example ungrammatical and labels the translation as intended."),
    Example("Kavalan", "29b", 268, "tanian tanuz-an na tuliq ya wasu?", "where chase-PV ERG bee ABS dog", "Where do the bees chase the dog?", "Independently printed repetition of example 4b."),
    Example("Kavalan", "39", 272, "* tanian=isu tu kelisiw-su?", "where=2SG.ABS OBL money-2SG.GEN", "Where do you put your money?", "Source marks this example ungrammatical and labels the translation as intended."),
    Example("Amis", "40", 272, "* icuwa kisu t-u payci?", "where 2SG.ABS OBL-CN money", "Where do you put money?", "Source marks this example ungrammatical and labels the translation as intended."),
    Example("Kavalan", "46", 274, "* u-tani=isu tu kelisiw?", "NHUM-how.many=2SG.ABS OBL money", "How much money do you want/take?", "Source marks this example ungrammatical and labels the translation as intended."),
    Example("Amis", "47", 274, "* pina ci ofad t-u payci?", "how.many NCM PN OBL-CN money", "How much money does Ofad want/take?", "Source marks this example ungrammatical and labels the translation as intended."),
    Example("Kavalan", "50", 276, "* tazian-an-ku m-Rasa tu/ya sudad.", "here-PV-1SG.ERG AV-buy OBL/ABS book", "I buy a/the book here.", "Source marks this example ungrammatical and labels the translation as intended."),
    Example("Amis", "51", 277, "* itiraw-en ni utay mi-pacu’ t-u/k-u fafuy.", "there-PV ERG PN AV-kill OBL-CN/ABS-CN pig", "Utay kills pigs there.", "Source marks this example ungrammatical and labels the translation as intended."),
    Example("Kavalan", "54b", 278, "* qumni-an-su t‹m›ayta ti-buya-an?", "when-PV-2SG.ERG <AV>see NCM-PN-LOC", "", "Source marks this example ungrammatical and supplies no translation."),
    Example("Kavalan", "54d", 279, "* mana-an-su m-ala ya kelisiw-ku?", "why-PV-2SG.ERG AV-take ABS money-1SG.GEN", "", "Source marks this example ungrammatical and supplies no translation."),
    Example("Amis", "55b", 279, "* ihakuwa-en ma-alaw isu ci panay?", "when-PV PV-see 2SG.ERG NCM PN", "", "Source marks this example ungrammatical and supplies no translation."),
    Example("Amis", "55d", 279, "* naw-en ma-ulah ci panay ci lekal-an?", "why-PV AV-like NCM PN NCM PN-OBL", "", "Source marks this example ungrammatical and supplies no translation."),
    Example("Amis", "57a", 280, "* c‹m›ikay wawa k-u-ni.", "<AV>run child ABS-CN-this", "", "Source marks this example ungrammatical and supplies no translation."),
]


EXCLUDED = [
    ExcludedSourceUnit("Theory", "9", 258, "Feature specifications of v", "theoretical feature list, not a Formosan sentence"),
    ExcludedSourceUnit("Theory", "12", 259, "Partial derivation for (8a)", "syntactic tree/analysis diagram, not a sentence"),
    ExcludedSourceUnit("Theory", "13", 260, "Partial derivation for (8b)", "syntactic tree/analysis diagram, not a sentence"),
    ExcludedSourceUnit("Theory", "16", 261, "The verbal structure of -en", "syntactic tree/analysis diagram, not a sentence"),
    ExcludedSourceUnit("Theory", "17", 262, "Partial derivation for (8c)", "syntactic tree/analysis diagram, not a sentence"),
    ExcludedSourceUnit("Theory", "22", 265, "The structure of Kavalan -an", "syntactic tree/analysis diagram, not a sentence"),
    ExcludedSourceUnit("Theory", "26", 267, "The structure of the do-how question", "syntactic tree/analysis diagram, not a sentence"),
    ExcludedSourceUnit("Theory", "31", 268, "Head Movement Constraint", "theoretical definition, not a sentence"),
    ExcludedSourceUnit("Theory", "32", 269, "Empty Category Principle", "theoretical definition, not a sentence"),
    ExcludedSourceUnit("Theory", "33", 269, "Head movement structure", "syntactic tree/analysis diagram, not a sentence"),
    ExcludedSourceUnit("Theory", "34", 269, "Adjunction structure for tanian", "syntactic tree/analysis diagram, not a sentence"),
    ExcludedSourceUnit("Theory", "35", 270, "Transparence Condition", "theoretical definition, not a sentence"),
    ExcludedSourceUnit("Theory", "36", 271, "Partial derivation for (27a)", "syntactic tree/analysis diagram, not a sentence"),
    ExcludedSourceUnit("Theory", "45", 274, "Partial derivation for (42a)", "syntactic tree/analysis diagram, not a sentence"),
    ExcludedSourceUnit("Theory", "58", 281, "DP-internal predicate inversion", "syntactic tree/analysis diagram, not a sentence"),
    ExcludedSourceUnit("Theory", "61", 282, "Structure of which and whose in Kavalan and Amis", "syntactic tree/analysis diagram, not a sentence"),
    ExcludedSourceUnit("Tzotzil", "62", 282, "Tzotzil examples from Aissen 1996", "non-Formosan comparison examples"),
    ExcludedSourceUnit("English", "63", 284, "Harley and Noyer English examples", "non-Formosan comparison examples"),
]


SOURCE_TRANSLATION_READINGS = {
    ("Amis", "10a"): (
        "Aki is going to drink water.",
        "Aki is drinking water.",
    ),
    ("Amis", "10b"): (
        "Sawmah is going to beat Mayaw.",
        "Sawmah is beating Mayaw.",
    ),
    ("Amis", "14a"): (
        "I will tenderise the meat a little.",
        "I will tenderise only the meat.",
    ),
    ("Amis", "19a"): (
        "Ofad drinks (wine) at my place.",
        "My place is where Ofad drinks (wine).",
    ),
    ("Amis", "19b"): (
        "Ofad runs to school to get the book.",
        "Ofad runs to school for the book.",
        "The book is what Ofad runs to school to get.",
    ),
    ("Amis", "19c"): (
        "Ofad eats fish with the chopsticks.",
        "The chopsticks are what Ofad uses to eat fish.",
    ),
    ("Kavalan", "21c"): (
        "I boiled water.",
        "I had the water boiled.",
    ),
    ("Amis", "42a"): (
        "How much money does Ofad want?",
        "How much money does Ofad take?",
    ),
    ("Kavalan", "43"): (
        "How much money did you take?",
        "The money that you took is how much?",
    ),
    ("Amis", "44"): (
        "How much money did Utay take?",
        "The money that Utay took is how much?",
    ),
    ("Kavalan", "59a"): (
        "Which child does Imuy see?",
        "The person that Imuy sees is which child?",
    ),
    ("Kavalan", "59b"): (
        "Whose money does Utay take?",
        "The stuff that Utay takes is whose money?",
    ),
    ("Amis", "60a"): (
        "Which dog do you like?",
        "What you like is which dog?",
    ),
    ("Amis", "60b"): (
        "Whose dog bites my cat?",
        "The thing that bites my cat is whose dog?",
    ),
}

REPEAT_TARGETS = {
    ("Kavalan", "7a"): "2a",
    ("Amis", "8a"): "1a",
    ("Amis", "8c"): "1b",
    ("Amis", "25a"): "1b",
    ("Kavalan", "27a"): "3a",
    ("Kavalan", "27b"): "3b",
    ("Amis", "28a"): "5a",
    ("Kavalan", "29b"): "4b",
}

SOURCE_NOTES = {
    ("Amis", "10a"): "Source separates two translation readings with a slash.",
    ("Amis", "10b"): "Source separates two translation readings with a slash.",
    ("Amis", "14a"): "Footnote 6 corrects the body translation; both readings are retained.",
    ("Amis", "49a"): "Optional secondary verb pateli is expanded under POL-026.",
    ("Amis", "49b"): "Optional secondary verb pateli is expanded under POL-026.",
    ("Kavalan", "41b"): "Published gloss '<AV>take' is retained despite the free translation 'bite'.",
    ("Kavalan", "48a"): "Optional secondary verb pizi is expanded under POL-026.",
    ("Kavalan", "48b"): "Optional secondary verb pizi is expanded under POL-026.",
}


def source_note(example: Example) -> str:
    if example.note.startswith(("Source ", "Independently ", "Exact repetition")):
        return example.note
    return SOURCE_NOTES.get((example.language, example.source_id), "")


def exclusion_reason(example: Example) -> str:
    """Return the current intake-policy reason for excluding a source example."""
    if example.printed.startswith("* "):
        return "source-marked ungrammatical example excluded under POL-016"
    if example.printed.startswith("? "):
        return "source-marked marginal example excluded under POL-016"
    return ""


def admitted_examples() -> list[Example]:
    """Return source examples eligible for generated corpus XML."""
    return [example for example in EXAMPLES if not exclusion_reason(example)]


def admitted_repeat_count() -> int:
    """Return admitted occurrences represented by an earlier S record."""
    return sum(
        (example.language, example.source_id) in REPEAT_TARGETS
        for example in admitted_examples()
    )


def excluded_units() -> list[ExcludedSourceUnit]:
    """Return every non-corpus source unit, including marked Formosan examples."""
    marked = [
        ExcludedSourceUnit(
            example.language,
            example.source_id,
            example.printed_page,
            example.printed,
            exclusion_reason(example),
        )
        for example in EXAMPLES
        if exclusion_reason(example)
    ]
    return [*EXCLUDED, *marked]


def xml_form(example: Example) -> str:
    """Return the included normalized variant used by the base XML record."""
    return form_variants(example)[0].form


def source_order(item: Example | ExcludedSourceUnit) -> tuple[int, str, str]:
    match = re.fullmatch(r"(\d+)([a-z]?)", item.source_id)
    if match is None:
        raise ValueError(f"Unexpected source ID: {item.source_id}")
    return int(match.group(1)), match.group(2), getattr(item, "language", getattr(item, "source_label", ""))


def prettify(root: ET.Element) -> str:
    xml = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(xml)
    lines = parsed.toprettyxml(indent="    ").splitlines()
    return "\n".join(line for line in lines if line.strip()) + "\n"


WORD_EDGE_CHARS = '*,.;:!?…[]{}"“”‘’'


def lexical_tokens(text: str) -> list[str]:
    """Return source words without sentence or constituent-edge punctuation."""
    tokens: list[str] = []
    for raw_token in text.split():
        token = raw_token.strip(WORD_EDGE_CHARS)
        if token:
            tokens.append(
                token.replace("(", "")
                .replace(")", "")
                .replace("‹", "<")
                .replace("›", ">")
            )
    return tokens


def normalize_source_form(text: str, *, preserve_infix: bool = False) -> str:
    """Normalize source notation without changing source spelling."""
    normalized = (
        text.removeprefix("* ")
        .removeprefix("? ")
        .replace("‘", "'")
        .replace("’", "'")
        .replace("[", "")
        .replace("]", "")
    )
    if preserve_infix:
        normalized = normalized.replace("‹", "<").replace("›", ">")
    else:
        normalized = normalized.replace("‹", "").replace("›", "")
    return re.sub(r"\s+", " ", normalized).strip()


def form_variants(example: Example) -> tuple[FormVariant, ...]:
    """Expand one optional source constituent into aligned S variants."""
    source = example.printed.removeprefix("* ").removeprefix("? ")
    optional = re.search(r"\(([^()]*)\)", source)
    if optional is None:
        return (
            FormVariant(
                "",
                "source form",
                normalize_source_form(source),
                normalize_source_form(source, preserve_infix=True),
                example.gloss,
            ),
        )

    included_source = source[: optional.start()] + optional.group(1) + source[optional.end() :]
    omitted_source = source[: optional.start()] + source[optional.end() :]
    included = normalize_source_form(included_source)
    omitted = normalize_source_form(omitted_source)
    included_aligned = normalize_source_form(included_source, preserve_infix=True)
    omitted_aligned = normalize_source_form(omitted_source, preserve_infix=True)
    included_words = lexical_tokens(included_aligned)
    omitted_words = lexical_tokens(omitted_aligned)
    included_glosses = lexical_tokens(example.gloss)
    omitted_glosses = included_glosses.copy()

    if len(included_words) == len(omitted_words) + 1:
        difference = next(
            index
            for index, word in enumerate(included_words)
            if index >= len(omitted_words) or word != omitted_words[index]
        )
        if len(included_glosses) != len(included_words):
            raise ValueError(
                f"Cannot align optional gloss for {example.language} {example.source_id}"
            )
        omitted_glosses.pop(difference)
    elif len(included_words) != len(omitted_words):
        raise ValueError(
            f"Unsupported optional form shape for {example.language} {example.source_id}"
        )

    return (
        FormVariant(
            "",
            "optional material included",
            included,
            included_aligned,
            example.gloss,
        ),
        FormVariant(
            "_OPT0",
            "optional material omitted",
            omitted,
            omitted_aligned,
            " ".join(omitted_glosses),
        ),
    )


def translation_readings(example: Example) -> tuple[str, ...]:
    readings = SOURCE_TRANSLATION_READINGS.get((example.language, example.source_id))
    if readings is not None:
        return readings
    return (example.published_translation,) if example.published_translation else ()


def alignment_words(variant: FormVariant) -> tuple[list[tuple[str, str]], str]:
    """Return source-supported word/gloss pairs or an explicit omission reason."""
    if not variant.gloss:
        return [], "source supplies no gloss"
    if "/" in variant.aligned_form or "/" in variant.gloss:
        return [], "source presents unresolved slash alternatives"
    form_words = lexical_tokens(variant.aligned_form)
    gloss_words = lexical_tokens(variant.gloss)
    if len(form_words) != len(gloss_words):
        return [], f"word/gloss token count differs ({len(form_words)} != {len(gloss_words)})"
    return list(zip(form_words, gloss_words, strict=True)), ""


def morpheme_parts(token: str, *, mark_infix: bool) -> list[str]:
    parts: list[str] = []
    for component in re.split(r"[-=]", token):
        if not component:
            continue
        infixes = re.findall(r"<([^<>]+)>", component)
        base = re.sub(r"<[^<>]+>", "-" if mark_infix else "", component)
        if base:
            parts.append(base)
        parts.extend(f"-{infix}-" if mark_infix else infix for infix in infixes)
    return parts


def marker_skeleton(token: str) -> str:
    return "".join(char for char in token if char in "-=<>")


def aligned_morphemes(form_token: str, gloss_token: str) -> tuple[list[str], list[str]]:
    """Align only segmentation that is explicit and one-to-one in the source."""
    if "/" in form_token or "/" in gloss_token:
        return [], []
    if marker_skeleton(form_token) != marker_skeleton(gloss_token):
        return [], []

    form_components = form_token.split("=")
    gloss_components = gloss_token.split("=")
    if len(form_components) != len(gloss_components):
        return [], []

    form_parts_by_component = [
        morpheme_parts(component, mark_infix=True) for component in form_components
    ]
    gloss_parts_by_component = [
        morpheme_parts(component, mark_infix=False) for component in gloss_components
    ]
    if any(
        len(form_parts) != len(gloss_parts)
        for form_parts, gloss_parts in zip(
            form_parts_by_component, gloss_parts_by_component, strict=True
        )
    ):
        return [], []

    for component_index in range(1, len(form_parts_by_component)):
        form_parts_by_component[component_index][0] = (
            "=" + form_parts_by_component[component_index][0]
        )

    form_parts = [part for component in form_parts_by_component for part in component]
    gloss_parts = [part for component in gloss_parts_by_component for part in component]
    return form_parts, gloss_parts


def add_word_tiers(sentence: ET.Element, variant: FormVariant) -> str:
    """Add every safe printed W/M alignment and return an omission reason, if any."""
    word_pairs, reason = alignment_words(variant)
    if reason:
        return reason

    analyses = [
        aligned_morphemes(form_word, gloss_word)
        for form_word, gloss_word in word_pairs
    ]
    sentence_is_parsed = any(len(forms) >= 2 for forms, _ in analyses)

    for word_index, ((form_word, gloss_word), (form_morphemes, gloss_morphemes)) in enumerate(
        zip(word_pairs, analyses, strict=True), start=1
    ):
        word = ET.SubElement(
            sentence,
            "W",
            {"id": f"{sentence.attrib['id']}_W{word_index:02d}"},
        )
        ET.SubElement(word, "FORM", {"kindOf": "original"}).text = form_word
        ET.SubElement(
            word,
            "TRANSL",
            {"kindOf": "original", f"{{{XML_NS}}}lang": "eng"},
        ).text = gloss_word

        if sentence_is_parsed and len(form_morphemes) < 2:
            form_morphemes = [form_word]
            gloss_morphemes = [gloss_word]
        if not sentence_is_parsed or len(form_morphemes) != len(gloss_morphemes):
            continue
        for morph_index, (form_morph, gloss_morph) in enumerate(
            zip(form_morphemes, gloss_morphemes, strict=True), start=1
        ):
            morph = ET.SubElement(
                word,
                "M",
                {"id": f"{word.attrib['id']}_M{morph_index:02d}"},
            )
            ET.SubElement(morph, "FORM", {"kindOf": "original"}).text = form_morph
            ET.SubElement(
                morph,
                "TRANSL",
                {"kindOf": "original", f"{{{XML_NS}}}lang": "eng"},
            ).text = gloss_morph
    return ""


def make_text(language: str, examples: list[Example]) -> ET.Element:
    info = LANGUAGES[language]
    root = ET.Element(
        "TEXT",
        {
            "id": f"lin_2015_{language.lower()}_interrogative_verbs",
            f"{{{XML_NS}}}lang": info["xml_lang"],
            "dialect": info["dialect"],
            "glottocode": info["glottocode"],
            "source": (
                f"{SOURCE}; source dialect note: {info['source_dialect']}; "
                "sentence examples extracted from numbered examples"
            ),
            "copyright": COPYRIGHT,
            "citation": CITATION,
            "BibTeX_citation": BIBTEX,
        },
    )
    canonical = [
        example
        for example in examples
        if (example.language, example.source_id) not in REPEAT_TARGETS
    ]
    for index, example in enumerate(sorted(canonical, key=source_order), start=1):
        occurrences = [
            item
            for item in examples
            if item.source_id == example.source_id
            or REPEAT_TARGETS.get((item.language, item.source_id)) == example.source_id
        ]
        occurrence_note = ", ".join(
            f"{item.source_id} (printed p. {item.printed_page}; PDF page {item.pdf_page})"
            for item in sorted(occurrences, key=source_order)
        )
        label = "example" if len(occurrences) == 1 else "source occurrences"
        note = f"{label} {occurrence_note}"
        if len(occurrences) > 1:
            note = f"{note}; identical printed occurrences represented by one S"
        if source_note(example):
            note = f"{note}; {source_note(example)}"
        variants = form_variants(example)
        for variant in variants:
            variant_note = note
            if len(variants) > 1:
                variant_note = f"{note}; {variant.label} under POL-026"
            sentence = ET.SubElement(
                root,
                "S",
                {
                    "id": f"S_{language.lower()}_{index:03d}{variant.id_suffix}",
                    "source": variant_note,
                },
            )
            ET.SubElement(sentence, "FORM", {"kindOf": "original"}).text = variant.form
            for reading_index, reading in enumerate(translation_readings(example)):
                attributes = {f"{{{XML_NS}}}lang": "eng"}
                if reading_index:
                    attributes["ver"] = "alt"
                ET.SubElement(sentence, "TRANSL", attributes).text = reading
            add_word_tiers(sentence, variant)
    return root


def write_xml() -> None:
    by_language: dict[str, list[Example]] = {}
    for example in admitted_examples():
        by_language.setdefault(example.language, []).append(example)

    for language, examples in sorted(by_language.items()):
        language_dir = XML_ROOT / language
        language_dir.mkdir(parents=True, exist_ok=True)
        out_path = language_dir / f"lin_2015_{language.lower()}_interrogative_verbs.xml"
        out_path.write_text(prettify(make_text(language, examples)), encoding="utf-8")


def write_tsvs() -> None:
    ACCEPTED_TSV.parent.mkdir(parents=True, exist_ok=True)
    with ACCEPTED_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "language",
                "canonical_dialect",
                "glottocode",
                "source_dialect_note",
                "source_id",
                "printed_page",
                "admission_status",
                "exclusion_reason",
                "source_form",
                "xml_form",
                "xml_record_source_id",
                "gloss",
                "source_note",
                "source_translation_eng",
                "alternate_translation_eng",
                "translation_readings_eng_json",
                "xml_variants_json",
                "pdf_page",
            ],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for example in sorted(EXAMPLES, key=source_order):
            info = example.language_info
            writer.writerow(
                {
                    "language": example.language,
                    "canonical_dialect": info["dialect"],
                    "glottocode": info["glottocode"],
                    "source_dialect_note": info["source_dialect"],
                    "source_id": example.source_id,
                    "printed_page": example.printed_page,
                    "admission_status": "excluded" if exclusion_reason(example) else "admitted",
                    "exclusion_reason": exclusion_reason(example),
                    "source_form": example.printed,
                    "xml_form": xml_form(example),
                    "xml_record_source_id": (
                        ""
                        if exclusion_reason(example)
                        else REPEAT_TARGETS.get((example.language, example.source_id), example.source_id)
                    ),
                    "gloss": example.gloss,
                    "source_note": source_note(example),
                    "source_translation_eng": example.published_translation,
                    "alternate_translation_eng": (
                        translation_readings(example)[1]
                        if len(translation_readings(example)) > 1
                        else ""
                    ),
                    "translation_readings_eng_json": json.dumps(
                        translation_readings(example), ensure_ascii=False
                    ),
                    "xml_variants_json": json.dumps(
                        [
                            {
                                "id_suffix": variant.id_suffix,
                                "label": variant.label,
                                "form": variant.form,
                                "aligned_form": variant.aligned_form,
                                "gloss": variant.gloss,
                            }
                            for variant in form_variants(example)
                        ],
                        ensure_ascii=False,
                    ),
                    "pdf_page": example.pdf_page,
                }
            )

    with EXCLUDED_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_label", "source_id", "printed_page", "pdf_page", "raw_form", "reason"],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for rejected in sorted(excluded_units(), key=source_order):
            writer.writerow(
                {
                    "source_label": rejected.source_label,
                    "source_id": rejected.source_id,
                    "printed_page": rejected.printed_page,
                    "pdf_page": rejected.pdf_page,
                    "raw_form": rejected.raw_form,
                    "reason": rejected.reason,
                }
            )

    with ALIGNMENT_OMISSIONS_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "language",
                "source_id",
                "printed_page",
                "pdf_page",
                "tier",
                "word_index",
                "form",
                "gloss",
                "reason",
            ],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        canonical = [
            example
            for example in admitted_examples()
            if (example.language, example.source_id) not in REPEAT_TARGETS
        ]
        for example in sorted(canonical, key=source_order):
            variant_reasons = [
                (variant, alignment_words(variant)[1])
                for variant in form_variants(example)
            ]
            for variant, reason in variant_reasons:
                if not reason:
                    continue
                writer.writerow(
                    {
                        "language": example.language,
                        "source_id": example.source_id,
                        "printed_page": example.printed_page,
                        "pdf_page": example.pdf_page,
                        "tier": f"W/M{variant.id_suffix}",
                        "word_index": "",
                        "form": variant.form,
                        "gloss": variant.gloss,
                        "reason": reason,
                    }
                )
                continue


def write_summary() -> None:
    by_language: dict[str, int] = {}
    for example in EXAMPLES:
        by_language[example.language] = by_language.get(example.language, 0) + 1

    lines = [
        "# Extraction Summary",
        "",
        f"Formosan source occurrences: {len(EXAMPLES)}",
        f"Admitted Formosan source occurrences: {len(admitted_examples())}",
        f"Formosan XML records: {sum(len(form_variants(example)) for example in admitted_examples() if (example.language, example.source_id) not in REPEAT_TARGETS)}",
        f"Excluded source units: {len(excluded_units())}",
        "",
        "Source occurrences by language:",
    ]
    for language in sorted(by_language):
        info = LANGUAGES[language]
        lines.append(
            f"- {language} -> {info['dialect']} (`{info['glottocode']}`): "
            f"{by_language[language]}"
        )
    lines.extend(
        [
            "",
            "The source footnote identifies the analysed dialects as Hsinshe Kavalan and Central Amis. FormosanBank currently has a single canonical Kavalan dialect value and maps Central Amis to `Xiuguluan`.",
            "All 95 independently printed Amis and Kavalan occurrences are accounted for. Under POL-016, the 18 source-starred and two source-marginal occurrences are excluded from XML but retained in the source and exclusion ledgers. Seven admitted repeat occurrences map to their matching source records. POL-026 expands eight optional source records into included and omitted S variants, leaving 76 XML records. The other 18 excluded units are theory diagrams or definitions and non-Formosan comparison material.",
            "Every one of the source PDF's 38 pages was visually reviewed; `CodeAndDocs/manual_source_review.tsv` records corpus and excluded IDs page by page.",
            "Thirty difficult records were checked directly against rendered source pages; `CodeAndDocs/direct_source_checks.tsv` records the focus and result of each comparison.",
            "The source ledger preserves printed infix brackets, optional parentheses, constituent brackets, segmentation, acceptability markers, and typographic apostrophes. XML original S FORM normalizes typographic apostrophes, removes analytical constituent and infix brackets, and expands optional material without changing source spelling. W retains source segmentation with ASCII infix brackets under POL-014.",
            "Madeline Boese's 2026-08-13 review routes Lin's source notation to the Ortho113 family. The article's Amis spelling distinguishes source q (pharyngeal stop) from apostrophe (glottal stop) and uses both u and o; the local LinAmis source profile records those values, and its validated Xiuguluan conversion targets Ortho113 without information loss. Kavalan uses Ortho113 directly. Standard FORM and original/standard PHON are generated only by the current shared tools under POL-002 and POL-003.",
            "Source slash readings and analytic or literal paraphrases are emitted in the same S as primary and `ver=\"alt\"` English translations under POL-024 and POL-025. The 14a body translation and its footnote correction are both retained.",
            "Kavalan example 41b retains the article's published gloss `<AV>take` despite its mismatch with the free translation `bite`.",
            "Published interlinear gloss lines generate W tiers with source glosses marked `kindOf=\"original\"`. M tiers preserve explicit one-to-one segmentation, including infix roots, and parsed sentences give every monomorphemic W one aligned M under POL-023. Every admitted XML record has a source-safe W alignment.",
            "",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    write_xml()
    write_tsvs()
    write_summary()
    print(
        f"Accounted for {len(EXAMPLES)} Formosan source occurrences and wrote "
        f"{sum(len(form_variants(example)) for example in admitted_examples() if (example.language, example.source_id) not in REPEAT_TARGETS)} XML records with "
        f"{len(excluded_units())} excluded source units."
    )


if __name__ == "__main__":
    main()
