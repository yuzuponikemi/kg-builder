# 仮説生成エンジン (Hypothesis Generation Engine)

## 概要

仮説生成エンジンは、構築されたナレッジグラフから**「未踏領域」**を発見し、新しい研究アイデアを提案するシステムです。グラフアルゴリズムとLLMを組み合わせることで、人間が気づきにくい分野間の関連性を自動的に発見します。

**別名**: "The Alchemist" - 異分野融合の錬金術師

## コンセプト

既存の論文から構築されたナレッジグラフ上で：
1. **構造的に類似しているが、まだ関係性が定義されていない概念ペア**を発見
2. **LLMを使って、これらの概念を結びつける仮説を生成**
3. **新規性・実現可能性・インパクトでスコアリング**

これは「認知の拡張」そのものであり、従来の文献レビューでは見つからない新しい研究方向を提示します。

## 技術スタック

- **NetworkX**: グラフアルゴリズム（中心性解析、コミュニティ検出、リンク予測）
- **python-louvain**: コミュニティ検出（Louvain法）
- **LLM統合**: Ollama / OpenAI / Anthropic / Gemini（既存のLLMクライアント）
- **Neo4j**: グラフデータベース（既存のナレッジグラフを使用）

## アーキテクチャ

```
Neo4j Knowledge Graph
        ↓
  GraphAnalytics (中心性解析、コミュニティ検出)
        ↓
  LinkPredictor (リンク予測、類似度計算)
        ↓
  HypothesisGenerator (LLMで仮説生成)
        ↓
  Results (JSON出力: 仮説 + スコア + メタデータ)
```

### モジュール構成

```
src/kg_builder/reasoning/
├── __init__.py                 # モジュール初期化
├── graph_analytics.py          # グラフ解析
├── link_predictor.py           # リンク予測
├── hypothesis_generator.py     # 仮説生成
├── hypothesis_engine.py        # メインエンジン
└── prompts/
    └── hypothesis_generation.txt  # LLMプロンプト
```

## 使用方法

### 基本的な使い方

```bash
# 仮説を生成
python scripts/generate_hypotheses.py

# 結果はdata/hypotheses/に保存される
```

### オプション

#### リンク予測の設定

```bash
# 類似度計算手法を指定
python scripts/generate_hypotheses.py --method adamic_adar

# 利用可能な手法:
# - jaccard (デフォルト)
# - adamic_adar (推奨: 共通隣接ノードを重視)
# - resource_allocation
# - common_neighbors
# - preferential_attachment

# 予測数を増やす
python scripts/generate_hypotheses.py --top-n 100

# 最小類似度を設定
python scripts/generate_hypotheses.py --min-similarity 0.2
```

#### フィルタリング

```bash
# 異分野融合のみ（異なる概念タイプ間のリンク）
python scripts/generate_hypotheses.py --cross-domain

# 中心的な概念を優先しない（全概念を平等に扱う）
python scripts/generate_hypotheses.py --no-central-focus
```

#### 仮説生成の設定

```bash
# 生成する仮説の数を制限
python scripts/generate_hypotheses.py --max-hypotheses 10

# より創造的な仮説を生成（temperature を上げる）
python scripts/generate_hypotheses.py --temperature 0.9

# より保守的な仮説を生成
python scripts/generate_hypotheses.py --temperature 0.3
```

#### 品質フィルター

```bash
# 高品質な仮説のみ
python scripts/generate_hypotheses.py \
  --min-novelty 0.7 \
  --min-feasibility 0.7 \
  --min-impact 0.8

# 実現可能性重視
python scripts/generate_hypotheses.py --min-feasibility 0.8
```

#### 出力設定

```bash
# 出力ファイルを指定
python scripts/generate_hypotheses.py --output my_hypotheses.json

# サマリーを表示しない
python scripts/generate_hypotheses.py --no-summary

# サマリーに表示する仮説の数
python scripts/generate_hypotheses.py --summary-top-n 20
```

### 組み合わせ例

```bash
# 推奨設定: 高品質な異分野融合仮説を生成
python scripts/generate_hypotheses.py \
  --method adamic_adar \
  --cross-domain \
  --max-hypotheses 20 \
  --min-novelty 0.6 \
  --min-impact 0.7 \
  --temperature 0.8 \
  --output data/hypotheses/cross_domain_hypotheses.json

# 保守的な設定: 実現可能性重視
python scripts/generate_hypotheses.py \
  --method jaccard \
  --max-hypotheses 10 \
  --min-feasibility 0.8 \
  --temperature 0.5

# 探索的な設定: より多くの創造的な仮説
python scripts/generate_hypotheses.py \
  --top-n 100 \
  --max-hypotheses 50 \
  --temperature 0.9 \
  --min-similarity 0.05
```

