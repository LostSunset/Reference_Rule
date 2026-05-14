# Reference Rule Pack

這個資料夾不是專案本體，而是一組可複製到任意專案的參考來源與 upstream 規則。

目標：

- `Reference_sources/` 保存 AI 下載或整理的書籍、期刊、工具使用手冊。
- `upstream/` 保存文獻或手冊中提到的外部程式碼專案，但永遠以唯讀 wrapper 方式管理。
- `docs/development-logs/` 保存開發者日誌與 AI 日誌規則。
- `reference_rule_sync.py` 讓每個專案的 AI 可以自動初始化、驗證、轉換關鍵頁 PNG、同步 upstream repo，並產生追溯 manifest。
- 當文件頁數太多時，同步器依 `image_reading.strategy` 自動選擇全文、分批全文、選擇性轉圖或延後轉圖。

## 快速使用

在任意專案根目錄放入這些項目：

```text
Reference_sources/
upstream/
reference_rule_sync.py
schedule/
```

初始化與檢查：

```bash
python reference_rule_sync.py init --root .
python reference_rule_sync.py validate --root .
```

如果 Windows 上的 `python` 指令被 Microsoft Store alias 攔截，請改用 `py -3`、`python3`，或設定排程範本中的 `REFERENCE_RULE_PYTHON` 環境變數為實際 Python 路徑。

同步全部內容：

```bash
python reference_rule_sync.py sync --root .
```

只同步 upstream：

```bash
python reference_rule_sync.py sync-upstream --root .
```

把 metadata 裡指定的 PDF 關鍵頁和建議的全文閱讀頁轉成 PNG，並補齊 `summary.html`：

```bash
python reference_rule_sync.py render-pages --root .
```

## AI 使用原則

當使用者要求 AI 下載 Books、Journals、Tools_User_Guides 時，AI 必須先閱讀：

- `Reference_sources/README.md`
- `upstream/README.md`
- `docs/development-logs/README.md`
- `Reference_sources/_templates/*.json`

Codex 也必須讀取 `AGENTS.md`，Claude Code 必須讀取 `CLAUDE.md`。兩者都會要求 AI 在非瑣碎變更時建立開發日誌。

AI 必須做到：

1. 依文件類型放入正確分類。
2. 建立或更新 `metadata.json`。
3. 記錄來源 URL、DOI、ISBN、下載日期、hash、授權資訊、使用理由。
4. 如果文件中有公式、表格、流程圖、演算法或關鍵定義，將對應頁面轉成 PNG 存在該來源資料夾的 `key_pages/`。
5. 期刊、書籍、工具文件建議轉成全文圖片閱讀頁，放在各來源資料夾的 `reading_pages/`。
6. 每份期刊、書籍、工具文件都要有 `summary.html`，記錄重點摘要、關鍵頁碼、公式、表格、圖與 upstream 關聯。
7. 如果文件提到可重現研究、官方工具、範例程式、GitHub/GitLab repo，必須把 repo 登記到 metadata 的 `upstream_repositories`，再用同步器放入 `upstream/`。
8. 永遠不要修改 `upstream/**/repo/` 內的檔案。需要改動時，寫在專案自己的 adapter、patch、note 或 fork。

## 建議排程

可依環境選擇一種範本：

- Windows：`schedule/windows-task-reference-rule-sync.ps1`
- Linux/macOS cron：`schedule/crontab.reference-rule-sync.example`
- GitHub Actions：`schedule/github-actions-reference-rule-sync.yml`

排程建議每天或每週執行：

```bash
python reference_rule_sync.py sync --root .
```

## 產出檔

同步器會維護：

- `reference_rule_manifest.json`：所有文獻、hash、關鍵頁、upstream 來源的總追溯表。
- `upstream/repos/<owner>__<repo>/wrapper.json`：單一 upstream repo 的 wrapper metadata。
- `upstream/repos/<owner>__<repo>/README.md`：提醒此 repo 為唯讀 upstream。
