# ナレッジグラフ構築パイプライン完全ガイド

トピックから完成したJSONナレッジグラフまで、ワンステップで実行できる完全自動パイプラインの使用ガイド。

## 目次

1. [概要](#概要)
2. [クイックスタート](#クイックスタート)
3. [パイプラインの流れ](#パイプラインの流れ)
4. [各ステップの詳細](#各ステップの詳細)
5. [レビュー論文の優先](#レビュー論文の優先)
6. [実行例](#実行例)
7. [出力ファイル](#出力ファイル)
8. [トラブルシューティング](#トラブルシューティング)

---

## 概要

### パイプラインとは

`build_knowledge_graph.py` は、研究トピックを入力するだけで、論文の検索からナレッジグラフのJSON保存まで、すべてを自動で実行するエンドツーエンドのパイプラインです。

### できること

✅ **ワンコマンドで完了**
```bash
uv run python scripts/build_knowledge_graph.py "knowledge graph construction"
```

これだけで：
1. arXivで関連論文を検索
2. LLMで論文の関連性を評価
3. 関連性の高い論文をダウンロード
4. 各論文から知識を抽出
5. JSONファイルとして保存
6. 論文インデックスを更新

### 特徴

- 🎯 **レビュー論文の優先**: 確立された知識を優先的に収集
- 🤖 **LLMによる品質フィルタリング**: 関連性の低い論文を自動除外
- 📊 **詳細な進捗表示**: 各ステップの進行状況をリアルタイム表示
- 💾 **自動保存**: 個別JSONと統合JSONを自動生成
- 🔄 **再開可能**: 各ステップが独立しているため、エラー時も再開可能

---

## クイックスタート

### 必要な準備

```bash
# 1. Neo4jを起動（JSONのみなら不要だが、後で使うため推奨）
docker-compose up -d neo4j

# 2. Ollamaを起動（ローカルLLM）
ollama pull llama3.1:8b

# 3. 環境変数を確認
cat .env | grep NEO4J_PASSWORD
```

### 基本的な実行

```bash
# トピックを指定して実行（デフォルト: 5論文、レビュー論文優先）
uv run python scripts/build_knowledge_graph.py "knowledge graph construction"
```

**これだけです！** 後は自動で実行されます。

### 実行中の画面

```
================================================================================
Knowledge Graph Builder - End-to-End Pipeline
================================================================================
Topic: knowledge graph construction
Max papers: 5
Relevance threshold: 0.7
Mode: Prefer review/survey papers
Combined graph: False

================================================================================
Step 1/6: Search arXiv
Description: Searching for papers on: knowledge graph construction
================================================================================
  Search query: knowledge graph construction (review OR survey OR overview)
  Priority: Review/Survey papers
✓ Found 47 papers

================================================================================
Step 2/6: Filter by Relevance
Description: Using LLM to assess relevance to: knowledge graph construction
================================================================================
  [1/47] Assessing: Knowledge Graphs: Opportunities and Challenges...
    Score: 0.92 - Highly relevant review paper covering knowledge graph cons...
    ✓ Selected
  [2/47] Assessing: A Survey on Knowledge Graph Construction...
    Score: 0.88 - Comprehensive survey on construction methods...
    Review paper boost: 0.85 → 0.88
    ✓ Selected
  ...
✓ Selected 5 papers (threshold: 0.7)

================================================================================
Step 3/6: Download Papers
Description: Downloading 5 papers
================================================================================
  [1/5] Downloading: Knowledge Graphs: Opportunities and Challenges...
    ✓ Saved to: 2301_12345.pdf
  ...
✓ Downloaded 5 papers

================================================================================
Step 4/6: Extract Knowledge
Description: Extracting entities and relationships from 5 papers
================================================================================
  [1/5] Processing: 2301_12345.pdf
    Extracting text from PDF...
      Extracted 45 text chunks
    Extracting entities...
      Processed 45/45 chunks
      Found 127 unique entities (from 342 total)
    Extracting relationships...
      Processed 45/45 chunks
      Found 189 unique relationships (from 456 total)
    ✓ Extracted 127 entities, 189 relationships
  ...
✓ Processed 5 papers, extracted 542 entities, 831 relationships

================================================================================
Step 5/6: Save JSON Files
Description: Saving 5 knowledge graphs
================================================================================
  [1/5] Saved: 2301_12345_knowledge_graph.json
  ...
✓ Saved 5 JSON files

================================================================================
Step 6/6: Update Index
Description: Updating papers_index.json
================================================================================
✓ Updated index: 5 total papers

================================================================================
Pipeline Summary
================================================================================
Total time: 487.3 seconds (8.1 minutes)

Papers:
  Searched:    47
  Filtered:    5
  Downloaded:  5
  Processed:   5

Knowledge Extraction:
  Total entities:      542
  Total relationships: 831

Output:
  JSON files created: 5

Files saved to:
  Papers:  data/papers/
  Exports: data/exports/

================================================================================

✓ Pipeline completed successfully!

Next steps:
  - Review JSON files in data/exports/
  - Import to Neo4j: python scripts/import_to_neo4j.py data/exports/
  - Explore in browser: http://localhost:7474
```

---

## パイプラインの流れ

### 全体フロー図

```
[トピック入力]
    ↓
┌─────────────────────────────────────────────┐
│ Step 1: arXiv検索                            │
│  - クエリ構築（レビュー論文優先）              │
│  - arXiv APIで検索                           │
│  - 結果: 候補論文リスト                       │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Step 2: LLMフィルタリング                     │
│  - 各論文の関連性をLLMで評価                  │
│  - レビュー論文にボーナススコア               │
│  - 閾値以上の論文を選択                       │
│  - 結果: 選定された論文リスト                 │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Step 3: 論文ダウンロード                      │
│  - arXivからPDFをダウンロード                 │
│  - data/papers/に保存                        │
│  - 結果: PDFファイル群                        │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Step 4: 知識抽出                             │
│  - PDFからテキスト抽出                        │
│  - チャンクに分割                            │
│  - LLMでエンティティ抽出                      │
│  - LLMで関係性抽出                           │
│  - 重複除去                                  │
│  - 結果: ナレッジグラフ（メモリ内）            │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Step 5: JSON保存                             │
│  - 各論文のナレッジグラフをJSON化              │
│  - data/exports/に保存                       │
│  - （オプション）統合グラフ作成               │
│  - 結果: JSONファイル群                       │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Step 6: インデックス更新                      │
│  - papers_index.jsonに論文情報追加            │
│  - メタデータ更新                            │
│  - 結果: 更新されたインデックス               │
└─────────────────────────────────────────────┘
    ↓
[完成したJSONナレッジグラフ]
```

### 処理時間の目安

| ステップ | 1論文あたり | 5論文の場合 |
|---------|-----------|-----------|
| Step 1: 検索 | - | 5-10秒 |
| Step 2: フィルタリング | 3-5秒 | 15-25秒 |
| Step 3: ダウンロード | 2-3秒 | 10-15秒 |
| Step 4: 知識抽出 | 60-120秒 | 5-10分 |
| Step 5: JSON保存 | 1秒 | 5秒 |
| Step 6: インデックス | - | 1秒 |
| **合計** | **約1-2分** | **約6-11分** |

※ Ollama使用時。LLMの速度に依存します。

---

## 各ステップの詳細

### Step 1: arXiv検索

**目的**: トピックに関連する論文をarXivから検索する

**処理内容**:
1. 検索クエリの構築
   - 通常モード: トピックそのまま
   - レビュー優先: `(topic) (review OR survey OR overview)`
   - レビューのみ: `(topic) AND (ti:"review" OR ti:"survey")`

2. arXiv APIで検索
   - 最大結果数: `max_papers × 3`（フィルタリングのため多めに取得）
   - ソート: 関連性順

3. 論文情報の取得
   - タイトル、著者、要約、PDF URL、arXiv ID

**出力**:
- `List[ArxivPaper]`: 候補論文のリスト

**例**:
```
Search query: knowledge graph construction (review OR survey OR overview)
Priority: Review/Survey papers
✓ Found 47 papers
```

---

### Step 2: LLMフィルタリング

**目的**: LLMを使って論文の関連性を評価し、質の高い論文を選定する

**処理内容**:
1. 各論文について：
   - タイトルと要約をLLMに送信
   - トピックとの関連性を0.0-1.0でスコアリング
   - 評価理由も取得

2. レビュー論文のブースト（`prefer_reviews=True`の場合）
   - タイトルまたは要約に review/survey/overview が含まれる
   - スコアを15%増加（最大1.0）
   - 例: 0.75 → 0.86

3. フィルタリング
   - スコアが閾値以上の論文を選択
   - デフォルト閾値: 0.7

4. 上位N件を選択
   - スコア順にソート
   - `max_papers` 件を選択

**出力**:
- `List[(paper, score, reasoning)]`: 選定された論文と評価

**例**:
```
[2/47] Assessing: A Survey on Knowledge Graph Construction...
  Score: 0.85 - Comprehensive survey covering construction methods
  Review paper boost: 0.85 → 0.98
  ✓ Selected
```

**LLMプロンプト例**:
```
Assess the relevance of this paper to the topic "knowledge graph construction".

Paper Title: A Survey on Knowledge Graph Construction
Paper Abstract: This survey provides a comprehensive overview...

Rate from 0.0 to 1.0 and provide reasoning.
```

---

### Step 3: 論文ダウンロード

**目的**: 選定された論文のPDFをダウンロードする

**処理内容**:
1. 各論文について：
   - arXiv URLからPDFをダウンロード
   - `data/papers/` に保存
   - ファイル名: `{arxiv_id}.pdf`（例: `2301_12345.pdf`）

2. レート制限
   - ダウンロード間隔: 1秒
   - arXivの利用規約を遵守

3. エラーハンドリング
   - ダウンロード失敗時はスキップ
   - 次の論文に継続

**出力**:
- `List[Path]`: ダウンロードされたPDFのパスリスト

**例**:
```
[3/5] Downloading: Knowledge Graph Embedding: A Survey...
  ✓ Saved to: 2002_00819.pdf
```

**保存場所**:
```
data/papers/
├── 2301_12345.pdf
├── 2302_67890.pdf
├── 2303_11111.pdf
└── papers_index.json
```

---

### Step 4: 知識抽出

**目的**: PDFから科学的知識（エンティティと関係性）を抽出する

**処理内容**:

#### 4-1. PDFテキスト抽出
```python
PDFExtractor(pdf_path)
  ↓
extract_metadata()  # タイトル、著者、ページ数
  ↓
extract_chunks()    # 2000文字チャンク、200文字オーバーラップ
```

#### 4-2. エンティティ抽出
各チャンクについて：
```python
LLM → EntityExtractor
  ↓
[
  {"name": "knowledge graph", "type": "method", "confidence": 0.95},
  {"name": "graph neural network", "type": "method", "confidence": 0.88},
  {"name": "RDF", "type": "material", "confidence": 0.92},
  ...
]
```

**エンティティタイプ**:
- `method`: 手法、アルゴリズム、技術
- `material`: 材料、データ、リソース
- `phenomenon`: 現象、効果、パターン
- `theory`: 理論、モデル、フレームワーク
- `measurement`: 指標、測定値、評価方法
- `application`: 応用、ユースケース

#### 4-3. 関係性抽出
各チャンクについて：
```python
LLM → RelationshipExtractor
  ↓
[
  {"source": "GNN", "target": "knowledge graph", "type": "USES", "confidence": 0.9},
  {"source": "TransE", "target": "embedding", "type": "IS_A", "confidence": 0.85},
  ...
]
```

**関係性タイプ**:
- `IS_A`: 分類・継承関係
- `PART_OF`: 構成要素
- `USES`: 利用・適用
- `ENABLES`: 実現・可能化
- `MEASURES`: 測定・評価
- `APPLIES_TO`: 適用対象
- `BASED_ON`: 基盤・ベース
- `RELATED_TO`: その他の関連

#### 4-4. 重複除去
```python
# エンティティの重複除去
"Knowledge Graph" と "knowledge graph" → 統合
高い信頼度のバージョンを保持

# 関係性の重複除去
(GNN, uses, KG) の重複 → 最高信頼度を保持
```

**出力**:
- ナレッジグラフ辞書（メモリ内）

**例**:
```
[1/5] Processing: 2301_12345.pdf
  Extracting text from PDF...
    Extracted 45 text chunks
  Extracting entities...
    Processed 5/45 chunks
    Processed 10/45 chunks
    ...
    Found 127 unique entities (from 342 total)
  Extracting relationships...
    Found 189 unique relationships (from 456 total)
  ✓ Extracted 127 entities, 189 relationships
```

**処理時間**: 1論文あたり1-2分（LLMの速度に依存）

---

### Step 5: JSON保存

**目的**: 抽出されたナレッジグラフをJSON形式で保存する

**処理内容**:

#### 5-1. 個別JSONファイル作成
各論文について：
```json
{
  "metadata": {
    "source_file": "2301_12345.pdf",
    "title": "Knowledge Graphs: A Survey",
    "authors": ["John Doe", "Jane Smith"],
    "arxiv_id": "2301.12345",
    "extraction_date": "2025-11-23T10:30:00",
    "num_pages": 35
  },
  "entities": [
    {
      "name": "knowledge graph",
      "type": "method",
      "description": "Graph-structured knowledge base",
      "confidence": 0.95
    },
    ...
  ],
  "relationships": [
    {
      "source": "GNN",
      "target": "knowledge graph",
      "type": "USES",
      "confidence": 0.9,
      "context": "GNNs are widely used for knowledge graph completion"
    },
    ...
  ],
  "statistics": {
    "num_entities": 127,
    "num_relationships": 189,
    "num_chunks_processed": 45
  }
}
```

#### 5-2. 統合グラフ作成（`--combine`オプション使用時）
全論文のエンティティと関係性を統合：
```json
{
  "metadata": {
    "description": "Combined graph from 5 papers on: knowledge graph",
    "num_papers": 5,
    "papers": [
      {"source_file": "2301_12345.pdf", "title": "..."},
      ...
    ]
  },
  "entities": [...],  // 全論文のエンティティ（重複除去済み）
  "relationships": [...],  // 全論文の関係性（重複除去済み）
  "statistics": {
    "num_papers": 5,
    "num_entities": 542,
    "num_relationships": 831
  }
}
```

**出力ファイル**:
```
data/exports/
├── 2301_12345_knowledge_graph.json
├── 2302_67890_knowledge_graph.json
├── 2303_11111_knowledge_graph.json
├── 2304_22222_knowledge_graph.json
├── 2305_33333_knowledge_graph.json
└── combined_knowledge_graph.json  # --combine使用時のみ
```

**例**:
```
[1/5] Saved: 2301_12345_knowledge_graph.json
[2/5] Saved: 2302_67890_knowledge_graph.json
...
Saved combined graph: combined_knowledge_graph.json
✓ Saved 6 JSON files
```

---

### Step 6: インデックス更新

**目的**: 処理済み論文のメタデータをインデックスに記録する

**処理内容**:

#### 6-1. インデックス読み込み
`data/papers/papers_index.json` を読み込み（なければ新規作成）

#### 6-2. 新規論文の追加
```json
{
  "papers": [
    {
      "source_file": "2301_12345.pdf",
      "title": "Knowledge Graphs: A Survey",
      "authors": ["John Doe", "Jane Smith"],
      "arxiv_id": "2301.12345",
      "num_entities": 127,
      "num_relationships": 189,
      "extraction_date": "2025-11-23T10:30:00"
    },
    ...
  ],
  "last_updated": "2025-11-23T10:35:00",
  "total_papers": 5
}
```

#### 6-3. 保存
更新されたインデックスを保存

**出力**:
- `data/papers/papers_index.json`

**例**:
```
✓ Updated index: 5 total papers
```

**用途**:
- どの論文を処理済みか追跡
- GitHubで共有（PDFなしでもメタデータ確認可能）
- 重複ダウンロード防止

---

## レビュー論文の優先

### なぜレビュー論文を優先するか？

レビュー論文（Review/Survey論文）は：
- ✅ 分野の確立された知識を体系的にまとめている
- ✅ 多数の先行研究を包括的にカバー
- ✅ 信頼性の高い情報源
- ✅ 基礎から応用まで幅広くカバー
- ✅ 最新の研究動向も含む

→ **確かな知識ベースを構築するのに最適**

### モード選択

#### 1. レビュー論文優先モード（デフォルト）
```bash
uv run python scripts/build_knowledge_graph.py "topic"
```

**動作**:
- 検索クエリに review/survey/overview を追加
- レビュー論文のスコアを15%ブースト
- レビューと通常論文の両方を含む

**適用場面**: ほとんどのケース（バランスの取れた選択）

#### 2. レビュー論文のみモード
```bash
uv run python scripts/build_knowledge_graph.py "topic" --review-papers-only
```

**動作**:
- タイトルまたは要約に "review" または "survey" を含む論文のみ
- 通常論文は完全に除外

**適用場面**:
- 確立された知識のみが必要
- 新しい分野の基礎理解
- 教育用途

#### 3. 全論文モード
```bash
uv run python scripts/build_knowledge_graph.py "topic" --no-review-preference
```

**動作**:
- レビュー論文の優遇なし
- すべての論文を平等に評価

**適用場面**:
- 最新の研究成果が必要
- 特定の手法の実装例が必要
- レビュー論文が少ない新興分野

### レビュー論文の判定ロジック

```python
def _is_review_paper(paper):
    review_keywords = ["review", "survey", "overview", "tutorial", "perspective"]
    title_lower = paper.title.lower()
    summary_lower = paper.summary.lower()

    return any(
        keyword in title_lower or keyword in summary_lower
        for keyword in review_keywords
    )
```

### スコアブースト例

```
通常論文:
  LLMスコア: 0.75
  最終スコア: 0.75

レビュー論文（prefer_reviews=True）:
  LLMスコア: 0.75
  ブースト: ×1.15
  最終スコア: 0.86 (min(0.75 × 1.15, 1.0))
```

---

## 実行例

### 例1: 基本的な実行

```bash
uv run python scripts/build_knowledge_graph.py "knowledge graph construction"
```

**結果**:
- 5論文のレビュー優先選択
- 個別JSON × 5
- 処理時間: 約6-8分

### 例2: 論文数を増やす

```bash
uv run python scripts/build_knowledge_graph.py "graph neural networks" --max-papers 10
```

**結果**:
- 10論文のレビュー優先選択
- 個別JSON × 10
- 処理時間: 約12-16分

### 例3: レビュー論文のみ

```bash
uv run python scripts/build_knowledge_graph.py "materials science" --review-papers-only
```

**結果**:
- Review/Survey論文のみ5件
- より確立された知識
- 信頼性の高いナレッジグラフ

### 例4: 統合グラフ作成

```bash
uv run python scripts/build_knowledge_graph.py "transformers" --max-papers 8 --combine
```

**結果**:
- 個別JSON × 8
- combined_knowledge_graph.json × 1
- 全論文の知識が統合されたグラフ

### 例5: 高品質フィルタリング

```bash
uv run python scripts/build_knowledge_graph.py "quantum computing" --threshold 0.85 --max-papers 3
```

**結果**:
- 非常に関連性の高い論文のみ3件
- 高品質だが少数

### 例6: サイレントモード

```bash
uv run python scripts/build_knowledge_graph.py "deep learning" --quiet
```

**結果**:
- 詳細なログを抑制
- 主要な情報のみ表示
- バックグラウンド実行に適している

### 例7: 完全なワークフロー

```bash
# 1. パイプライン実行
uv run python scripts/build_knowledge_graph.py "knowledge graphs" --max-papers 5 --combine

# 2. Neo4jにインポート
uv run python scripts/import_to_neo4j.py data/exports/

# 3. 統計確認
uv run python scripts/neo4j_manager.py stats

# 4. コンセプト検索
uv run python scripts/neo4j_manager.py search "graph"

# 5. Neo4jブラウザで可視化
open http://localhost:7474
```

---

## 出力ファイル

### ディレクトリ構造

```
kg-builder/
├── data/
│   ├── papers/              # ダウンロードしたPDF（Gitにコミットされない）
│   │   ├── 2301_12345.pdf
│   │   ├── 2302_67890.pdf
│   │   ├── ...
│   │   └── papers_index.json  # メタデータ（Gitにコミットされる）
│   │
│   └── exports/             # 知識グラフJSON（Gitにコミットされる）
│       ├── 2301_12345_knowledge_graph.json
│       ├── 2302_67890_knowledge_graph.json
│       ├── ...
│       └── combined_knowledge_graph.json
```

### JSONファイルの構造

#### 個別ナレッジグラフ

`data/exports/2301_12345_knowledge_graph.json`:
```json
{
  "metadata": {
    "source_file": "2301_12345.pdf",
    "title": "Knowledge Graphs: Opportunities and Challenges",
    "authors": ["John Doe", "Jane Smith"],
    "arxiv_id": "2301.12345",
    "num_pages": 35,
    "extraction_date": "2025-11-23T10:30:00"
  },
  "entities": [
    {
      "name": "knowledge graph",
      "type": "method",
      "description": "A graph-structured knowledge base that stores facts",
      "confidence": 0.95
    },
    {
      "name": "graph neural network",
      "type": "method",
      "description": "Neural network designed for graph-structured data",
      "confidence": 0.92
    },
    {
      "name": "RDF",
      "type": "material",
      "description": "Resource Description Framework for knowledge representation",
      "confidence": 0.88
    }
  ],
  "relationships": [
    {
      "source": "graph neural network",
      "target": "knowledge graph",
      "type": "USES",
      "confidence": 0.90,
      "context": "GNNs are widely used for knowledge graph completion tasks"
    },
    {
      "source": "RDF",
      "target": "knowledge graph",
      "type": "PART_OF",
      "confidence": 0.85,
      "context": "RDF is a common format for representing knowledge graphs"
    }
  ],
  "statistics": {
    "num_entities": 127,
    "num_relationships": 189,
    "num_chunks_processed": 45
  }
}
```

#### 統合ナレッジグラフ

`data/exports/combined_knowledge_graph.json`:
```json
{
  "metadata": {
    "creation_date": "2025-11-23T10:35:00",
    "description": "Combined knowledge graph from 5 papers on: knowledge graphs",
    "num_papers": 5,
    "papers": [
      {
        "source_file": "2301_12345.pdf",
        "title": "Knowledge Graphs: Opportunities and Challenges",
        "authors": ["John Doe", "Jane Smith"]
      },
      ...
    ]
  },
  "entities": [
    // 全論文からの統合エンティティ（重複除去済み）
  ],
  "relationships": [
    // 全論文からの統合関係性（重複除去済み）
  ],
  "statistics": {
    "num_papers": 5,
    "num_entities": 542,
    "num_relationships": 831
  }
}
```

#### 論文インデックス

`data/papers/papers_index.json`:
```json
{
  "papers": [
    {
      "source_file": "2301_12345.pdf",
      "title": "Knowledge Graphs: Opportunities and Challenges",
      "authors": ["John Doe", "Jane Smith"],
      "arxiv_id": "2301.12345",
      "num_entities": 127,
      "num_relationships": 189,
      "extraction_date": "2025-11-23T10:30:00"
    },
    ...
  ],
  "last_updated": "2025-11-23T10:35:00",
  "total_papers": 5
}
```

### GitHubでの共有

**.gitignore設定**:
```gitignore
# PDFは除外（ローカルのみ）
data/papers/*.pdf

# JSONは含める（共有）
!data/papers/papers_index.json
!data/exports/*.json
```

**メリット**:
- ✅ 著作権の問題なし（PDFは共有しない）
- ✅ ナレッジグラフは共有可能
- ✅ メタデータで論文を追跡可能
- ✅ 他のユーザーが同じ論文をダウンロードして再現可能

---

## トラブルシューティング

### 問題1: 論文が見つからない

**症状**:
```
✓ Found 0 papers
✗ No papers found. Try a different query.
```

**原因**:
- 検索クエリが厳しすぎる
- レビュー論文のみモードで該当論文がない
- arXivに該当論文がない

**解決策**:
```bash
# 1. レビュー論文優先を解除
uv run python scripts/build_knowledge_graph.py "topic" --no-review-preference

# 2. より一般的なクエリを使用
uv run python scripts/build_knowledge_graph.py "graph neural networks"  # "GNN"より広い

# 3. カテゴリで検索
uv run python scripts/build_knowledge_graph.py "cat:cs.AI machine learning"
```

### 問題2: 関連性フィルタで全て除外される

**症状**:
```
✓ Found 47 papers
✗ No papers passed the relevance threshold (0.7)
```

**原因**:
- 閾値が高すぎる
- トピックとarXiv論文のミスマッチ

**解決策**:
```bash
# 1. 閾値を下げる
uv run python scripts/build_knowledge_graph.py "topic" --threshold 0.6

# 2. より具体的なトピックを指定
uv run python scripts/build_knowledge_graph.py "knowledge graph embedding methods"

# 3. 検索数を増やす
uv run python scripts/build_knowledge_graph.py "topic" --max-papers 10
```

### 問題3: ダウンロードエラー

**症状**:
```
[1/5] Downloading: Paper Title...
  ✗ Error: HTTP 403 Forbidden
```

**原因**:
- arXivのレート制限
- ネットワーク問題

**解決策**:
```bash
# 1. 少し待ってから再実行
sleep 60
uv run python scripts/build_knowledge_graph.py "topic"

# 2. 論文数を減らす
uv run python scripts/build_knowledge_graph.py "topic" --max-papers 3

# 3. プロキシ設定を確認
export HTTP_PROXY=your_proxy
```

### 問題4: LLMエラー

**症状**:
```
Error: Failed to connect to Ollama
```

**原因**:
- Ollamaが起動していない
- モデルがダウンロードされていない

**解決策**:
```bash
# 1. Ollama起動確認
ollama list

# 2. モデルダウンロード
ollama pull llama3.1:8b

# 3. Ollama起動
ollama serve

# 4. 接続確認
curl http://localhost:11434/api/tags
```

### 問題5: 知識抽出が遅い

**症状**:
- 1論文の処理に10分以上かかる

**原因**:
- LLMが遅い（CPUモード）
- 論文のページ数が多い

**解決策**:
```bash
# 1. より高速なモデルを使用
# .envで設定
OLLAMA_MODEL=mistral:7b  # llama3.1:8bより高速

# 2. GPU使用を確認
# .envで設定
OLLAMA_NUM_GPU=1  # 0ならCPUモード

# 3. OpenAI APIを使用（有料だが高速）
# .envで設定
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
```

### 問題6: メモリ不足

**症状**:
```
MemoryError: Unable to allocate array
```

**原因**:
- 大量の論文を一度に処理
- エンベディングモデルのメモリ使用

**解決策**:
```bash
# 1. 論文数を減らす
uv run python scripts/build_knowledge_graph.py "topic" --max-papers 3

# 2. バッチ処理
uv run python scripts/build_knowledge_graph.py "topic part1" --max-papers 5
uv run python scripts/build_knowledge_graph.py "topic part2" --max-papers 5

# 3. CPUモードを使用（GPUメモリ不足の場合）
# .envで設定
OLLAMA_NUM_GPU=0
EMBEDDING_DEVICE=cpu
```

### 問題7: JSONエンコードエラー

**症状**:
```
UnicodeEncodeError: 'ascii' codec can't encode character
```

**原因**:
- 特殊文字を含む論文タイトルや著者名

**解決策**:
- スクリプトは `ensure_ascii=False` を使用しているため、通常は発生しない
- 発生した場合は、該当論文をスキップして再実行

### 問題8: ディスク容量不足

**症状**:
```
OSError: [Errno 28] No space left on device
```

**原因**:
- PDFファイルの蓄積

**解決策**:
```bash
# 1. 不要なPDFを削除
rm data/papers/*.pdf
# ※ papers_index.jsonは削除しない

# 2. ディスク使用量確認
du -sh data/papers/
du -sh data/exports/

# 3. 古い論文を別の場所に移動
mkdir ~/archive
mv data/papers/old_*.pdf ~/archive/
```

---

## 次のステップ

パイプライン実行後：

### 1. JSONファイルの確認
```bash
# ファイルリスト
ls -lh data/exports/

# 内容確認
cat data/exports/2301_12345_knowledge_graph.json | jq '.statistics'
```

### 2. Neo4jにインポート
```bash
# インポート
uv run python scripts/import_to_neo4j.py data/exports/

# 統計確認
uv run python scripts/neo4j_manager.py stats
```

### 3. Neo4jブラウザで可視化
```bash
# ブラウザを開く
open http://localhost:7474

# Cypherクエリ例
MATCH (c:Concept)-[r]->(t:Concept)
RETURN c, r, t
LIMIT 50
```

### 4. GitHubにコミット
```bash
# 追加（PDFは除外される）
git add data/papers/papers_index.json
git add data/exports/*.json

# コミット
git commit -m "Add knowledge graphs on [topic]"

# プッシュ
git push
```

### 5. 追加の論文処理
```bash
# 別のトピックで追加実行
uv run python scripts/build_knowledge_graph.py "another topic" --max-papers 5

# 既存のナレッジグラフと統合（Neo4j上で）
uv run python scripts/import_to_neo4j.py data/exports/
```

---

## まとめ

### パイプラインの利点

✅ **ワンコマンド実行**: トピック入力だけで完全自動化
✅ **レビュー論文優先**: 確立された知識を効率的に収集
✅ **詳細な進捗表示**: 各ステップの進行状況を可視化
✅ **エラー耐性**: 一部の論文が失敗しても継続
✅ **JSON保存**: 移植性の高いフォーマット
✅ **GitHub連携**: PDFは除外、知識は共有

### 推奨ワークフロー

```bash
# 1. 新しいトピックの知識収集
uv run python scripts/build_knowledge_graph.py "your topic" --max-papers 5 --review-papers-only

# 2. Neo4jにインポート
uv run python scripts/import_to_neo4j.py data/exports/

# 3. 分析と可視化
uv run python scripts/neo4j_manager.py stats
open http://localhost:7474

# 4. 結果をGitHubに共有
git add data/papers/papers_index.json data/exports/
git commit -m "Add knowledge graphs on your topic"
git push
```

### さらに詳しく

- **Neo4j統合**: [Neo4j Guide](NEO4J_GUIDE.md)
- **arXiv検索**: [Search Guide](SEARCH_GUIDE.md)
- **Ollama設定**: [Ollama Guide](OLLAMA_GUIDE.md)
- **プロジェクト計画**: [Strategic Plan](../STRATEGIC_PLAN.md)

---

**Happy Knowledge Graph Building! 🎉**
