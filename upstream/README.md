# Upstream Rules

`upstream/` 存放外部原始專案的唯讀 wrapper。這些 repo 可能來自書籍、期刊、工具手冊、官方範例或研究專案。

核心規則：

> upstream 進來的形式永遠是 wrapper，專案永遠不能直接修改 upstream repo。

## 目錄格式

```text
upstream/
  README.md
  repos/
    <owner>__<repo>/
      README.md
      wrapper.json
      repo/
```

- `repo/` 是外部 git repository 的 clone。
- `wrapper.json` 記錄 repo URL、來源文獻、同步時間、HEAD commit。
- wrapper 層可以放 notes、patch 說明、adapter 指引。
- `repo/` 內的內容視為唯讀，不能被專案 AI 或開發者直接修改。

## 修改規則

禁止：

- 在 `upstream/**/repo/` 修改檔案。
- 把專案需求直接改進 upstream clone。
- 在 upstream clone 裡 commit 專案特定修補。

允許：

- 在專案自己的 `src/`、`adapters/`、`vendor_adapters/` 等位置寫 wrapper 或 adapter。
- 在 wrapper 層新增 `PATCHES.md` 描述需要的修補。
- fork 原始 repo，並在 metadata 中清楚記錄 fork URL 與原因。
- 提交 issue 或 PR 到原始 upstream，並把連結記錄到 wrapper metadata。

## 自動同步規則

使用根目錄的同步器：

```bash
python reference_rule_sync.py sync-upstream --root .
```

同步器會：

1. 掃描 `Reference_sources/**/metadata.json`。
2. 找出 `upstream_repositories` 或 metadata 裡出現的 GitHub/GitLab repo URL。
3. 將 repo clone 到 `upstream/repos/<owner>__<repo>/repo`。
4. 已存在時執行 fetch/pull fast-forward。
5. 如果 upstream clone 內有未提交修改，跳過更新並回報錯誤，避免覆蓋人為改動。
6. 更新 wrapper metadata 與根目錄 `reference_rule_manifest.json`。

## Git 追蹤建議

在一般專案中，建議追蹤 wrapper metadata，但不要把 clone 下來的 `repo/` 內容提交到專案 git。

`upstream/.gitignore` 預設忽略：

```text
repos/*/repo/
```

這樣每個環境都能用同步器重建 upstream clone，同時保留可審查的來源追溯資料。

如果你的專案必須固定 upstream 程式碼版本，請在 `wrapper.json` 記錄 commit SHA，並由同步器或排程鎖定版本；不要直接修改 clone 內容。

