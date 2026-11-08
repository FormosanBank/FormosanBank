# Virginia Fey阿美語辭典

### **概述**

Virginia Fey的阿美語辭典是一本重要的著作，詳盡記錄了阿美語。該辭典於1980年代中期開始編纂，並在後來進行了修訂，採用更新的拼寫法，Virginia Fey的阿美語辭典為各方研究、教育人員提供了一項寶貴的語言資源。

這部辭典為FormosanBank的重要資源之一，與其他語料庫相輔相成，提供了更豐富的阿美語詞彙及細微語意差異的詮釋。它包含了非常多的詞條，並附有英語和華語的定義，某些詞條亦提供阿美語的例句。

***

### **背景**

由Virginia Fey於1986年首次編纂，該辭典經歷幾個階段的轉變：

1. **原始文獻：**&#x6700;初以舊式天主教拼寫法發行，旨在為阿美語的使用者和學習者提供參考指南。
2. **拼寫法修訂：**&#x7531;於語言學者們的努力──尤其是Namoh Rata吳明義教授的貢獻，該語料庫後來被轉換為與原住民族語言書寫系統一致的新式拼寫法。
3. **數位化改編：**&#x6578;位版源自社群主導的努力，如[GitHub: miaoski/amis-data](https://github.com/miaoski/amis-data)等資料庫中所記錄的成果。這一開源合作使此辭典得以整合入FormosanBank的標準化XML格式。

***

### **語料庫特點**

* **詞彙條目：**&#x5305;括範圍廣泛的詞彙條目，涵蓋日常物品、動作、文化概念、植物和動物等。
* **多語言定義：**&#x6BCF;項詞條基本上會提供英語和華語釋義，提升辭典的實用性，並允許更廣泛的研究範圍。
* **例句：**&#x90E8;分條目提供阿美語例句，提供語境並展示其用法。
* **拼寫法修訂：**&#x8FAD;典資料已從舊式天主教拼寫法更新為目前在原住民族語言教育和族語復振工作中使用的標準化拼寫法。

***

**語料庫處理**

將辭典資料轉換為FormosanBank標準化XML格式，處理流程包含以下階段：

1. **語料獲取:** 來源資料取自[miaoski/amis-data](https://github.com/miaoski/amis-data) GitHub存儲庫。CSV檔案提供了詞彙條目、英語和華語的定義，有時還包括阿美語的例句。
2. **語料擷取與XML轉換:**
   * CSV檔案中的每項條目包含阿美語的詞彙、英語及華語的定義，部分條目還會附有例句及其相應的翻譯。
   * CSV資料經過擷取並依照FormosanBank XML標準結構化為XML格式，確保與FormosanBank中的其他語料庫相容。
   * 每個條目表示為一個XML \<S> 元素，其中包含：
     * `<FORM>`：原始單詞或句子。
     * `<AUDIO>`：英文和華語翻譯（如果有提供）。
3. **清理與標準化:**
   * XML檔案經過進一步清理，例如去除空元素並標準化標點符號和拼寫。
   * 將HTML轉義碼替換為對應的字元，並且將`kindOf="standard"`屬性新增到`<FORM>`元素中。原始文本標記為`<FORM kindOf="original">`，標準化的文本則標記為<`FORM kindOf="standard">`。
4. **品質管控:**
   * 執行品質管控，步驟如下：
     * 交叉參照詞彙清單與API結果，確保所有條目都已成功處理。
     * 驗證XML結構，以確保符合FormosanBank標準。
     * 隨機樣本的手動檢查，以驗證資料的完整性。
     * 進行字詞頻率分析，將[官方拼寫法](https://yongfu.name/temp-data/pdf/writingsystemsdoc.pdf)及[原語會族語辭典語料庫](https://docs.google.com/document/d/1eXZzq4oKyJD2CIsgI6vB6sZi9e0CoYoO/edit#heading=h.ihv636)進行對比，以檢查是否存在任何異常。

***

### **語料庫備註**

此部分說明語料庫中的相關註解（例如：解釋非標準拼寫法字詞的出現）

* 根據Li等人（2024）的說法：「Fey（1986）的字典...忽略了某些音素差異，例如喉塞音與咽化塞音之間的區別，比如，秀姑巒阿美語'op'op『青蛙』與qopo『集合』」。然而，這個語料庫的原始資料庫指出，「感謝吳明義先生將天主教的舊式拼法，改寫成原民會版本的新式拼法。」目前尚不清楚這是否解決了Li等人提出的擔憂，但該拼寫法似乎與我們的參考語料庫相符。
* 某些句子常會有多種不同的翻譯，因此不要假設每個目標語言只有一個元素。

***

### **重要性**

* 語言保存：透過廣泛的詞彙條目及其含義的記錄，本辭典有助於保存和復振阿美語。
* 語言學研究：研究人員可以使用標準化、機器可讀的語料庫，促進辭典學分析、比較研究以及自然語言處理工具的開發。
* 教育資源：教育工作者和在地族人可以利用辭典來創建學習材料、提供課堂教學並開發語言應用程式。

***

### **存取資訊**

* 用於生成FormosanBank語料庫的原始數位線上字典可以在此找到：[https://github.com/miaoski/amis-data](https://github.com/miaoski/amis-data)
* 包含Virginia Fey阿美語辭典語料庫及重建語料庫的程式碼的資料庫可以[在此](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Virginia_Fey_Dictionary)找到。

***

### **版權**

根據我們所引用的GitHub資料庫 [https://github.com/miaoski/amis-data](https://github.com/miaoski/amis-data)，台灣聖經公會已提供CC-BY-NC授權許可：

> 謹感謝 臺灣聖經公會 授權電子化。商業使用之授權，請洽\[臺灣聖經公會]。

> 感謝吳明義老師將天主教的舊式拼法，改寫成原民會版本的新式拼法。

> This work is licensed under the Creative Commons 姓名標示-非商業性 3.0 Unported License. To view a copy of this license, visit [http://creativecommons.org/licenses/by-nc/3.0/deed.zh\_TW](http://creativecommons.org/licenses/by-nc/3.0/deed.zh_TW).

目前公開XML標示為CC BY-SA，與上述來源的CC BY-NC聲明衝突。在中繼資料完成調整前，使用者應遵循限制較嚴格的來源CC BY-NC條款。

***

### **致謝**

本辭典是許多個人和組織團體奉獻與合作的成果：

* Virginia Fey：辭典的原始編纂者。
* Namoh Rata吳明義老師：將舊的天主教拼寫轉換為新的標準化版本。
* 台灣聖經公會：授權數位化並改編字典。
* GitHub貢獻者：使資料得以存取並易於整合進FormosanBank。

***

### **引用說明**

根據我們的[使用條款](../../qi-ta-zi-yuan/shi-yong-tiao-kuan.md)，若您在任何出版物中使用此語料庫或任何從此語料庫衍生的產品，您必須同時引用FormosanBank以及以下資料：

* Fey, V. (1986). Amis dictionary. Taipei: The Bible Society.
* miaoski. (2023). miaoski/amis-data \[Python]. GitHub. [https://github.com/miaoski/amis-data](https://github.com/miaoski/amis-data) (Original work published 2013)
