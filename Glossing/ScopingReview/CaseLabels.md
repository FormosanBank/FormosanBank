# Case labels across sources — audit

Question (maintainer, 2026-11-11): are differing case labels across sources
(NOM vs ABS, GEN vs ERG, 受格 vs OBL) true translations of one marker system,
or distinct sets? Method: per (source, language), the morpheme forms carrying
each case label with frequencies; weighted cross-source overlap of the
normalized form distributions.

## Verdict

In every language with multiple glossed sources the labels are relabels of a
single marker system. Caveats: (1) segmentation depth — Wu-school Amis
segments k-u where NTU glosses whole ku, deflating overlap artificially;
(2) the ergative analysis (Lin 2015) relabels: ABS = the nominative marker
set, ERG = the genitive marker set. Correction adopted into the tables:
Kavalan-Chang's 受格 marks tu — the same morpheme as NTU's 斜格/OBL — so the
proposed 受格→ACC must become 受格→OBL-equivalent.

## Key overlaps (weighted; 1.00 = identical marker distribution)

### Kavalan

- NTU `GEN` (n=2148): na:68% ku:14% ta:9% su:3% ni:2%
- NTU `屬格` (n=2145): na:67% ku:14% ta:9% su:3% ni:2%
- NTU `NOM` (n=1045): ya:28% iku:16% a:16% ita:12% imi:9%
- NTU `主格` (n=1042): ya:28% iku:17% a:16% ita:12% imi:9%
- NTU `處格` (n=854): ta:55% an:41% sa:2% timaikuan:0% tamaikuan:0%
- NTU `OBL` (n=607): tu:96% timaisu:1% timaita:1% timaimu:0% timaiku:0%
- NTU `斜格` (n=606): tu:96% timaisu:1% timaita:1% timaimu:0% timaiku:0%
- Kavalan-Chang-Reference-Grammar `受格` (n=125): tu:100%
- NTU `所有格` (n=123): zana:75% zata:13% zaku:6% zanumi:2% zani:2%
- Kavalan-Chang-Reference-Grammar `主格` (n=104): ya:72% a:28%
- Kavalan-Chang-Reference-Grammar `處所格` (n=47): an:47% ta:47% ta-an:6%
- Kavalan-Chang-Reference-Grammar `屬格` (n=43): na:63% ni:37%
- Amis-Kavalan-Lin-Interrogative-Verbs `ABS` (n=31): ya:90% isu:6% iku:3%
- Amis-Kavalan-Lin-Interrogative-Verbs `ERG` (n=25): su:32% ku:32% na:24% ni:12%
- Amis-Kavalan-Lin-Interrogative-Verbs `GEN` (n=11): ku:55% na:27% su:18%
- Amis-Kavalan-Lin-Interrogative-Verbs `OBL` (n=3): tu:100%

  - 1.00  Kavalan-Chang-Reference-Grammar:受格 ~ Amis-Kavalan-Lin-Interrogative-Verbs:OBL
  - 0.96  NTU:斜格 ~ Kavalan-Chang-Reference-Grammar:受格
  - 0.96  NTU:斜格 ~ Amis-Kavalan-Lin-Interrogative-Verbs:OBL
  - 0.96  NTU:OBL ~ Kavalan-Chang-Reference-Grammar:受格
  - 0.96  NTU:OBL ~ Amis-Kavalan-Lin-Interrogative-Verbs:OBL
  - 0.88  NTU:處格 ~ Kavalan-Chang-Reference-Grammar:處所格
  - 0.72  Kavalan-Chang-Reference-Grammar:主格 ~ Amis-Kavalan-Lin-Interrogative-Verbs:ABS
  - 0.65  NTU:屬格 ~ Kavalan-Chang-Reference-Grammar:屬格

### Amis