## 出力形式

生成された仮説は以下のJSON形式で保存されます：

```json
{
  "metadata": {
    "timestamp": "2024-11-24T10:30:00",
    "similarity_method": "jaccard",
    "num_predictions": 50,
    "num_hypotheses": 42
  },
  "graph_analysis": {
    "statistics": {
      "num_nodes": 523,
      "num_edges": 1247,
      "density": 0.0091,
      "num_communities": 15
    },
    "top_concepts_pagerank": [
      {"name": "Graph Neural Networks", "score": 0.023},
      {"name": "Knowledge Graph", "score": 0.019}
    ]
  },
  "hypotheses": [
    {
      "hypothesis": {
        "title": "Integrating Graph Attention with Quantum Computing",
        "rationale": "Both concepts leverage network topology...",
        "research_direction": "Develop quantum-enhanced GNN...",
        "mechanism": "Quantum superposition could enable...",
        "next_steps": [
          "Survey existing quantum graph algorithms",
          "Design hybrid classical-quantum architecture",
          "Benchmark on molecular graphs"
        ],
        "novelty_score": 0.92,
        "feasibility_score": 0.65,
        "impact_score": 0.88,
        "keywords": ["quantum computing", "GNN", "molecular design"]
      },
      "link_prediction": {
        "source": "Graph Attention Networks",
        "target": "Quantum Computing",
        "similarity_score": 0.34,
        "source_type": "method",
        "target_type": "theory"
      },
      "combined_score": 0.82
    }
  ]
}
```

### フィールド説明

- **novelty_score**: 仮説の新規性（0.0-1.0）
- **feasibility_score**: 実現可能性（0.0-1.0）
- **impact_score**: 潜在的なインパクト（0.0-1.0）
- **combined_score**: 総合スコア（novelty × 0.4 + impact × 0.4 + feasibility × 0.2）

## Python APIとして使用

```python
from kg_builder.config import get_settings
from kg_builder.graph.neo4j_client import Neo4jClient
from kg_builder.reasoning import HypothesisEngine

# 設定とクライアント
settings = get_settings()
client = Neo4jClient(
    uri=settings.neo4j_uri,
    user=settings.neo4j_user,
    password=settings.neo4j_password,
)

# エンジン初期化
engine = HypothesisEngine(client)

# 仮説生成
results = engine.generate_hypotheses(
    similarity_method="adamic_adar",
    top_n=50,
    cross_domain_only=True,
    max_hypotheses=20,
    temperature=0.8,
    min_novelty=0.6,
    min_impact=0.7,
)

# 結果を保存
engine.save_results(results, "my_hypotheses.json")

# サマリーを表示
engine.print_summary(results, top_n=10)

# 個別に使用
from kg_builder.reasoning import GraphAnalytics, LinkPredictor, HypothesisGenerator

# グラフ解析のみ
analytics = GraphAnalytics(client)
analytics.load_graph_from_neo4j()
top_concepts = analytics.get_top_concepts("pagerank", top_n=20)
communities = analytics.detect_communities()

# リンク予測のみ
predictor = LinkPredictor(analytics)
predictions = predictor.find_cross_domain_links(method="jaccard", top_n=30)

# 仮説生成のみ
generator = HypothesisGenerator()
hypotheses = generator.generate_hypotheses_batch(predictions, max_hypotheses=10)
```

## ユースケース

### 1. 異分野融合の発見

```bash
python scripts/generate_hypotheses.py \
  --cross-domain \
  --method adamic_adar \
  --max-hypotheses 30 \
  --min-novelty 0.7
```

**例**: "Graph Neural Networks" (method) × "Protein Folding" (phenomenon)
→ 「GNNを使ったタンパク質構造予測の新手法」

### 2. 中心的概念の新規応用

```bash
python scripts/generate_hypotheses.py \
  --focus-on-central-concepts \
  --max-hypotheses 20 \
  --min-impact 0.8
```

**例**: "Transformer" (重要な手法) × "Knowledge Graph Reasoning" (未接続)
→ 「Transformer-based Knowledge Graph Completion」

### 3. 理論と応用の架橋

```bash
python scripts/generate_hypotheses.py \
  --filter-types theory application \
  --max-hypotheses 15 \
  --min-feasibility 0.7
```

**例**: "Variational Inference" (theory) × "Drug Discovery" (application)
→ 「変分推論を用いた創薬最適化」

