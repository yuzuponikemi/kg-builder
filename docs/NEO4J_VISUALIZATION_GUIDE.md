# Neo4j 可視化ガイド

## ブラウザアクセス

```bash
# Neo4jブラウザを開く
open http://localhost:7474

# ログイン情報
Username: neo4j
Password: your_password_here
```

## 基本的なCypherクエリ

### 1. データベースの全体像を見る

```cypher
// スキーマの可視化
CALL db.schema.visualization()
```

### 2. サンプルノードを表示

```cypher
// 最初の25個のノードを表示
MATCH (n)
RETURN n
LIMIT 25
```

### 3. 論文を表示

```cypher
// 全ての論文を表示
MATCH (p:Paper)
RETURN p

// 論文の詳細情報を表示
MATCH (p:Paper)
RETURN p.title, p.arxiv_id, p.num_entities
```

### 4. コンセプト（概念）を表示

```cypher
// 全てのコンセプトタイプを確認
MATCH (c:Concept)
RETURN DISTINCT c.type, count(*) as count
ORDER BY count DESC

// 特定タイプのコンセプトを表示
MATCH (c:Concept {type: 'method'})
RETURN c
LIMIT 50

MATCH (c:Concept {type: 'phenomenon'})
RETURN c
LIMIT 50

MATCH (c:Concept {type: 'theory'})
RETURN c
LIMIT 50
```

### 5. 論文とコンセプトの関係を表示

```cypher
// 論文とそのコンセプトの関係（最初の50件）
MATCH (p:Paper)-[r:MENTIONS]->(c:Concept)
RETURN p, r, c
LIMIT 50

// 特定の論文のコンセプトを全て表示
MATCH (p:Paper {arxiv_id: '2202.07412v1'})-[r:MENTIONS]->(c:Concept)
RETURN p, r, c

// 特定タイプのコンセプトを持つ論文
MATCH (p:Paper)-[r:MENTIONS]->(c:Concept {type: 'method'})
RETURN p, r, c
LIMIT 100
```

## 分析クエリ

### 6. 最も言及されているコンセプトTOP 20

```cypher
MATCH (p:Paper)-[r:MENTIONS]->(c:Concept)
RETURN c.name, c.type, count(r) as mentions
ORDER BY mentions DESC
LIMIT 20
```

### 7. 特定のキーワードを検索

```cypher
// "knowledge graph" を含むコンセプト
MATCH (c:Concept)
WHERE toLower(c.name) CONTAINS 'knowledge graph'
RETURN c.name, c.type, c.description

// "neural" を含むコンセプトとそれを言及する論文
MATCH (p:Paper)-[r:MENTIONS]->(c:Concept)
WHERE toLower(c.name) CONTAINS 'neural'
RETURN p, r, c
LIMIT 50
```

### 8. 複数の論文で共通して言及されているコンセプト

```cypher
// 2つ以上の論文で言及されている共通概念
MATCH (p:Paper)-[:MENTIONS]->(c:Concept)<-[:MENTIONS]-(p2:Paper)
WHERE p <> p2
RETURN c.name, c.type, count(DISTINCT p) as paper_count
ORDER BY paper_count DESC
LIMIT 30

// 共通概念のグラフを可視化
MATCH (p:Paper)-[r:MENTIONS]->(c:Concept)<-[r2:MENTIONS]-(p2:Paper)
WHERE p <> p2 AND id(p) < id(p2)
WITH c, count(DISTINCT p) as paper_count
WHERE paper_count >= 2
MATCH (p:Paper)-[r:MENTIONS]->(c)
RETURN p, r, c
LIMIT 100
```

### 9. 各論文のコンセプト数

```cypher
MATCH (p:Paper)-[r:MENTIONS]->(c:Concept)
RETURN p.title, count(c) as concept_count, collect(DISTINCT c.type) as concept_types
ORDER BY concept_count DESC
```

### 10. タイプ別のコンセプト分布

```cypher
MATCH (c:Concept)
RETURN c.type as type, count(*) as count
ORDER BY count DESC
```