- NTU `NOM` (n=817): ku:43% cingra:15% kuya:13% kiya:7% kaku:7%
- NTU `主格` (n=814): ku:43% cingra:15% kuya:13% kiya:7% kaku:7%
- NTU `GEN` (n=679): nira:40% nu:29% aku:15% nuya:6% niya:3%
- NTU `屬格` (n=678): nira:40% nu:29% aku:15% nuya:6% niya:3%
- NTU `OBL` (n=345): tu:55% tuya:18% tiya:9% tura:4% tunini:4%
- NTU `斜格` (n=343): tu:55% tuya:18% tiya:9% tura:4% tunini:4%
- NTU `處格` (n=192): i:99% an:1%
- NTU `所有格` (n=45): maku:51% mita:20% ningra:11% misu:4% niyam:4%
- Amis-Pa-Verbs `NOM` (n=29): k:41% ∅:24% kaku:24% cingra:7% ku:3%
- Amis-Kavalan-Lin-Interrogative-Verbs `ABS` (n=26): k:73% kisu:12% kaku:8% cingra:4% ku:4%
- Amis-Pa-Verbs `DAT` (n=23): t:61% an:39%
- Amis-Kavalan-Lin-Interrogative-Verbs `ERG` (n=17): ni:59% isu:35% aku:6%
- Amis-Kavalan-Lin-Interrogative-Verbs `OBL` (n=11): t:82% an:18%
- Amis-Pa-Verbs `GEN` (n=10): n:50% aku:40% ni:10%
- Amis-Kavalan-Lin-Interrogative-Verbs `GEN` (n=4): aku:50% nu:50%

  - 0.79  Amis-Kavalan-Lin-Interrogative-Verbs:OBL ~ Amis-Pa-Verbs:DAT
  - 0.56  Amis-Kavalan-Lin-Interrogative-Verbs:ABS ~ Amis-Pa-Verbs:NOM
  - 0.44  NTU:屬格 ~ Amis-Kavalan-Lin-Interrogative-Verbs:GEN
  - 0.43  NTU:GEN ~ Amis-Kavalan-Lin-Interrogative-Verbs:GEN
  - 0.40  Amis-Kavalan-Lin-Interrogative-Verbs:GEN ~ Amis-Pa-Verbs:GEN

### Kanakanavu

- NTU `主格` (n=2016): sua:41% ku:20% kasu:10% kia:8% nguain:7%
- NTU `NOM` (n=1740): sua:40% ku:20% kasu:10% kia:10% nguain:6%
- ILCAA-Kanakanavu-Texts `NOM` (n=995): sua:56% ku:18% kia:10% kita:5% kasu:3%
- NTU `屬格` (n=762): maku:41% kee:16% musu:14% in:13% mita:5%
- NTU `GEN` (n=606): maku:46% kee:15% musu:12% in:10% mita:6%
- ILCAA-Kanakanavu-Texts `GEN` (n=596): ini:44% maku:19% in:13% aku:6% ni:4%
- Song-Kanakanavu-Grammar `主格` (n=348): sua:43% ku:18% nguain:15% kasu:11% kita:3%
- ILCAA-Kanakanavu-Texts `OBL` (n=339): ʔinia:48% ʔikua:23% kamua:7% kimia:5% sua:5%
- NTU `斜格` (n=211): kasua:20% 'inia:18% 'ikua:16% kamua:12% na:9%
- NTU `處格` (n=198): na:99% a:1%
- NTU `OBL` (n=180): kasua:19% 'ikua:13% 'inia:13% kamua:12% na:11%
- Song-Kanakanavu-Grammar `屬格` (n=171): maku:25% musu:23% kee:21% in:20% mia:4%
- Song-Kanakanavu-Grammar `處格` (n=88): na:100%
- NTU `所有格` (n=69): maku:33% tamna:28% mita:12% in:10% musu:7%
- NTU `處所格` (n=65): na:94% sua:5% mataa:2%
- Song-Kanakanavu-Grammar `斜格` (n=42): 'inia:38% 'ikua:24% kasua:21% kamua:12% kitana:2%
- NTU `受格` (n=9): iikua:33% 'ikua:22% kitana:11% kamua:11% kimia:11%
- NTU `ACC` (n=9): iikua:33% 'ikua:22% kimia:22% kitana:11% kamua:11%

  - 0.99  NTU:處格 ~ Song-Kanakanavu-Grammar:處格
  - 0.94  NTU:處所格 ~ Song-Kanakanavu-Grammar:處格
  - 0.86  NTU:主格 ~ Song-Kanakanavu-Grammar:主格
  - 0.83  NTU:NOM ~ Song-Kanakanavu-Grammar:主格
  - 0.77  NTU:屬格 ~ Song-Kanakanavu-Grammar:屬格
  - 0.77  NTU:NOM ~ ILCAA-Kanakanavu-Texts:NOM
  - 0.76  NTU:主格 ~ ILCAA-Kanakanavu-Texts:NOM
  - 0.70  NTU:斜格 ~ Song-Kanakanavu-Grammar:斜格