## アルゴリズム詳細

### 1. グラフ解析

**中心性指標**:
- **PageRank**: グラフ全体での重要度
- **Betweenness**: 他のノード間の橋渡し度
- **Degree Centrality**: 直接の接続数

**コミュニティ検出**:
- **Louvain法**: モジュラリティ最大化

### 2. リンク予測

**Jaccard係数**:
```
J(A, B) = |neighbors(A) ∩ neighbors(B)| / |neighbors(A) ∪ neighbors(B)|
```

**Adamic-Adar**（推奨）:
```
AA(A, B) = Σ_{z ∈ CN(A,B)} 1 / log(degree(z))
```
共通隣接ノードを重視、かつそのノードの稀少性を考慮

**Resource Allocation**:
```
RA(A, B) = Σ_{z ∈ CN(A,B)} 1 / degree(z)
```

**Common Neighbors**:
```
CN(A, B) = |neighbors(A) ∩ neighbors(B)|
```

### 3. 仮説生成

LLMプロンプトに以下を含める：
- 概念名、タイプ、説明
- 類似度スコア
- 共通隣接ノード
- グラフ構造の証拠

LLMが生成：
- 仮説タイトル
- 根拠（rationale）
- 研究方向（research direction）
- メカニズム（mechanism）
- 次のステップ（next steps）
- スコア（novelty / feasibility / impact）

## ベストプラクティス

### 1. 初回実行時

```bash
# まずグラフの統計情報を確認
python scripts/neo4j_manager.py stats

# 少数の仮説で試す
python scripts/generate_hypotheses.py --max-hypotheses 5

# 結果を確認してからパラメータを調整
```

### 2. 類似度手法の選択

- **Jaccard**: バランスが良い、高速
- **Adamic-Adar**: **推奨** - 質の高い予測
- **Common Neighbors**: シンプル、高速
- **Resource Allocation**: Adamic-Adarと類似
- **Preferential Attachment**: 人気ノード間の接続を予測

### 3. Temperature の調整

- **0.3-0.5**: 保守的、実現可能性重視
- **0.7**: **デフォルト** - バランス良好
- **0.8-0.9**: 創造的、探索的

### 4. フィルタリング戦略

**高品質優先**:
```bash
--min-novelty 0.7 --min-feasibility 0.7 --min-impact 0.8
```

**実現可能性優先**:
```bash
--min-feasibility 0.8 --min-novelty 0.5
```

**革新性優先**:
```bash
--min-novelty 0.8 --min-impact 0.8
```

## トラブルシューティング

### Neo4jに接続できない

```bash
# Neo4jが起動しているか確認
docker ps | grep neo4j

# Neo4jを起動
docker-compose -f docker/docker-compose.yml up -d neo4j
```

### グラフが空

```bash
# ナレッジグラフをインポート
python scripts/import_to_neo4j.py data/exports/

# または論文から抽出
python scripts/build_knowledge_graph.py "your topic"
```

### 仮説が生成されない

- `--min-similarity` を下げる（例: 0.05）
- `--top-n` を増やす（例: 100）
- フィルター条件を緩和

### LLMエラー

- `.env` でLLMプロバイダーが正しく設定されているか確認
- Ollamaの場合: `ollama list` でモデルがインストールされているか確認
- API Key が正しく設定されているか確認（OpenAI/Anthropic/Gemini）

## パフォーマンス

- **グラフ解析**: 500ノード/1000エッジで 1-2秒
- **リンク予測**: 50予測で 2-5秒
- **仮説生成**: 1仮説あたり 3-10秒（LLM依存）
  - Ollama (ローカル): 5-10秒/仮説
  - OpenAI GPT-4: 3-5秒/仮説
  - Gemini: 2-4秒/仮説

**推奨**: 大量の仮説を生成する場合は `--max-hypotheses` で制限

## 今後の拡張

- [ ] 仮説の自動検証（文献検索）
- [ ] 仮説間の関連性分析
- [ ] インタラクティブなWeb UI
- [ ] 時系列分析（研究トレンド予測）
- [ ] 複数論文の横断的な仮説生成
- [ ] カスタムフィルタリングルール

## 参考文献

- [Link Prediction in NetworkX](https://networkx.org/documentation/stable/reference/algorithms/link_prediction.html)
- [Louvain Community Detection](https://python-louvain.readthedocs.io/)
- [Original Paper: Accelerating Scientific Discovery with Generative Knowledge Extraction](https://arxiv.org/abs/2403.11996)
