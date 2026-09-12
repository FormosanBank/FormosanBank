# Preserved Siraya transcription corrections

These corrections and the fixed hyphen-removal CSV were carried forward from the published corpus. They are historical evidence, not instructions to rerun the retired OCR notebooks.

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
