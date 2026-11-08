---
icon: file-lines
---

# FormosanBank的XML格式

FormosanBank使用的XML格式是以Pangloss Collection為基礎的標準化結構，以確保語料庫的一致性並利於計算處理。此格式也提供詳細的語言學標註和後設資料管理，使研究人員、語言愛好者和開發者能易於瀏覽、分析和整合語料。同時，採取統一格式，將促進FormosanBank的透明度以及與其他語言學工具、資源的互通性，使其成為該計畫技術架構下的關鍵組成要素。

***

### 基本結構

XML格式遵循層級結構，主要元素的組織方式如下：

```
<TEXT xml:lang="fr" source="" audio="">
    <S>
        <W>
            <M>
            </M>
        </W>
    </S>
</TEXT>
```

***

### 帶有ID屬性的範例

每個元素都包含唯一的識別符（`id`），以便引用：

```
<TEXT xml:lang="ami" id="story1">
    <S id="S1">
        <W id="S1W1">
            <M id="S1W1M1">
            </M>
        </W>
    </S>
</TEXT>
```

***

### \<TEXT>元素

`<TEXT>`代表整個文檔。`<TEXT>`是根元素，只能有\<S>標籤作為子元素。\<TEXT>元素必須包含以下屬性：

* `id`：文本的唯一標識符；跨資源中唯一。
* `citation`：對原始來源的APA格式引用。關於此XML文本的使用者需附上此引用並同時引用FormosanBank。如果有多個與語料庫（XML檔案）相關的引用，這些引用會以「|」分隔符分隔。
* `BibTeX_citation`：對原始來源的BibTeX格式引用。如果有多個與語料庫（XML檔案）相關的引用，這些引用會以「,」分隔符分隔。
* `copyright`：版權或授權訊息（例如：CC BY）。
* `xml:lang`：語言代碼，使用ISO 639-3標準。

可選屬性可能包括：

* `source`：對原始檔案、章節或其他相關細節的描述。如果此檔案包含原始來源的所有內容，則此屬性與citation屬性重複，不會使用。source屬性沒有特定格式；它應包含足夠的訊息，讓使用者能夠將XML中的內容與原始來源對應起來。
* `audio`：關聯語音檔案的名稱。如果音檔已進行分段處理（diarization），且無對應整個XML的單一音檔，則此屬性會設置為“diarized”。
* `glottocode`：指定特定方言時，則使用[Glottolog](https://glottolog.org/)代碼。
* `dialect`：用於標示使用中的臺灣南島語方言名稱。僅在方言名稱對應於42個官方方言之一時才會使用。如需更多資訊，請參見下一單元臺灣南島語方言。

***

### `<S>`、`<W>`和`<M>`元素

* `<S>`：代表一個句子或語句；只能是`<TEXT>`元素的子元素。
* `<W>`：代表一個詞彙；只能是`<S>`元素的子元素。
* `<M>`：代表一個語素；只能是`<W>`元素的子元素。

這三種元素採用（並且需要）的唯一屬性是id屬性。

***

### `<FORM>`元素

在`<S>`、`<W>`和\<M>的最低層級中，必須使用\<FORM>元素來表示文本內容。`<FORM>`元素只能作為`<S>`、`<W>`和`<M>`元素的子元素。`<FORM>`必須出現在階層結構的最低層級，但也可以同時存在於多個層級中：

```
<S id="S14">
    <FORM>tɐrú kə mənaŋorɐ nə...</FORM>
    <W>
        <FORM>tɐrú</FORM>
    </W>
    <W>
        <FORM>kə</FORM>
    </W>
    <W>
        <FORM>mənaŋorɐ</FORM>
    </W>
</S>
```

`<FORM>`元素有一個選擇性的屬性──`kindOf`，該屬性有兩種使用情境：

* 用於表示音韻轉寫，此時屬性值為 "`phono`"。
* 用於標示具有多種書寫系統的語言所使用的書寫系統，書寫系統列表可在此處查詢。

FormosanBank 的 XML 格式確保了語料的全面呈現，既支持詳細分析，也支持高層次探索。

***

### `<AUDIO>`元素

`<AUDIO>`元素將特定音檔片段與XML中的語言元素（如句子、詞彙或語素）連結，確保使用者可以將文本語料與相應的音檔對應起來。

屬性：

* `start`與`end`：當整個 XML 文件與單一大型音訊檔案相關聯時使用。這些屬性表示音檔片段的起始與結束時間（以秒為單位），從檔案的開頭開始計算。
* `file`與`url`：當音檔經過分段處理（即每個元素如句子或詞彙有各自的音檔）時使用。file屬性指定該片段的音檔，url屬性（選擇性）提供觸接該檔案的網絡連結。

使用場景：

1. 單一大型音訊檔案：當單一音檔涵蓋整個XML文件時（在`<TEXT>`標籤的 `audio`屬性中引用），`<AUDIO>`元素將包括start和end屬性，以指示相關片段的時間範圍。

範例：

```
<AUDIO start="10.5" end="12.8"/>
```

2. 分段音訊檔案：如果每個元素（如句子、單詞等）皆有提供單獨的音檔，則 `<TEXT>`標籤的`audio`屬性將設置為"`diarized`"。在這種情況下，`<AUDIO>`元素將使用`file`屬性指示相應的音檔，並可選擇包含url屬性，以提供音檔的網絡連結。

範例：

```
<AUDIO start="0" end="4.23" file="sentence1_audio.mp3" url="https://example.com/audio/sentence1_audio.mp3"/>
```

***

### \<TRANSL>元素

\<TRANSL>元素用於提供語言元素（句子、單詞或語素等）的翻譯。它置放在XML架構的不同層級，以提供適當細緻程度的翻譯。

屬性：

* xml:lang: 翻譯的語言代碼，使用ISO 639-3標準。
* kindOf（選擇性）：指定用來生成翻譯的方法或工具，例如中間語言或翻譯軟體（例如：kindOf="DeepL"）。建議在可行時包含軟體版本，以便進行更完整的記錄。

使用指引：

1. 句子層級翻譯：當放置於\<S>元素內時，\<TRANSL>標籤提供整個句子或語句的翻譯。

範例：

```
<S id="S1">
    <FORM>This is a sentence.</FORM>
    <TRANSL xml:lang="en">This is a sentence.</TRANSL>
    <TRANSL xml:lang="fr" kindOf="manual">Ceci est une phrase.</TRANSL>
</S>
```

2. 詞彙層級翻譯：當放置於\<W>元素內時，\<TRANSL>標籤提供該特定詞彙的翻譯。

範例：

```
<W id="W1">
    <FORM>ʕa</FORM>
    <TRANSL xml:lang="en">I</TRANSL>
</W>
```

3. 語素層級翻譯（Leipzig萊比錫註釋）：\
   對於遵循萊比錫規則的語言學註釋，可在\<M>元素內使用\<TRANSL>元素提供語素層級的註釋。

範例：

```
<W>
    <M>
        <FORM>ʕa</FORM>
        <TRANSL xml:lang="en">1SG</TRANSL>
    </M>
</W>
```

注意：範例中未包含\<W>和\<M>元素的class或subclass屬性，也未包含 \<TRANSL>元素的ver屬性。