## 高度な可視化

### 11. 概念の共起ネットワーク（同じ論文で言及される概念）

```cypher
// 同じ論文で言及される2つのコンセプトを結ぶ
MATCH (c1:Concept)<-[:MENTIONS]-(p:Paper)-[:MENTIONS]->(c2:Concept)
WHERE id(c1) < id(c2)
RETURN c1, c2, count(p) as co_occurrences
ORDER BY co_occurrences DESC
LIMIT 100
```

### 12. 特定のコンセプトとその関連概念

```cypher
// "knowledge graph" に関連する概念
MATCH (c:Concept)<-[:MENTIONS]-(p:Paper)-[:MENTIONS]->(related:Concept)
WHERE toLower(c.name) CONTAINS 'knowledge graph' AND c <> related
RETURN c, p, related
LIMIT 50
```

### 13. 論文間の類似性（共通概念による）

```cypher
// 多くの共通概念を持つ論文のペア
MATCH (p1:Paper)-[:MENTIONS]->(c:Concept)<-[:MENTIONS]-(p2:Paper)
WHERE id(p1) < id(p2)
WITH p1, p2, count(c) as common_concepts
WHERE common_concepts >= 5
RETURN p1.title, p2.title, common_concepts
ORDER BY common_concepts DESC
```

## ビジュアライゼーションのカスタマイズ

### グラフ表示後の操作：

1. **ノードをクリック** - 詳細情報が右側に表示されます
2. **ノードをドラッグ** - グラフのレイアウトを調整できます
3. **左下のアイコン** - 表示設定：
   - 🎨 **色** - ノードタイプごとに色を変更
   - 📏 **サイズ** - プロパティに基づいてサイズを変更
   - 🏷️ **キャプション** - 表示するプロパティを選択
4. **ズーム** - マウスホイールまたはピンチ操作
5. **パン** - ドラッグで移動

### カラーコーディングの例：

```cypher
// Conceptノードをタイプごとに色分け
MATCH (c:Concept)
RETURN c
LIMIT 100
```

実行後、左下の設定で：
- `Concept` ノードをクリック
- "Color by" → `type` を選択
- "Caption" → `name` を選択

## よく使うクエリテンプレート

### キーワードで検索して周辺を表示

```cypher
MATCH (c:Concept)-[r]-(related)
WHERE toLower(c.name) CONTAINS '{{keyword}}'
RETURN c, r, related
LIMIT 50
```

使用例：`{{keyword}}` を `neural`, `graph`, `learning` などに置き換える

### トップNのコンセプトとそのつながり

```cypher
MATCH (p:Paper)-[r:MENTIONS]->(c:Concept)
WITH c, count(r) as mentions
ORDER BY mentions DESC
LIMIT 10
MATCH (p:Paper)-[r:MENTIONS]->(c)
RETURN p, r, c
```

## エクスポート

### CSVとしてエクスポート

```cypher
// コンセプトリストをエクスポート
MATCH (c:Concept)
RETURN c.name, c.type, c.description

// 論文リストをエクスポート
MATCH (p:Paper)
RETURN p.title, p.arxiv_id, p.num_entities
```

結果の右上の「⬇」アイコンからCSV/JSONとしてエクスポート可能

## トラブルシューティング

### データが表示されない場合

```cypher
// データベースに何があるか確認
CALL db.labels()  // 全てのラベルを表示
CALL db.relationshipTypes()  // 全てのリレーションシップタイプを表示
MATCH (n) RETURN count(n) as total_nodes  // 総ノード数
```

### パフォーマンスが遅い場合

```cypher
// LIMITを使って結果を制限
MATCH (n)
RETURN n
LIMIT 100  // 最初の100件のみ

// 特定の条件で絞り込む
MATCH (c:Concept {type: 'method'})
WHERE c.name CONTAINS 'graph'
RETURN c
```

## さらに学ぶには

- Neo4j Browser ガイド: ブラウザ内で `:help` と入力
- Cypherガイド: `:help cypher` と入力
- 例：`:play intro` - インタラクティブなチュートリアル
