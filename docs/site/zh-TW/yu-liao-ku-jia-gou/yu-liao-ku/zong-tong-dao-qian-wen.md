# 總統道歉文

### **概述**

2016年8月1日，蔡英文總統在原住民日代表政府向臺灣原住民族作出歷史性致歉。道歉的內容涉及原住民族族人在四百年間所遭受的痛苦和不公平待遇，這同時也標誌著總統府原住民族歷史正義與轉型正義委員會（原轉會）的成立。

這份道歉文是作為推動歷史正義的起點，並已翻譯成16族官方認定的臺灣南島語：阿美語、泰雅語、賽夏語、邵語、賽德克語、布農語、排灣語、魯凱語、太魯閣與、噶瑪蘭語、鄒語、卡那卡那富語、拉阿魯哇語、卑南語、雅美(達悟)語和撒奇萊雅語。這些翻譯後的道歉文本構成了本語料庫的主要內容。本語料庫僅包含文本資料。另外也提供英語和華語版本。

***

### **語料庫處理**

總統道歉文語料庫源自於翻譯官方釋出的臺灣總統道歉文而來。這些翻譯文本包含有16種官方認定的臺灣南島語以及華語和英語版本。語料庫的處理步驟如下：

1. **句子譯文間的對齊處理:** 每段臺灣南島語文本與其對應的英語和華語翻譯進行了對齊處理。我們將道歉文內容均分切割為33個段落，所有語言的分段均保持一致，下方展示一個範例圖示。唯一的例外是卡那卡那富語，其分段與其他語言有較大差異，因此單獨另外處理，僅分為29個段落。

<figure><img src="../../.gitbook/assets/image (4).png" alt=""><figcaption></figcaption></figure>

2. **依據FormosanBank標準生成XML:** 對齊後的資料經過結構化成為符合FormosanBank標準的XML檔案。每個XML檔案包含以下內容：
   * 每個段落標註句子層級（S）元素，子元素FORM代表臺灣南島語文本，子元素 TRANSL則代表英語和華語翻譯。
   * 每種臺灣南島語特有的後設資料和語言代碼。
3. **清理與標準化:** XML檔案生成之後，都經歷多道清理與標準化程序，如下所述：
   * XML清理：標準化標點符號，並將Unicode字元進行扁平化處理，合併變音符號與其基本字元。
   * 拼寫法標準化：進行二次處理，在保留原始版本的同時，新增標準化版本的臺灣南島語文本，以確保一致性，例如在適用情況下將所有「u」轉換為「o」。
   * 最終調整：將HTML轉義碼替換為對應字元，並新增屬性如kindOf="original"和kindOf="standard"，以確保符合[XML架構要求](https://docs.google.com/document/d/1eXZzq4oKyJD2CIsgI6vB6sZi9e0CoYoO/edit#heading=h.4i7ojhp)。
4. **輸出:** 處理完成的XML檔案存放於XML目錄中，每個檔案以其對應的臺灣南島語命名。每份檔案格式處理都確保其可讀性與分析容易度。

***

### **語料庫備註**

此部分說明語料庫中的相關備註（例如，解釋非標準拼寫法的字詞的出現）

* 阿美語：總統道歉文本的阿美語版本中出現了幾次字母b，這並不屬於該語言的標準拼寫法。所有b都集中出現於兩個詞中：Balay和Sbalay。這兩個詞是原道歉文本中引用的泰雅語詞彙，並以相同形式出現在阿美語翻譯中。以下是英文翻譯中的範例：「在泰雅語中，真相叫做 'Balay'，而和解叫做 'Sbalay'」。
* 卡那卡那富語：此語料庫中出現少量的字母h和f，包含h或f的字詞在原語會族語辭典語料庫中均未出現，因此，我們選擇保留這些字母。
* 卑南語：此語料庫中多次出現字母ē，都跟yēncumin（標記為外來詞）和sēhu這兩個詞彙有關，因此，我們未對其進行統一處理。
* 撒奇萊雅語：少量含f的字詞被視為是外來詞。

***

### **重要性**

1. **保存原住民族語言:** 將道歉文本翻譯成族語，確保所有原住民族族人都能接觸到該文本，並且有助於語言保存和復振。
2. **統一文本以利語言學比較:** 跨多種語言所提供的相同文本，有助於研究和比較臺灣南島語各語言之結構、詞彙與句法。
3. **文化與語言認同:** 此語料庫足以彰顯原住民族語言在面對歷史事件和在臺灣文化脈絡中的重要性。該語料庫代表著保存語言多樣性的重要舉措，並以臺灣原住民族的母語角度來理解重大歷史事件。

***

### **存取資訊** &#x20;

* 有關道歉文的資訊、英語和華語的道歉文本以及16族臺灣南島語版本的文本，均可[於此](https://indigenous-justice.president.gov.tw/)公開獲取。 &#x20;
* 您可在[此處](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Presidential_Apologies)找到FormosanBank中總統道歉文語料庫的儲存庫以及重建語料庫的程式碼。&#x20;

***

### **版權**

根據[臺灣的版權規定](https://commons.wikimedia.org/wiki/Commons:Copyright_rules_by_territory/Taiwan)，總統演講的轉錄不受版權保護，因為它們屬於公共領域。

> 未受保護的部分
>
> 另見：[Commons:未受版權保護的作品](https://commons.wikimedia.org/wiki/Commons:Unprotected_works)
>
> 根據2022年6月15日修訂的《著作權法》，以下項目不屬於著作權的標的，適用於\{{PD-ROC-exempt\}}：\[2022年第9條]
>
> 1. 憲法、法律、命令或公文。
> 2. 由中央或地方政府機關翻譯或編纂的前項所指之作品。
> 3. 標語及常用之符號、名詞、公式、數字表、表格、筆記簿或年曆。
> 4. 僅為傳達事實之新聞報導的口述或文字作品。
> 5. 根據法律或命令舉行的各類考試的試題及其選擇性試題。
>
> 前項第一款所稱「公文」，包括公告、演說詞、新聞稿及公務員執行職務所製作的其他文書。\[2022年第9條]

***

### **引用說明**

依據我們的[使用條款](../../qi-ta-zi-yuan/shi-yong-tiao-kuan.md)，若您在任何出版物中使用此語料庫或任何由此語料庫衍生的產品，您必須同時引用FormosanBank以及：

* **引用道歉文文本（通用版）：**&#x54;sai, I. W. (2016, August 1). President Tsai Ing-wen's apology to the Indigenous Peoples on behalf of the government \[Speech transcript]. [https://indigenous-justice.president.gov.tw/](https://indigenous-justice.president.gov.tw/)
* **引用道歉文文本（特定語言版）：**&#x54;sai, I. W. (2016, August 1). President Tsai Ing-wen's apology to the Indigenous Peoples on behalf of the government \[Speech transcript, Amis translation]. [https://indigenous-justice.president.gov.tw/](https://indigenous-justice.president.gov.tw/)
