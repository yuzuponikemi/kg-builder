# 反復的仮説探索 (Recursive Hypothesis Exploration)

## 🌌 コンセプト: "Recursive Alchemist"

**メインのナレッジグラフから仮説を生成し、その仮説自体を新しい概念として扱い、再度仮説を生成する。** これを繰り返すことで、多次元の「探索ツリー」が形成され、SF的なプロトタイプレベルの想像力拡張が可能になります。

### アイデア

```
Original Knowledge Graph (Layer 0)
         |
         ↓ 仮説生成
    Hypothesis Layer 1
    ├─ Branch A: 医療 × AI
    ├─ Branch B: 材料科学 × 量子
    └─ Branch C: 社会システム × 生態系
         |
         ↓ 各ブランチから再生成
    Hypothesis Layer 2
         ├─ Branch C-1: バイオミメティクス都市設計
         └─ Branch C-2: 群知能型社会システム
              |
              ↓ さらに拡張...
         Hypothesis Layer 3 (SF的領域)
              └─ Branch C-2-A: 分散自律型都市生命体
```

### 特徴

1. **多次元探索**: 一つの知識グラフから複数の方向性に分岐
2. **反復的拡張**: 仮説が新しい概念となり、さらなる仮説を生成
3. **SF的想像力**: 深く探索することで、現実を超えた研究アイデアへ
4. **探索履歴**: 全ての探索パスを保存し、後で振り返れる

## アーキテクチャ

### データ構造

#### HypothesisLayer
各レイヤーは以下を含む：
- **layer_id**: レイヤーの一意ID
- **parent_layer_id**: 親レイヤーのID（Layer 0はNone）
- **branch_name**: ブランチの名前
- **hypotheses**: このレイヤーの仮説リスト
- **expanded_concepts**: 仮説から抽出された新しい概念
- **expanded_relationships**: 仮説から抽出された新しい関係性

#### 概念抽出

仮説から以下を抽出：

```python
{
  "name": "仮説のタイトル",
  "type": "hypothesis",  # 新しいタイプ
  "description": "仮説の根拠",
  "confidence": 0.85,
  "source_hypothesis": {
    "source_concept": "元の概念A",
    "target_concept": "元の概念B"
  },
  "keywords": ["keyword1", "keyword2"],
  "layer": "expansion"
}
```

#### 関係性抽出

```python
{
  "from": "概念A",
  "to": "概念B",
  "type": "hypothesized_connection",  # 仮説的なつながり
  "confidence": 0.75,
  "rationale": "仮説の根拠",
  "mechanism": "メカニズムの説明",
  "layer": "expansion"
}
```

### ブランチング戦略

#### 1. Diversity（多様性）
異なる概念タイプの組み合わせでブランチを作成

```python
# 例: methodxtheory, materialxphenomenon, etc.
```

#### 2. Impact（インパクト）
インパクトスコアでソートし、高/中/低のブランチを作成

#### 3. Novelty（新規性）
新規性スコアでソートし、革新的/標準的/保守的のブランチを作成

#### 4. Feasibility（実現可能性）
実現可能性でソートし、短期/中期/長期のブランチを作成

## 使用方法

### 基本的な使い方

```bash
# 基本的な反復探索（2層、各層2ブランチ）
python scripts/explore_hypotheses_recursive.py

# 深い探索（3層、各層3ブランチ）
python scripts/explore_hypotheses_recursive.py \
  --max-depth 3 \
  --branches-per-layer 3 \
  --hypotheses-per-layer 15
```

### オプション

#### 探索パラメータ

```bash
# 最大深さ（デフォルト: 2）
--max-depth 3

# 各レイヤーの仮説数（デフォルト: 10）
--hypotheses-per-layer 15

# 各レイヤーのブランチ数（デフォルト: 2）
--branches-per-layer 3

# ブランチング基準（デフォルト: diversity）
--branching-criteria diversity  # diversity, impact, novelty, feasibility
```

#### 仮説生成設定

```bash
# 類似度計算手法
--method adamic_adar

# LLM temperature（創造性）
--temperature 0.9  # 0.3=保守的, 0.9=創造的
```

#### 品質フィルター（Layer 0のみ）

```bash
# Layer 0の仮説を高品質に限定
--min-novelty 0.7 \
--min-feasibility 0.6 \
--min-impact 0.8
```

### 実行例

#### 1. 多様性重視の探索

```bash
python scripts/explore_hypotheses_recursive.py \
  --max-depth 3 \
  --branches-per-layer 3 \
  --branching-criteria diversity \
  --hypotheses-per-layer 12
```

**結果**: 異なる概念タイプの組み合わせが自動的にブランチ化され、多様な研究方向が探索されます。

#### 2. インパクト重視の探索

