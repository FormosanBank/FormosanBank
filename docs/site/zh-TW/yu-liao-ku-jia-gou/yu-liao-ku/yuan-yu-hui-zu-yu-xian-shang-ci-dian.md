# 原語會族語線上辭典

### **概述**

[原住民族語言研究發展基金會](https://www.ilrdf.org.tw/en/)（ILRDF，以下簡稱原語會）族語線上辭典是一項全面又完整的數位資源，旨在保存與推廣臺灣原住民族語言。該辭典以[原住民族委員會](https://www.cip.gov.tw/en/index.html)與教育部於2005年共同頒布的[原住民族語言書寫系統](https://yongfu.name/temp-data/pdf/writingsystemsdoc.pdf)為基礎，代表著數百名參與者將近七年合作努力的成果。原語會族語線上辭典是語言復振、教育與研究的重要工具，確保臺灣原住民族的文化與語言知識得以為後代永續保存。

原語會族語線上辭典語料庫是FormosanBank專案計畫不可或缺的組成部分，其提供了豐富且結構化的語料集，包括16個官方認定的臺灣南島語：阿美語、泰雅語、賽夏語、邵語、賽德克語、布農語、排灣語、魯凱語、太魯閣語、噶瑪蘭語、鄒語、卡那卡那富語、拉阿魯哇語、卑南語、雅美(達悟)語及撒奇萊雅語。這些辭典在記錄和保存語言多樣性具有重要價值，內容涵蓋文字、錄音和翻譯，為研究、教育及語言復振提供了全面的資源。

***

### **背景**

該計畫於2007年啟動，系統性地編纂16族原住民語的辭典。每部辭典平均耗時兩年完成，凝聚了語言教師、專家與學者們的心血。至2014年，所有辭典均已編纂完成，是臺灣原住民族語言記錄的一項重要里程碑。

體認到永續發展的重要性，原語會將這些辭典進行數位化，並推出族語線上辭典平台。此數位轉型使辭典得以具動態性、可擴展性及可維護性，成為語言推廣、教學、研究與學習的重要資源。

**原語會族語線上辭典特點**

1. 線上存取與查詢
   * 使用者可實時查詢單詞、查看其定義、聆聽發音，並搜尋相關例句。
2. 資源下載
   * 該平台提供可供離線學習的下載內容，包括：
     * 詞卡
     * 全辭典文本
     * 華語索引版本
3. 互動學習工具
   * 功能包括：
     * 線上測驗：測試您對語言知識的掌握程度。
     * 詞彙建議：貢獻或建議新詞彙。
     * 範例與應用：提供實用句子，便於即時學習與應用。
4. 社群參與
   * 使用者可以在討論區分享回饋或交流使用問題，營造友善互動的環境。
   * 定期諮詢專家，以確保內容更新與準確性，並將詞彙使用的最終決策權交還至各族族人。
5. 語料收集API（應用程式介面）
   * 原語會提供的API有助於精簡語料收集以及與FormosanBank的整合，確保有效存取完整的字典內容。

***

### **語料庫處理**

以下，我們概述處理流程和品質管控措施，這些措施旨在將語料重新架構為機器可讀取的格式，同時也確保其準確性和可用性。

1. 自PDF提取語料
   * 首先，自原語會為每個語言所提供的PDF檔中提取辭典條目。使用特定標記（例如：★）來識別條目，以將辭典內容與其他文字做區分。
   * 提取的條目作為詞彙清單儲存在words\_list目錄中以供進一步處理。
2. 詞彙語料的API整合
   * 提取的詞彙可用於查詢原語會API、檢索：
     * 詞彙釋義
     * 展示詞彙使用語境的例句
     * 發音的音檔連結
   * 這些API呼叫的結果會儲存在每種語言的.PickleScrapes檔案，便於後續的高效存取與再用。
3. XML轉換
   * 爬取的資訊經過結構化，以符合FormosanBank XML標準的XML格式，確保與FormosanBank內其他語料庫的一致性與兼容性。
     * 每個辭典條目表示為一個XML `<S>` 元素，其中包含：
     * `<FORM>`：原始單詞或片語。
     * `<TRANSL>`：單詞或例句的華語翻譯。
     * `<AUDIO>`：音訊檔案的連結或路徑。
4. 音訊檔案的下載與整合
   * 音檔是透過API連結下載，並存放於XML/audio下各語言專屬的子資料夾中。
   * 對應的XML文件已更新包含音訊檔案的路徑，實現無縫整合。
5. 清理與標準化
   * XML檔案經過進一步清理，移除空元素並標準化標點符號與拼寫。
   * 將HTML轉義碼替換為對應的字元，並且將kindOf="standard" 屬性新增到\<FORM>元素中。原始文本標記為\<FORM kindOf="original">，標準化的文本則標記為\<FORM kindOf="standard">。
6. 品質管控
   * 執行品質管控，步驟如下：
     * 將詞彙列表與API結果進行交叉檢查，確保所有條目皆已成功處理。
     * 驗證XML結構以確保符合FormosanBank的XML架構標準。
     * 手動檢查隨機樣本以核實語料的完整性。
     * 以[官方拼寫法](https://yongfu.name/temp-data/pdf/writingsystemsdoc.pdf)為參考進行字詞頻率分析，檢查拼寫中是否存在異常情況。

***

### **語料庫的主要特點**

1. 語料面向
   * 該語料庫總計包含659,295個詞元及超過135小時的音訊，這為研究臺灣南島語提供了豐富又全面的資源。透過細緻化的製作過程，以提升其語料及音檔的完善和高品質。
2. 音訊整合
   * 高品質的音訊檔案伴隨多數例句，為分析發音、音韻及口語語境提供寶貴資源。
3. 翻譯支援
   * 例句均附有華語翻譯，確保研究者與學習者能夠方便使用。

***

### **重要性**

1. 語言保存
   * 該語料庫支持瀕危原住民族語的記錄與復振，確保其作為活的文化資產得以延續。
2. 可及性
   * 此線上平台跨越地理藩籬，將資源提供予世界各地的使用者。
3. 教育與研究&#x20;
   * 憑藉豐富範例與結構化的內容，這些辭典對語言學習者與研究者而言皆是無價之寶。

***

### **存取資訊**

* 您可以瀏覽族語線上辭典的線上平台：[https://e-dictionary.ilrdf.org.tw](https://e-dictionary.ilrdf.org.tw)，探索16族原住民語的辭典。
* 您可在[此處](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/ILRDF_Dicts)找到FormosanBank中族語線上辭典語料庫的儲存庫以及重建語料庫的程式碼。

***

### **致謝**

誠摯感謝各族族人、語言學家與研究人員的共同合作，本計畫才能得以完成。尤其感謝原住民族語言研究發展基金會（[ILRDF](https://www.ilrdf.org.tw/en/)）的寶貴貢獻，以及臺灣原住民族的支持與參與。

***

### **版權**

根據族語線上辭典的[版權頁](https://e-dictionary.ilrdf.org.tw/copyright.htm)，ILRDF所監製的著作，如辭典，屬於「合理使用」範疇，且可以複製：

本網站上所刊載以本會名義公開發表之著作，即著作人為本會者，在合理範圍內，得重製、公開播送或公開傳輸；利用時，並請註明出處。

***

### **引用說明**

根據我們的[使用條款](../../qi-ta-zi-yuan/shi-yong-tiao-kuan.md)，若您在任何出版物中使用此語料庫或其衍生產品，必須同時引用FormosanBank及與所使用語言相對應的辭典：

* 阿美語: Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 阿美語 \[Indigenous languages online dictionary: Amis language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 泰雅語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 泰雅語 \[Indigenous languages online dictionary: Atayal language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 布農語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 布農語 \[Indigenous languages online dictionary: Bunun language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 卡那卡那富語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 卡那卡那富語 \[Indigenous languages online dictionary: Kanakanavu language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 噶瑪蘭語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 噶瑪蘭語 \[Indigenous languages online dictionary: Kavalan language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 排灣語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 排灣語 \[Indigenous languages online dictionary: Paiwan language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 卑南語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 卑南語 \[Indigenous languages online dictionary: Puyuma language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 魯凱語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 魯凱語 \[Indigenous languages online dictionary: Rukai language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 拉阿魯哇語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 拉阿魯哇語 \[Indigenous languages online dictionary: Saaroa language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 賽夏語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 賽夏語 \[Indigenous languages online dictionary: Saisiyat language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 撒奇萊雅語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 撒奇萊雅語 \[Indigenous languages online dictionary: Sakizaya language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 賽德克語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 賽德克語 \[Indigenous languages online dictionary: Seediq language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 邵語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 邵語 \[Indigenous languages online dictionary: Thao language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 太魯閣語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 太魯閣語 \[Indigenous languages online dictionary: Truku language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 鄒語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 鄒語 \[Indigenous languages online dictionary: Tsou language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
* 雅美(達悟)語：Council of Indigenous Peoples, & Indigenous Languages Research and Development Foundation. (2024, January). 原住民族語言線上辭典: 雅美語 \[Indigenous languages online dictionary: Yami language]. Executing Institution: National Taiwan Normal University. [https://e-dictionary.ilrdf.org.tw/](https://e-dictionary.ilrdf.org.tw/)
