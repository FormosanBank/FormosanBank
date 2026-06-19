# Siraya Gospels of Gravius

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

In the 1600s, Gravius translated John and Matthew to Siraya. The translations were published side-by-side with a Dutch translation.

These were digitized through a combination of OCR and hand correction (though the Dutch has not yet been fully corrected.)

We added an English translation in the form of the King James Bible, and a Chinese translation in the form of the Chinese Union version. Both are public domain.

***

**Notes**

* The Dutch translations of Matthew are incomplete and error-prone. They are included for now but should not be used. 

* The Dutch is quite hard to read. b and v are probably confused frequently.

* Matthew 25:11 has an æ̈ character (æ̈ with an umlaut). It almost certainly occurs somewhere else, but none made it into the XML.

***

**Versificiation**

The Siraya John 1 has 52 verses, whereas more modern version (even King James) have 51. Claude Sonnet 4.6 used the Dutch translations to come up with this analysis:

Looking at the KJV vs the Dutch translations in the XML, the divergence is clear at verse 38/39:

XML verse38 (Dutch): "Ende Jesus hem omkeerende ende siende haer bolgen/ seyde tot harr." → "Jesus turned and saw them following, and said to them" — only the first half of KJV 1:38
XML verse39 (Dutch): "Wat soeckt ghy... Rabbi... waer woont ghye" → "What seek ye? Rabbi... where dwellest thou?" — the second half of KJV 1:38
KJV 1:38 is: "Then Jesus turned, and saw them following, and saith unto them, What seek ye? They said unto him, Rabbi... where dwellest thou?"

The 1661 Gravius text split KJV 1:38 into two separate verses. From that point on, the XML numbering is exactly one ahead of KJV:

XML verse	KJV verse
38	first half of 1:38
39	second half of 1:38
40	1:39
41	1:40
…	…
51	1:50
52	1:51
So when adding English translations, for John chapter 1, verses 1–37 map 1:1 directly, then verses 39–52 map to KJV verses 38–51.

***

**Quality Control**

Quality Control Modifications

Below is a list of preliminary lexical adjustments made to Siraya words broked up by line breaks in the text by hyphen -. 
They have been consolidated based on full word appearances in surrounding verses. 

A-lid -> Alid
ma-mang -> mamang
kianna -> ki anna
kan-na -> kanna
tatau -> ta tau 
ræ-mæh -> ræmæh 
te-ni -> teni
ty-ni -> tyni
Tama-mat-tæ'i-tan -> Tama-mattæ'i-tan
ba-lei -> balei
ap-pa -> appa
kmyt-ta -> kmytta
mat'-moei -> mat'moei 
Joan-nes -> Joannes
kana-dap -> kanadap
E-saïas -> Esaïas
Fa-riseen -> Fariseen 
Be-thabara -> Bethabara
Rab-bi -> Rabbi 
Jo-na -> Jona 
Mo-ses -> Moses
Mat-tæ -> Mattæ
Naza-reth -> Nazareth 
Natha-naël -> Nathanaël 
Jo-den -> Joden 
ma-riang -> mariang 
mali-touk -> malitouk 
Je-sus -> Jesus 
Ni-kodemus -> Nikodemus
as-si -> assi 
pa-mut -> pamut
Chri-stus -> Christus 
Samari-tanen -> Samaritanen 
Ja-cob -> Jacob
ra-loum -> raloum  
dmier-ri -> dmierri  
Ju-dea -> Judea 
Je-rusalem -> Jerusalem
mis-sing -> missing 
A-lak -> Alak 
pas-tæ -> pattæ
vavou-las -> vavoulas 
Je-den -> Joden 
Filip-pus -> Filippus 
R ab-bi -> Rabbi 
ra -> râ
Jesuss -> Jesus  
R a-ma -> Rama 
yul-lum -> vullum 
vul-um -> vullum
te-nitou -> teni tou
KamamangKk'atta -> Kamamang k'atta
Ka-pernaum -> Kapernaum 
Pæhta-tutæu -> Pæhtatæutæu   
at-ta -> atta 
Ta-touhko -> Tatouhko
Fari-seen -> Fariseen 
va-rau -> varau
A-braham -> Abraham
ty- ni -> tyni 
Samari-taen -> Samaritaen
Abra-ham -> Abraham 
ta-ma -> tama 
Jeru-salem -> Jerusalem
Betha-nia -> Bethania
Mar-tha -> Martha
La-zarus -> Lazarus
Pahtatæu-tæu -> Pahtatæutæu
Ma-ria -> Maria 
Ka-jafas -> Kajafas
Esra-im -> Esraim
Nar-dus -> Nardus  
kaasfi -> ka assi 
Hiad-doudoung -> Hiaddoudoung
Hiaddou-doung -> Hiaddou-doung
Si-mon -> Simon
Pe-trus -> Petrus 
Iska-riot -> Iskariot
Ju-das -> Judas 
Asfsi -> Assi 
hmas -> hmaä
mak-ka -> makka 
Ra-man -> Raman
Mei-rang -> Meirang
Ra-ma -> Rama 
afssi -> assi 
ma-dallia -> madallia 
myh-ka -> myhka 
ka-væ -> kavæ
Pahta-tæutæu -> Pahtatæutæu
Na-zareth -> Nazareth 
Pahtatæu-tæuugh -> Pahtatæutæuugh
Da-dyllo -> Dadyllo
Pah-tatæutæu -> Pahtatæutæu 
Annatani -> Annata ni
ym-hou -> ymhou
Pi-latus -> Pilatus
ba-vau -> bavau
Barra-bas -> Barrabas  
Pila-tus -> Pilatus 
Tatouh-ko -> Tatouhko 
He-breen -> Hebreen  
Ma-gdalena -> Magdalena
Pæhtatæu-tæu -> Pæhtatæutæu 
Pah-tateutæu -> Pahtateutæu 
Pahta-tæu -> Pahta-tæu
R ab-bouni -> Rabbouni
Ra-ram -> Raram 
R a-ram -> Raram  
Ph-tatæutu -> Pæh-tatæutæu
An-nata -> Annata

After these changes were made by hand, we wrote code to accomplish the same thing automatically. `fix_linebreak_hyphens.py` will remove a hyphen if at least two examples of the hyphenless Siraya word were found elsewhere in the text prior to any changes. It outputs two useful log files:

* `hyphen_removals.csv` 

This was set to be quite conservative and only apply if the version with the hyphen was infrequent and the alternative was very frequent. However, this does sometimes result in removing hyphens that were not the result of a line break. This is perhaps desirable behavior. To be safe, this is applied only to the "standard" tier.