```bash
python scripts/explore_hypotheses_recursive.py \
  --max-depth 2 \
  --branches-per-layer 3 \
  --branching-criteria impact \
  --min-impact 0.7 \
  --temperature 0.8
```

**結果**: 高インパクト、中インパクト、低インパクトの3つのブランチが作成され、それぞれが独立に探索されます。

#### 3. SF的探索（創造性最大）

```bash
python scripts/explore_hypotheses_recursive.py \
  --max-depth 4 \
  --branches-per-layer 2 \
  --temperature 0.95 \
  --hypotheses-per-layer 8 \
  --branching-criteria novelty
```

**結果**: 非常に創造的な仮説が生成され、4層の深さで未来的な研究アイデアが探索されます。

## 出力形式

### JSON構造

```json
{
  "metadata": {
    "timestamp": "2024-11-24T12:00:00",
    "num_layers": 7,
    "max_depth": 3
  },
  "layers": [
    {
      "layer_id": 0,
      "parent_layer_id": null,
      "branch_name": "root",
      "hypotheses": [...],
      "expanded_concepts": [
        {
          "name": "量子-生物システム融合",
          "type": "hypothesis",
          "description": "量子コンピューティングと生物システムを融合...",
          "confidence": 0.87,
          "source_hypothesis": {
            "source_concept": "Quantum Computing",
            "target_concept": "Biological Systems"
          }
        }
      ],
      "expanded_relationships": [
        {
          "from": "Quantum Computing",
          "to": "Biological Systems",
          "type": "hypothesized_connection",
          "confidence": 0.82,
          "rationale": "量子効果が生物プロセスで観測される..."
        }
      ]
    },
    {
      "layer_id": 100,
      "parent_layer_id": 0,
      "branch_name": "Branch-methodxtheory",
      "hypotheses": [...],
      "expanded_concepts": [...],
      "expanded_relationships": [...]
    }
  ]
}
```

### ツリー構造の可視化

```
Layer 0 - root
  Hypotheses: 10
  Expanded Concepts: 10
  Top: Quantum-Enhanced Neural Networks

  Layer 100 - Branch-methodxtheory
    Hypotheses: 8
    Expanded Concepts: 8
    Top: Topological Quantum Learning

    Layer 200 - Branch-impact-1
      Hypotheses: 6
      Expanded Concepts: 6
      Top: Self-Organizing Quantum Matter Networks
```

## Python API

```python
from kg_builder.config import get_settings
from kg_builder.graph.neo4j_client import Neo4jClient
from kg_builder.reasoning import HypothesisEngine, RecursiveAlchemist

# 設定
settings = get_settings()
client = Neo4jClient(
    uri=settings.neo4j_uri,
    user=settings.neo4j_user,
    password=settings.neo4j_password,
)

# エンジン初期化
hypothesis_engine = HypothesisEngine(client)
recursive_alchemist = RecursiveAlchemist(hypothesis_engine)

# Layer 0を生成
recursive_alchemist.generate_layer_0(
    similarity_method="adamic_adar",
    max_hypotheses=15,
    temperature=0.8,
)

# 反復的探索
layers = recursive_alchemist.explore_recursive(
    max_depth=3,
    hypotheses_per_layer=10,
    branches_per_layer=3,
    branching_criteria="diversity",
)

# 結果を保存
recursive_alchemist.export_exploration_tree("my_exploration.json")

# サマリー表示
recursive_alchemist.print_tree_summary()

# 個別のレイヤーにアクセス
layer_0 = recursive_alchemist.layers[0]
print(f"Layer 0 has {len(layer_0.hypotheses)} hypotheses")
print(f"Expanded {len(layer_0.expanded_concepts)} concepts")

# 特定のブランチを抽出
methodxtheory_layers = [
    l for l in recursive_alchemist.layers
    if "methodxtheory" in l.branch_name
]
```

## ユースケース

### 1. 未来技術の探索

```bash
# 4層の深い探索で未来的な技術を発見
python scripts/explore_hypotheses_recursive.py \
  --max-depth 4 \
  --temperature 0.9 \
  --branching-criteria novelty
```

**例**:
- Layer 0: "Quantum Computing + Neuroscience"
- Layer 1: "Quantum Consciousness Interface"
- Layer 2: "Distributed Quantum Cognition Network"
- Layer 3: "Planetary-Scale Quantum Mind" (SF領域)

### 2. 段階的イノベーション

```bash
# 実現可能性基準でブランチ分け
python scripts/explore_hypotheses_recursive.py \
  --max-depth 3 \
  --branching-criteria feasibility
```

**結果**:
- Branch 1: 短期実現可能（2-5年）
- Branch 2: 中期実現可能（5-10年）
- Branch 3: 長期実現可能（10+年）

