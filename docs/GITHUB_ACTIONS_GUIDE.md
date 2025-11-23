# GitHub Actions自動化ガイド

GitHub Actionsを使って、ナレッジグラフ構築パイプラインを完全自動化する方法の完全ガイド。

## 目次

1. [概要](#概要)
2. [セットアップ手順](#セットアップ手順)
3. [ワークフローの使い方](#ワークフローの使い方)
4. [カスタマイズ](#カスタマイズ)
5. [トラブルシューティング](#トラブルシューティング)
6. [コスト管理](#コスト管理)
7. [セキュリティ](#セキュリティ)

---

## 概要

### できること

GitHub Actionsワークフローにより、以下が自動化されます：

```
トリガー → GitHub Actions実行
    ↓
1. arXiv検索（レビュー論文優先）
2. LLMフィルタリング（Gemini 2.5 Flash）
3. 論文ダウンロード
4. 知識抽出
5. JSON保存
6. GitHubへ自動コミット
    ↓
完成したナレッジグラフがリポジトリに追加
```

### 利点

✅ **完全自動化**: 手動実行不要
✅ **スケジュール実行**: 定期的に新しい知識を収集
✅ **クラウド実行**: ローカルマシン不要
✅ **バージョン管理**: すべての知識グラフをGitで管理
✅ **成果物保存**: JSONファイルを90日間保持
✅ **コスト効率**: Gemini 2.5 Flashは無料枠が大きい

### 使用するLLM

**Gemini 2.5 Flash** を使用します：
- **速度**: 非常に高速
- **コスト**: 無料枠が大きい（月間1500リクエスト）
- **品質**: 知識抽出に十分な性能
- **制限**: レート制限あり（15 RPM、4M TPM）

---

## セットアップ手順

### ステップ1: Gemini API キーの取得

1. **Google AI Studioにアクセス**
   ```
   https://aistudio.google.com/app/apikey
   ```

2. **APIキーを作成**
   - 「Create API key」をクリック
   - 新しいプロジェクトを選択または作成
   - APIキーが生成される（例: `AIzaSy...`）

3. **APIキーをコピー**
   - ⚠️ **重要**: このキーは一度しか表示されません
   - 安全な場所に保存してください

### ステップ2: GitHub Secretsの設定

1. **GitHubリポジトリに移動**
   ```
   https://github.com/YOUR_USERNAME/kg-builder
   ```

2. **Settings → Secrets and variables → Actions**
   - リポジトリページ上部の「Settings」タブ
   - 左サイドバーの「Secrets and variables」→「Actions」

3. **New repository secretをクリック**

4. **シークレットの追加**
   ```
   Name: GEMINI_API_KEY
   Secret: AIzaSy... (ステップ1で取得したAPIキー)
   ```

5. **Add secretをクリック**

✅ これでシークレットが設定されました！

### ステップ3: ワークフローファイルの確認

ワークフローファイルは既に配置されています：
```
.github/workflows/build-knowledge-graph.yml
```

このファイルがリポジトリにコミットされていることを確認：
```bash
git add .github/workflows/build-knowledge-graph.yml
git commit -m "Add GitHub Actions workflow"
git push
```

### ステップ4: 動作確認

1. **GitHubリポジトリの「Actions」タブに移動**

2. **ワークフローが表示されることを確認**
   - 「Build Knowledge Graph」というワークフローがリストに表示される

3. **初回実行（次のセクション参照）**

---

## ワークフローの使い方

### 手動実行

1. **「Actions」タブに移動**
   ```
   https://github.com/YOUR_USERNAME/kg-builder/actions
   ```

2. **「Build Knowledge Graph」ワークフローを選択**

3. **「Run workflow」ボタンをクリック**

4. **パラメータを入力**

   | パラメータ | 説明 | デフォルト |
   |----------|------|-----------|
   | `topic` | 検索トピック | knowledge graph construction |
   | `max_papers` | 処理する論文数 | 5 |
   | `review_only` | レビュー論文のみ | true |
   | `combine` | 統合グラフ作成 | true |
   | `threshold` | 関連性閾値 | 0.7 |

   **例**:
   ```
   topic: graph neural networks
   max_papers: 10
   review_only: true
   combine: true
   threshold: 0.75
   ```

5. **「Run workflow」をクリックして実行開始**

6. **進行状況の確認**
   - ワークフローが開始される
   - 各ステップの進行状況をリアルタイムで確認可能
   - 約10-20分で完了（論文数による）

### スケジュール実行

デフォルトで**毎週月曜日 0:00 UTC**に自動実行されます。

スケジュールを変更する場合：

```yaml
# .github/workflows/build-knowledge-graph.yml
schedule:
  # 毎日午前0時
  - cron: '0 0 * * *'

  # 毎週水曜日と土曜日
  - cron: '0 0 * * 3,6'

  # 毎月1日
  - cron: '0 0 1 * *'
```

**Cron構文リファレンス**:
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
* * * * *
```

### プッシュトリガー（オプション）

特定のファイルが更新されたときに実行するには：

```yaml
# .github/workflows/build-knowledge-graph.yml
on:
  push:
    branches:
      - main
    paths:
      - 'config/topics.txt'  # このファイルが変更されたとき
```

トピックファイルの例（`config/topics.txt`）:
```
knowledge graph construction
graph neural networks
materials science
quantum computing
```

---

## 実行結果の確認

### 1. GitHub UI

**Actionsタブ**:
- ワークフロー実行の一覧
- 各ステップの詳細ログ
- 成功/失敗のステータス

**Summaryページ**:
- 実行サマリー
- 生成されたファイル数
- ファイルサイズ

### 2. 成果物（Artifacts）

**ダウンロード方法**:
1. 完了したワークフローをクリック
2. 下部の「Artifacts」セクション
3. `knowledge-graphs-XXX` をクリックしてダウンロード

**含まれるファイル**:
```
knowledge-graphs-XXX.zip
├── 2301_12345_knowledge_graph.json
├── 2302_67890_knowledge_graph.json
├── ...
├── combined_knowledge_graph.json
└── papers_index.json
```

**保持期間**: 90日間

### 3. 自動コミット

ワークフローが成功すると、自動的にコミット＆プッシュされます：

```
🤖 Auto-build: Add knowledge graphs for 'graph neural networks' (#42)
```

**コミット内容**:
- `data/exports/*.json` - 知識グラフ
- `data/papers/papers_index.json` - 論文インデックス

**PDFは含まれません**（.gitignoreで除外）

### 4. ログの確認

詳細ログもアーティファクトとして保存：
```
pipeline-logs-XXX.zip
└── kg-builder.log
```

**保持期間**: 30日間

---

## カスタマイズ

### デフォルトトピックの変更

スケジュール実行時のデフォルトトピックを変更：

```yaml
# .github/workflows/build-knowledge-graph.yml
- name: Determine topic
  id: topic
  run: |
    if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
      # 手動実行時の処理
      ...
    else:
      # スケジュール実行時のデフォルト設定
      echo "topic=YOUR_TOPIC_HERE" >> $GITHUB_OUTPUT
      echo "max_papers=10" >> $GITHUB_OUTPUT
      echo "review_only=true" >> $GITHUB_OUTPUT
      echo "combine=true" >> $GITHUB_OUTPUT
      echo "threshold=0.75" >> $GITHUB_OUTPUT
    fi
```

### LLMモデルの変更

Geminiの別モデルを使用する場合：

```yaml
# .github/workflows/build-knowledge-graph.yml
- name: Configure environment
  run: |
    cat > .env << EOF
    LLM_PROVIDER=gemini
    GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}
    GEMINI_MODEL=gemini-1.5-pro  # より高性能なモデル
    ...
```

**利用可能なGeminiモデル**:
- `gemini-2.0-flash-exp` - 最速、推奨（デフォルト）
- `gemini-1.5-flash` - 安定版
- `gemini-1.5-pro` - 高品質（コスト高）

### タイムアウトの調整

処理時間が長い場合：

```yaml
jobs:
  build-knowledge-graph:
    timeout-minutes: 180  # 3時間に延長
```

### 成果物の保持期間

```yaml
- name: Upload knowledge graphs
  uses: actions/upload-artifact@v4
  with:
    retention-days: 180  # 180日間に延長
```

### Slack通知の有効化

1. **Slack Webhook URLを取得**
   - Slackワークスペース設定
   - Incoming Webhooksアプリを追加
   - Webhook URLをコピー

2. **GitHub Secretに追加**
   ```
   Name: SLACK_WEBHOOK_URL
   Secret: https://hooks.slack.com/services/XXX/YYY/ZZZ
   ```

3. **ワークフローのコメントアウトを解除**
   ```yaml
   # .github/workflows/build-knowledge-graph.yml
   # 最後のステップのコメントを外す
   - name: Notify Slack
     if: always()
     uses: slackapi/slack-github-action@v1
     with:
       webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
       ...
   ```

---

## トラブルシューティング

### 問題1: ワークフローが表示されない

**症状**: Actionsタブにワークフローが表示されない

**原因**:
- ワークフローファイルがコミットされていない
- YAMLの構文エラー

**解決策**:
```bash
# ファイルの確認
ls -la .github/workflows/build-knowledge-graph.yml

# コミット状況確認
git status

# コミット＆プッシュ
git add .github/workflows/
git commit -m "Add workflow"
git push
```

### 問題2: シークレットエラー

**症状**: `Error: GEMINI_API_KEY is not set`

**原因**: GitHub Secretsが正しく設定されていない

**解決策**:
1. Settings → Secrets and variables → Actions
2. `GEMINI_API_KEY` が存在するか確認
3. 存在しない場合は追加
4. 存在する場合は値を再設定

### 問題3: Gemini APIエラー

**症状**: `403 Forbidden` または `429 Too Many Requests`

**原因**:
- APIキーが無効
- レート制限に到達

**解決策**:

**APIキーの確認**:
```bash
# ローカルでテスト
export GEMINI_API_KEY="your-key"
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp:generateContent?key=${GEMINI_API_KEY}"
```

**レート制限対策**:
- 処理する論文数を減らす（`max_papers: 3`）
- スケジュール間隔を広げる
- 有料プランにアップグレード

### 問題4: パイプラインタイムアウト

**症状**: `Error: The job running on runner Hosted Agent has exceeded the maximum execution time of 120 minutes.`

**原因**: 論文数が多すぎる、またはLLMが遅い

**解決策**:

1. **タイムアウトを延長**:
   ```yaml
   timeout-minutes: 180  # 3時間
   ```

2. **論文数を減らす**:
   ```yaml
   max_papers: 3  # 5 → 3に削減
   ```

3. **より高速なモデル使用**:
   ```yaml
   GEMINI_MODEL=gemini-2.0-flash-exp  # 既にデフォルト
   ```

### 問題5: コミット失敗

**症状**: `Error: refusing to allow a GitHub App to create or update workflow`

**原因**: GitHub Actionsがワークフローファイルを更新しようとしている

**解決策**:
ワークフローファイルは自動コミットから除外されています（正常動作）

### 問題6: 依存関係エラー

**症状**: `ModuleNotFoundError: No module named 'google.generativeai'`

**原因**: 依存関係のインストール失敗

**解決策**:
`pyproject.toml` に `google-generativeai>=0.8.0` が含まれているか確認：

```toml
dependencies = [
    ...
    "google-generativeai>=0.8.0",
    ...
]
```

---

## コスト管理

### Gemini API無料枠

**Gemini 2.5 Flash**:
- **無料枠**: 月間1500リクエスト
- **レート制限**: 15 RPM、4M TPM（トークン/分）

**推定使用量**（論文あたり）:
- エンティティ抽出: 約40リクエスト（チャンク数に依存）
- 関係性抽出: 約40リクエスト
- 関連性フィルタリング: 1リクエスト
- **合計**: 約80-100リクエスト/論文

**月間処理可能論文数**（無料枠内）:
```
1500リクエスト ÷ 100リクエスト/論文 = 約15論文/月
```

**コスト削減策**:
1. **論文数を制限**: `max_papers: 3`
2. **実行頻度を調整**: 週1回 → 月1回
3. **レビュー論文のみ**: `review_only: true`（デフォルト）

### GitHub Actions使用時間

**無料枠**:
- パブリックリポジトリ: **無制限**
- プライベートリポジトリ: 月2000分

**推定使用時間**（5論文）:
- セットアップ: 2分
- パイプライン実行: 8-12分
- 後処理: 1分
- **合計**: 約11-15分/実行

**月間実行回数**（無料枠内、プライベートリポジトリ）:
```
2000分 ÷ 15分/実行 = 約133回/月
```

→ 週1回実行なら十分な余裕

---

## セキュリティ

### APIキーの保護

✅ **推奨**:
- GitHub Secretsを使用（暗号化保存）
- APIキーを直接コードに書かない
- `.env` ファイルを `.gitignore` に追加

❌ **禁止**:
- APIキーをコミットしない
- ログに出力しない
- 公開リポジトリで平文保存しない

### アクセス権限

ワークフローの権限設定（デフォルトで適切）:
```yaml
permissions:
  contents: write  # コミット＆プッシュに必要
```

### セキュリティのベストプラクティス

1. **APIキーの定期ローテーション**
   - 3-6ヶ月ごとに新しいキーを生成
   - 古いキーを無効化

2. **使用量のモニタリング**
   - Google AI Studioでクォータ確認
   - 異常な使用量に注意

3. **リポジトリ権限の制限**
   - 必要最小限のコラボレーターのみ
   - Secretsへのアクセス制限

4. **監査ログの確認**
   - Settings → Actions → General
   - ワークフロー実行履歴を定期確認

---

## 高度な設定

### マトリックス戦略（複数トピック並列実行）

```yaml
jobs:
  build-knowledge-graph:
    strategy:
      matrix:
        topic:
          - 'knowledge graph construction'
          - 'graph neural networks'
          - 'materials science'
    steps:
      - name: Run pipeline
        run: |
          python scripts/build_knowledge_graph.py "${{ matrix.topic }}" \
            --max-papers 5 \
            --review-papers-only
```

### 条件付き実行

```yaml
# mainブランチのみ
jobs:
  build-knowledge-graph:
    if: github.ref == 'refs/heads/main'
```

### 環境変数の集中管理

```yaml
env:
  PYTHON_VERSION: '3.11'
  MAX_PAPERS: 5
  THRESHOLD: 0.7

jobs:
  build-knowledge-graph:
    steps:
      - name: Run pipeline
        run: |
          python scripts/build_knowledge_graph.py "${{ inputs.topic }}" \
            --max-papers ${{ env.MAX_PAPERS }}
```

### キャッシュの活用

```yaml
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

---

## チェックリスト

### 初回セットアップ

- [ ] Gemini API キーを取得
- [ ] GitHub Secretsに `GEMINI_API_KEY` を追加
- [ ] ワークフローファイルをコミット＆プッシュ
- [ ] Actionsタブでワークフローを確認
- [ ] 手動実行でテスト
- [ ] 結果を確認（成果物ダウンロード）

### 定期メンテナンス

- [ ] 月1回: API使用量を確認
- [ ] 3ヶ月ごと: APIキーをローテーション
- [ ] 週1回: ワークフロー実行結果を確認
- [ ] 必要に応じて: トピックやパラメータを調整

---

## まとめ

### ワークフローの流れ

```
1. トリガー
   ├─ 手動実行（任意のトピック）
   ├─ スケジュール（毎週月曜）
   └─ プッシュ（オプション）
      ↓
2. 環境セットアップ
   ├─ Python 3.11
   ├─ 依存関係インストール
   └─ Gemini API設定
      ↓
3. パイプライン実行
   ├─ arXiv検索
   ├─ LLMフィルタリング
   ├─ 論文ダウンロード
   ├─ 知識抽出
   └─ JSON保存
      ↓
4. 結果の処理
   ├─ サマリー生成
   ├─ 成果物アップロード
   └─ GitHubへコミット
      ↓
5. 完了
```

### 推奨設定（コスト最適化）

```yaml
topic: 適宜変更
max_papers: 3-5
review_only: true
combine: true
threshold: 0.7-0.8
schedule: 週1回または月1回
```

### 次のステップ

1. **Neo4jインポート自動化** (オプション):
   - GitHub ActionsからNeo4jへの自動インポート
   - セルフホストランナーの使用

2. **通知の設定**:
   - Slack通知
   - Emailアラート

3. **可視化の追加**:
   - GitHub Pagesで結果を公開
   - レポート生成

---

## 参考リンク

- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **Gemini API Documentation**: https://ai.google.dev/docs
- **Workflow Syntax**: https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions
- **Secrets Management**: https://docs.github.com/en/actions/security-guides/encrypted-secrets

---

**完全自動化されたナレッジグラフ構築の準備完了！** 🎉
