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
- `key_pages`：需要被轉成 PNG 的頁面。
- `upstream_repositories`：文獻或手冊中提到、需要同步到 `upstream/` 的 repo。

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