### 3. 異分野融合の深掘り

```bash
# 多様性基準で最大限の異分野融合
python scripts/explore_hypotheses_recursive.py \
  --max-depth 3 \
  --branches-per-layer 4 \
  --branching-criteria diversity
```

**結果**: 複数の分野横断的な研究パスが同時に探索される

## 高度な使用法

### カスタムブランチング

```python
# 独自のブランチング基準を実装
class CustomBranching:
    def create_branches(self, hypotheses, num_branches):
        # カスタムロジック
        # 例: キーワードベースのクラスタリング
        pass

recursive_alchemist = RecursiveAlchemist(hypothesis_engine)
# ブランチング関数を差し替え
recursive_alchemist.branching_strategy = CustomBranching()
```

### 手動レイヤー操作

```python
# 特定の仮説だけを選んで次のレイヤーを作成
interesting_hypotheses = [
    h for h in layer_0.hypotheses
    if h['hypothesis']['novelty_score'] > 0.9
]

custom_layer = HypothesisLayer(
    layer_id=999,
    parent_layer_id=0,
    branch_name="Custom-HighNovelty",
    hypotheses=interesting_hypotheses,
)

recursive_alchemist.expand_layer(custom_layer)
recursive_alchemist.layers.append(custom_layer)
```

### 探索パスの可視化

```python
import json

# 特定のパスを追跡
def trace_path(layers, start_layer_id, target_layer_id):
    path = []
    current = next(l for l in layers if l.layer_id == target_layer_id)

    while current:
        path.append(current)
        if current.parent_layer_id is None:
            break
        current = next(
            (l for l in layers if l.layer_id == current.parent_layer_id),
            None
        )

    return list(reversed(path))

# パスを表示
path = trace_path(recursive_alchemist.layers, 0, 200)
for layer in path:
    print(f"{layer.layer_id}: {layer.branch_name}")
    print(f"  Top: {layer.hypotheses[0]['hypothesis']['title']}")
```

## パフォーマンス

- **Layer 0生成**: 10仮説で約30-60秒（LLM依存）
- **レイヤー拡張**: 1レイヤーあたり1-2秒
- **3層探索**: 各層10仮説で約2-5分

**推奨**:
- 最大深さ: 2-4層（それ以上は非常に時間がかかる）
- 各層の仮説数: 8-15個
- ブランチ数: 2-3個

## 制限事項と今後の拡張

### 現在の制限

1. **グラフの実際の拡張は未実装**: 現在は仮説を抽出するのみで、実際にNeo4jグラフには追加していない
2. **ブランチ間の相互作用なし**: 各ブランチは独立に探索される
3. **可視化機能が限定的**: テキストベースのサマリーのみ

### 今後の拡張予定

- [ ] **動的グラフ拡張**: 仮説をリアルタイムでNeo4jに追加
- [ ] **インタラクティブUI**: Web UIで探索ツリーを可視化・操作
- [ ] **ブランチマージ**: 異なるブランチの仮説を組み合わせる
- [ ] **評価指標**: 探索パスの「SF度」「実現可能性」を自動評価
- [ ] **探索戦略の学習**: 成功した探索パターンを学習
- [ ] **コラボレーション**: 複数人で探索ツリーを共有・編集

## トラブルシューティング

### 仮説が生成されない

- Layer 0で十分な仮説が生成されているか確認
- `--hypotheses-per-layer` を増やす
- `--min-novelty` などのフィルターを緩和

### 探索が遅い

- `--max-depth` を減らす（2層推奨）
- `--hypotheses-per-layer` を減らす
- Geminiなど高速なLLMプロバイダーを使用

### メモリ不足

- `--branches-per-layer` を減らす
- `--max-depth` を減らす

## 哲学的考察

この反復的仮説探索は、人間の想像力の**メタ認知的プロセス**をシミュレートしています：

1. **発散思考**: 複数の方向性に同時に探索
2. **収束思考**: 各ブランチで最も有望な仮説を選択
3. **メタ思考**: 仮説自体を概念として扱い、さらなる仮説を生成

深く探索するほど、現実から離れ、SF的な領域に入ります。これは：
- **短期探索（1-2層）**: 実現可能な研究アイデア
- **中期探索（3-4層）**: 野心的な研究ビジョン
- **長期探索（5+層）**: SF的想像力の領域

> "The best way to predict the future is to invent it." - Alan Kay

このツールは、未来を**予測**するのではなく、**発明**するためのものです。

## 参考文献

- [Original KG-Builder Paper](https://arxiv.org/abs/2403.11996)
- Concept mapping and knowledge representation
- Tree of Thoughts: Deliberate Problem Solving with LLMs
- Divergent thinking in creative problem solving
