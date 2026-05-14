# Reference Sources Rules

`Reference_sources/` 是 AI 和專案共同使用的外部參考來源庫。它只存放「可追溯的參考資料」，不存放專案實作程式碼。

## 分類規則

```text
Reference_sources/
  Books/
  Journals/
  Tools_User_Guides/
```

- `Books/`：書籍、教科書、專書、章節 PDF、出版社提供的補充資料。
- `Journals/`：期刊論文、conference paper、preprint、technical report。
- `Tools_User_Guides/`：官方使用手冊、API guide、設備手冊、軟體 manual、規格書。

如果來源同時屬於多種類型，以「使用目的」決定分類。例如一本軟體手冊應放在 `Tools_User_Guides/`，不是 `Books/`。

## 單一來源資料夾格式

每個來源必須是一個資料夾：

```text
Reference_sources/<Category>/<source_id>/
  metadata.json
  source.pdf
  notes.md
  summary.html
  reading_pages/
    page-1.png
    page-2.png
  key_pages/
    page_012.png
    page_137_formula-2-4.png
```

`source_id` 使用小寫 kebab-case，建議格式：

```text
<type>-<first-author-or-org>-<year>-<short-title>
```

範例：

```text
book-goodfellow-2016-deep-learning
journal-vaswani-2017-attention-is-all-you-need
guide-nvidia-2025-cuda-c-programming-guide
```

## metadata.json 必填欄位

每個來源必須有 `metadata.json`：

```json
{
  "id": "journal-vaswani-2017-attention-is-all-you-need",
  "type": "journal",
  "title": "Attention Is All You Need",
  "authors": ["Ashish Vaswani"],
  "year": "2017",
  "source_url": "https://arxiv.org/abs/1706.03762",
  "downloaded_at": "2026-05-14",
  "downloaded_by": "AI",
  "license": "unknown",
  "local_files": ["source.pdf"],
  "hashes": {
    "source.pdf": "sha256:<filled-by-sync-script>"
  },
  "summary_html": "summary.html",
  "image_reading": {
    "enabled": true,
    "directory": "reading_pages",
    "dpi": 180,
    "status": "recommended"
  },
  "key_pages": [
    {
      "page": 3,
      "label": "scaled-dot-product-attention",
      "reason": "Contains the main attention formula.",
      "png": "key_pages/page_003_scaled-dot-product-attention.png"
    }
  ],
  "upstream_repositories": [
    {
      "url": "https://github.com/tensorflow/tensor2tensor",
      "reason": "Code project referenced by the paper."
    }
  ],
  "notes": "Short explanation of why this source was added."
}
```

可從 `Reference_sources/_templates/` 複製對應範本後修改。

### 欄位規範

- `id`：必須等於資料夾名稱。
- `type`：只能是 `book`、`journal`、`tool_user_guide`。
- `title`：原始標題。
- `authors`：作者、組織或維護者。
- `year`：出版、發布或版本年份；未知時填 `unknown`。
- `source_url`：下載頁或官方 landing page，不要只填檔案暫存連結。
- `downloaded_at`：ISO 日期，格式 `YYYY-MM-DD`。
- `downloaded_by`：例如 `AI` 或使用者名稱。
- `license`：授權資訊；未知時填 `unknown`，但不要空白。
- `local_files`：此來源資料夾內保存的原始檔案。
- `hashes`：由同步器填入或更新。
- `summary_html`：此來源的 HTML 重點摘要，預設 `summary.html`。
- `image_reading`：全文轉圖片閱讀設定；期刊、書籍、工具文件建議啟用。
- `key_pages`：需要被轉成 PNG 的頁面。
- `upstream_repositories`：文獻或手冊中提到、需要同步到 `upstream/` 的 repo。

## 全文圖片閱讀規則

期刊、書籍、工具文件建議都轉成圖片閱讀，讓 AI 在跨工具、跨環境時可以用穩定的視覺頁面檢查公式、表格、圖、排版與上下文。

每個來源的全文頁面 PNG 建議放在：

```text
Reference_sources/<Category>/<source_id>/reading_pages/
```

同步器會讀取 metadata 的 `image_reading`：

```json
{
  "image_reading": {
    "enabled": true,
    "directory": "reading_pages",
    "dpi": 180,
    "strategy": "auto",
    "max_full_pages": 120,
    "max_chunked_pages": 500,
    "chunk_size": 100,
    "front_matter_pages": 12,
    "unknown_page_count_strategy": "defer_full",
    "status": "recommended"
  }
}
```