### Seediq

- NTU `主格` (n=1655): ka:62% ku:18% su:6% ta:5% miyan:3%
- NTU `屬格` (n=1470): na:49% mu:18% daha:11% su:10% ta:8%
- NTU `NOM` (n=1210): ka:56% ku:21% su:6% ta:6% miyan:4%
- NTU `GEN` (n=1154): na:51% mu:17% daha:10% ta:10% su:7%
- Seediq-Chang-Reference-Grammar `主格` (n=138): ka:100%
- Seediq-Chang-Reference-Grammar `屬格` (n=57): na:100%
- Naomi-Tsukida-Correlative-Clauses-Seediq `NOM` (n=35): ka:83% ku:9% nami:3% su:3% ta:3%
- Naomi-Tsukida-Correlative-Clauses-Seediq `GEN` (n=11): na:64% su:18% mu:18%
- Naomi-Tsukida-Correlative-Clauses-Seediq `OBL` (n=7): an:86% 'an:14%
- NTU `所有格` (n=4): ndheya:25% naku:25% nisu:25% nita:25%
- NTU `受格` (n=3): heya:67% un:33%

  - 0.83  Seediq-Chang-Reference-Grammar:主格 ~ Naomi-Tsukida-Correlative-Clauses-Seediq:NOM
  - 0.78  NTU:主格 ~ Naomi-Tsukida-Correlative-Clauses-Seediq:NOM
  - 0.76  NTU:屬格 ~ Naomi-Tsukida-Correlative-Clauses-Seediq:GEN
  - 0.75  NTU:GEN ~ Naomi-Tsukida-Correlative-Clauses-Seediq:GEN
  - 0.72  NTU:NOM ~ Naomi-Tsukida-Correlative-Clauses-Seediq:NOM
  - 0.64  Seediq-Chang-Reference-Grammar:屬格 ~ Naomi-Tsukida-Correlative-Clauses-Seediq:GEN
  - 0.62  NTU:主格 ~ Seediq-Chang-Reference-Grammar:主格
  - 0.56  NTU:NOM ~ Seediq-Chang-Reference-Grammar:主格

### Sakizaya

- NTU `主格` (n=1450): ku:35% kya:18% ci:10% ciniza:7% kuyni:7%
- NTU `屬格` (n=873): nu:43% niza:15% nya:11% ni:9% aku:8%
- NTU `NOM` (n=870): ku:28% kya:27% kuyni:11% ciniza:7% kuheni:5%
- NTU `GEN` (n=575): nu:51% nya:17% niza:13% nuyni:7% nuheni:3%
- NTU `斜格` (n=516): tu:50% tuyni:17% tya:16% an:6% tuyza:2%
- NTU `OBL` (n=283): tuyni:32% tya:29% tu:27% tuyu:3% tuyza:2%
- Sakizaya-Affixes `主格` (n=194): ku:58% ci:17% kaku:15% kita:4% kisu:3%
- Sakizaya-Affixes `屬格` (n=156): nu:52% ni:18% aku:14% ita:5% misu:3%
- Sakizaya-Affixes `斜格` (n=93): tu:82% ci:8% an:6% takuwan:1% takuwanan:1%
- NTU `所有格` (n=83): maku:39% mita:23% niyam:12% misu:10% heni:7%
- Sakizaya-Affixes `處所格` (n=54): i:96% ni:2% an:2%
- NTU `處格` (n=10): i:50% an:40% ku:10%

  - 0.66  NTU:屬格 ~ Sakizaya-Affixes:屬格
  - 0.60  NTU:GEN ~ Sakizaya-Affixes:屬格
  - 0.57  NTU:斜格 ~ Sakizaya-Affixes:斜格
  - 0.56  NTU:主格 ~ Sakizaya-Affixes:主格
  - 0.52  NTU:處格 ~ Sakizaya-Affixes:處所格
  - 0.35  NTU:NOM ~ Sakizaya-Affixes:主格