規則：

- `enabled: true` 時，`python reference_rule_sync.py sync --root .` 會嘗試把 PDF 全文轉成 PNG。
- `strategy: auto` 時，同步器會依頁數選擇轉圖方式。
- 若系統沒有 `pdftoppm` 或 `mutool`，同步器會保留 warning，不中斷其他同步。
- 大型書籍可以先只轉 `key_pages/`；若暫時不轉全文，必須把 `image_reading.status` 寫成 `deferred`，並在 `notes` 說明原因。
- `reading_pages/` 是給 AI 閱讀用的頁面影像，不取代原始 PDF。

### 頁數太多時的轉圖策略

AI 與同步器必須先判斷 PDF 頁數，再決定如何轉成圖片：

| 頁數 | 預設策略 | 輸出 |
| --- | --- | --- |
| `1-120` 頁 | `full` | 全文一次轉成 `reading_pages/` |
| `121-500` 頁 | `chunked_full` | 每 `100` 頁分批轉成 `reading_pages/` |
| `501+` 頁 | `selective` | 只轉前 `12` 頁與 metadata 裡的 `key_pages` |
| 無法判斷頁數 | `deferred` | 不做全文轉圖，只保留 warning 並依 `key_pages` 規則處理 |

可在 metadata 中調整門檻：

```json
{
  "image_reading": {
    "strategy": "auto",
    "max_full_pages": 120,
    "max_chunked_pages": 500,
    "chunk_size": 100,
    "front_matter_pages": 12,
    "unknown_page_count_strategy": "defer_full"
  }
}
```

策略說明：

- `full`：強制全文轉圖，適合短文件。
- `chunked_full`：強制分批全文轉圖，適合中型文件或避免單次命令太重。
- `selective`：只轉封面、目錄、前置頁與 `key_pages`，適合大型書籍或超長手冊。
- `deferred`：暫緩全文轉圖，但仍應補 `summary.html` 和 `key_pages`。
- `auto`：由同步器依上表自動選擇。

## HTML 重點摘要規則

每個期刊、書籍、工具文件都必須有一個 HTML 重點摘要：

```text
Reference_sources/<Category>/<source_id>/summary.html
```

同步器會在缺少 `summary.html` 時自動建立摘要模板。AI 新增或閱讀來源後，應把模板補成可用摘要，至少包含：

- 這份來源要解決的問題。
- 專案應該採用的重點結論。
- 重要公式、表格、圖與其頁碼。
- 與程式碼、工具、API、資料集、upstream repo 的關聯。
- 使用限制、授權或可信度注意事項。

HTML 摘要應該保持可離線閱讀，不依賴外部 CSS 或 JavaScript。

## 關鍵頁 PNG 規則

當 AI 需要引用或檢查下列內容時，必須把頁面轉成 PNG：

- 公式與推導。
- 重要表格。
- 演算法 pseudo-code。
- 架構圖、流程圖、系統圖。
- 實驗設定、benchmark 設定。
- API 行為定義或參數表。

PNG 必須放在來源自己的 `key_pages/`：

```text
Reference_sources/<Category>/<source_id>/key_pages/
```

命名格式：

```text
page_<page-number-3-digits>_<short-label>.png
```

範例：

```text
page_042_formula-3-7.png
page_118_algorithm-training-loop.png
```

頁碼以 PDF 閱讀器顯示的頁碼為準；如果文件內部頁碼不同，寫在 `reason` 中說明。

## 追溯規則

任何 AI 新增來源時都必須回答這四件事，並寫入 metadata 或 notes：

1. 來源從哪裡來。
2. 為什麼這個專案需要它。
3. 哪些頁面會被用來查公式、表格或規則。
4. 是否提到外部程式碼 repo、工具或資料集。

同步器會把所有 metadata 彙整到根目錄的 `reference_rule_manifest.json`。

## 禁止事項

- 不要把未分類檔案直接丟在 `Books/`、`Journals/`、`Tools_User_Guides/` 根層。
- 不要只存 PDF 而沒有 `metadata.json`。
- 不要用 `paper1.pdf`、`book-final.pdf` 這類無法追溯的名稱。
- 不要把 upstream repo 的程式碼放進 `Reference_sources/`。
- 不要把 AI 產生的專案程式碼放進這裡。
