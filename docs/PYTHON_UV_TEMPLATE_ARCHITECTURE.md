# python-uv-template アーキテクチャ設計書

このドキュメントは、python-uv-templateが持つすべての機能を網羅的に記載しています。
別のリポジトリで同等の機能を実装する際の設計書として使用できます。

---

## 📋 目次

1. [概要](#概要)
2. [コア機能](#コア機能)
3. [ファイル構造](#ファイル構造)
4. [詳細実装ガイド](#詳細実装ガイド)
5. [設定ファイル](#設定ファイル)

---

## 概要

### プロジェクトの目的

研究用Pythonソフトウェア開発のための完全なテンプレート。以下を重視：

- **再現性**: 依存関係の厳密な固定管理
- **品質**: 自動テスト、型チェック、リンター
- **自動化**: CI/CD、自律的コード修正、Claude Code統合
- **テスト駆動開発（TDD）**: テストファーストの開発フロー

### 主要技術スタック

| 分類 | 技術 |
|------|------|
| パッケージ管理 | uv (Astral) |
| テスト | pytest, pytest-cov |
| リンター/フォーマッター | ruff |
| 型チェック | mypy |
| ドキュメント | Sphinx (sphinx-rtd-theme) |
| CI/CD | GitHub Actions |
| AI統合 | Claude Code (Anthropic) |

---

## コア機能

### 1. 自律的コード修正システム

**目的**: CIが失敗した際、Claudeが自動的にエラーを解析・修正

**仕組み**:
```
1. claude/** ブランチにpush
2. CI実行（pytest, ruff, mypy）
3. 失敗時 → auto-fix.yml が起動
4. エラーログを収集
5. Issueを自動作成、@claudeメンション
6. Claudeがエラー解析・修正・コミット
7. CI再実行
```

**必要なワークフロー**:
- `.github/workflows/ci.yml`: テスト実行
- `.github/workflows/auto-fix.yml`: 自動修正トリガー
- `.github/workflows/claude-code.yml`: Claude統合

### 2. 依存関係の自動管理

**目的**: 完全な再現性を保ちつつ、依存関係を自動更新

**方式**: requirements.in/txt 2ファイル管理

```
requirements.in  (人間が編集)
    ↓ uv pip compile
requirements.txt (機械が生成、全バージョン固定)
    ↓ CI で自動更新
自動コミット＆プッシュ
```

**ワークフロー**:
```yaml
- Compile requirements.txt
- Check for changes
- Auto-commit if changed
- Install from requirements.txt
```

### 3. CI/CD パイプライン

**チェック項目**:
1. **ruff check**: コードスタイル
2. **ruff format**: フォーマット
3. **mypy**: 型チェック（srcのみ、外部ライブラリ除外）
4. **pytest**: テスト（100%カバレッジ目標）

**特徴**:
- `continue-on-error: true` で全チェック実行
- ログを artifact として保存（7日間）
- 失敗時に auto-fix ワークフローをトリガー

### 4. テスト環境

**pytest設定** (`pyproject.toml`):
```toml
testpaths = ["tests"]
addopts = [
    "-v",
    "--strict-markers",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
]
```

**フィクスチャ** (`tests/conftest.py`):
- ランダムシード固定（再現性）
- 一時ディレクトリ
- サンプルデータ
- カスタムマーカー（slow, integration, benchmark, scientific）

### 5. コード品質管理

**Ruff設定**:
```toml
line-length = 100
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM"]
```

**Mypy設定**:
```toml
files = ["src", "tests", "benchmarks", "scripts"]  # 外部ライブラリ除外
disallow_untyped_defs = true  # src のみ厳格
```

**Pre-commit**:
- ruff (lint + format)
- mypy
- bandit (セキュリティ)
- nbqa (Jupyter対応)

### 6. ドキュメント生成

**Sphinx構成**:
```
docs/
├── conf.py              # Sphinx設定
├── index.rst            # トップページ
├── getting_started.rst  # 導入ガイド
├── api_reference.rst    # API自動生成
├── examples.rst         # 使用例
└── contributing.rst     # コントリビューション
```

**拡張機能**:
- autodoc: 自動API生成
- napoleon: Google/NumPy docstring対応
- intersphinx: 外部ドキュメントリンク

### 7. ベンチマーク

**pytest-benchmark使用**:
```python
def test_benchmark_function(benchmark):
    result = benchmark(function_to_test, arg1, arg2)
    assert result == expected
```

**実行**:
```bash
pytest benchmarks/ --benchmark-only
pytest benchmarks/ --benchmark-compare
```

### 8. Claude Code統合

**3つのワークフロー**:

1. **claude-code.yml**: @claudeメンション時に起動
2. **ci.yml**: 通常のCIチェック
3. **auto-fix.yml**: CI失敗時の自動修正

**トリガー**:
- Issue/PR コメントで `@claude`
- `claude/**` ブランチへのpush

### 9. GitHub連携

**Issueテンプレート**:
- `bug_report.yml`: バグレポート
- `feature_request.yml`: 機能リクエスト
- `claude_task.yml`: Claudeタスク依頼

**PRテンプレート**:
- チェックリスト付き
- レビュー依頼セクション

---

## ファイル構造

```
python-uv-template/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # メインCIワークフロー
│   │   ├── auto-fix.yml        # 自動修正ワークフロー
│   │   └── claude-code.yml     # Claude統合
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── feature_request.yml
│   │   └── claude_task.yml
│   └── pull_request_template.md
│
├── docs/                       # Sphinxドキュメント
│   ├── conf.py
│   ├── index.rst
│   ├── getting_started.rst
│   ├── api_reference.rst
│   ├── examples.rst
│   └── contributing.rst
│
├── examples/                   # Jupyter notebook例
│   ├── basic_usage.ipynb
│   └── README.md
│
├── src/                        # ソースコード
│   ├── __init__.py
│   └── calculator.py           # サンプルモジュール
│
├── tests/                      # テストコード
│   ├── __init__.py
│   ├── conftest.py            # pytest設定・フィクスチャ
│   └── test_calculator.py
│
├── benchmarks/                 # パフォーマンステスト
│   ├── __init__.py
│   ├── conftest.py
│   ├── benchmark_calculator.py
│   └── README.md
│
├── scripts/                    # ユーティリティスクリプト
│   ├── process_data.py        # データ処理例
│   └── README.md
│
├── .env.example               # 環境変数テンプレート
├── .gitignore
├── .pre-commit-config.yaml    # Pre-commitフック設定
├── CONTRIBUTING.md            # コントリビューションガイド
├── Makefile                   # タスクランナー
├── pyproject.toml             # プロジェクト設定
├── README.md
├── requirements.in            # トップレベル依存関係
├── requirements.txt           # 固定バージョン依存関係
└── requirements-dev.txt       # 開発用依存関係
```

---

## 詳細実装ガイド

### 1. CIワークフローの実装

#### ci.yml の核心部分

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # requirements.txt自動コミット用

    steps:
      # 1. requirements.txtを自動更新
      - name: Compile requirements.txt
        run: uv pip compile requirements.in -o requirements.txt

      - name: Check for requirements.txt changes
        id: check-requirements
        run: |
          if git diff --quiet requirements.txt; then
            echo "changed=false" >> $GITHUB_OUTPUT
          else
            echo "changed=true" >> $GITHUB_OUTPUT
          fi

      - name: Commit updated requirements.txt
        if: steps.check-requirements.outputs.changed == 'true'
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add requirements.txt
          git commit -m "Auto-update requirements.txt from requirements.in"
          git push

      # 2. テスト実行（continue-on-error で全実行）
      - name: Run ruff linter
        id: ruff-check
        continue-on-error: true
        run: ruff check . 2>&1 | tee ruff-check.log

      - name: Run mypy type checker
        id: mypy
        continue-on-error: true
        run: mypy --ignore-missing-imports 2>&1 | tee mypy.log

      - name: Run pytest
        id: pytest
        continue-on-error: true
        run: python -m pytest -v --tb=short 2>&1 | tee pytest.log

      # 3. ログをアーティファクトとして保存
      - name: Upload test logs as artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-logs
          path: |
            pytest.log
            ruff-check.log
            mypy.log

      # 4. 失敗判定
      - name: Check if any step failed
        if: |
          steps.ruff-check.outcome == 'failure' ||
          steps.mypy.outcome == 'failure' ||
          steps.pytest.outcome == 'failure'
        run: |
          echo "::error::CI checks failed."
          exit 1
```

**重要ポイント**:
- `|| true` は使わない（outcome が正しく 'failure' にならない）
- `continue-on-error: true` だけで失敗を処理
- ログを必ず保存（デバッグ用）

#### auto-fix.yml の実装

```yaml
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: ["claude/**"]

jobs:
  auto-fix:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write

    steps:
      - name: Download test logs
        uses: actions/download-artifact@v4
        with:
          name: test-logs
          run-id: ${{ github.event.workflow_run.id }}

      - name: Prepare error context
        run: |
          # エラーログをまとめる
          echo "## CI Test Failure Report" > error-context.md
          cat pytest.log >> error-context.md
          cat ruff-check.log >> error-context.md
          cat mypy.log >> error-context.md

      - name: Create issue for auto-fix
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const errorContext = fs.readFileSync('error-context.md', 'utf8');

            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `[Auto-fix] CI Failed on ${branch}`,
              body: `${errorContext}\n\n@claude CIが失敗しました。修正してください。`,
              labels: ['auto-fix', 'claude']
            });
```

### 2. 依存関係管理の実装

#### requirements.in の作成

```
# requirements.in
# Core testing
pytest>=8.0.0
pytest-cov>=4.1.0

# Code quality
ruff>=0.3.0
mypy>=1.8.0

# Data processing
numpy>=1.24.0
pandas>=2.0.0

# Type stubs for mypy
pandas-stubs>=2.0.0
```

#### Makefile タスク

```makefile
compile:
	uv pip compile requirements.in -o requirements.txt
	@echo "✓ requirements.txt updated"

install:
	uv pip install --system -r requirements.txt
	uv pip install --system -r requirements-dev.txt
```

### 3. テスト環境の実装

#### tests/conftest.py

```python
import random
import tempfile
from pathlib import Path
from collections.abc import Generator

import numpy as np
import pytest


@pytest.fixture(scope="session", autouse=True)
def set_random_seeds() -> None:
    """再現性のためランダムシードを固定"""
    random.seed(42)
    np.random.seed(42)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """一時ディレクトリを提供"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_data() -> dict:
    """テスト用サンプルデータ"""
    return {
        "array": np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
        "matrix": np.array([[1.0, 2.0], [3.0, 4.0]]),
    }


def pytest_configure(config: pytest.Config) -> None:
    """カスタムマーカーを登録"""
    config.addinivalue_line("markers", "slow: 遅いテスト")
    config.addinivalue_line("markers", "integration: 統合テスト")
    config.addinivalue_line("markers", "benchmark: ベンチマーク")
```

### 4. pyproject.toml の完全設定

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "your-project"
version = "0.1.0"
description = "Research software with TDD"
requires-python = ">=3.9"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
]

[tool.ruff]
line-length = 100
target-version = "py39"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]
ignore = ["E501"]  # line too long

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ARG", "S101"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true
exclude = ["^build/", "^dist/", "^.venv/"]
files = ["src", "tests", "benchmarks", "scripts"]

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = "benchmarks.*"
disallow_untyped_defs = false

[tool.bandit]
exclude_dirs = ["tests", "benchmarks", "examples"]
skips = ["B101"]
```

### 5. Pre-commit設定

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: [--ignore-missing-imports]
        exclude: ^(tests/|examples/)

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]
```

### 6. Sphinx ドキュメント

#### docs/conf.py

```python
import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

project = "your-project"
copyright = "2024, Your Team"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "sphinx.ext.intersphinx",
]

html_theme = "sphinx_rtd_theme"

napoleon_google_docstring = True
napoleon_numpy_docstring = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}
```

---

## 設定ファイル

### .env.example

```bash
# Python設定
PYTHONHASHSEED=0
PYTHONUNBUFFERED=1

# NumPy/SciPy設定
OMP_NUM_THREADS=4
NUMBA_CACHE_DIR=/tmp/numba_cache

# データパス
DATA_DIR=./data
OUTPUT_DIR=./output

# ログ設定
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# 再現性設定
RANDOM_SEED=42
```

### .gitignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Type checking
.mypy_cache/

# Environments
.env
.venv
venv/

# IDEs
.vscode/
.idea/

# Documentation
docs/_build/

# Data
data/
*.csv
*.h5
*.pkl
```

---

## 実装チェックリスト

### 必須実装（最小構成）

- [ ] `pyproject.toml` 設定
- [ ] `requirements.in` + `requirements.txt`
- [ ] `.github/workflows/ci.yml`
- [ ] `tests/conftest.py` (pytest設定)
- [ ] `Makefile` (タスクランナー)
- [ ] `.gitignore`

### 推奨実装（完全構成）

- [ ] `.github/workflows/auto-fix.yml` (自動修正)
- [ ] `.github/workflows/claude-code.yml` (Claude統合)
- [ ] `.github/ISSUE_TEMPLATE/` (3種類)
- [ ] `.github/pull_request_template.md`
- [ ] `.pre-commit-config.yaml`
- [ ] `docs/` (Sphinx)
- [ ] `benchmarks/`
- [ ] `examples/` (Jupyter)
- [ ] `scripts/`
- [ ] `.env.example`
- [ ] `CONTRIBUTING.md`

### オプション実装

- [ ] `requirements-dev.txt` (開発用依存関係)
- [ ] Docker対応
- [ ] GitHub Pages デプロイ
- [ ] バージョン自動管理

---

## よくある実装パターン

### パターン1: 最小構成（5分で実装）

```bash
# 1. 基本ファイル作成
touch pyproject.toml requirements.in Makefile
mkdir -p src tests .github/workflows

# 2. pyproject.toml をコピー
# 3. ci.yml をコピー
# 4. make install で確認
```

### パターン2: 完全構成（30分で実装）

```bash
# このリポジトリをテンプレートとして使用
# または、すべてのファイルをコピー
```

### パターン3: 段階的実装

```
Week 1: CI + テスト
Week 2: 依存関係自動管理
Week 3: Claude統合
Week 4: ドキュメント + ベンチマーク
```

---

## トラブルシューティング

### Q1: mypy が外部ライブラリをチェックしてしまう

```toml
[tool.mypy]
files = ["src", "tests"]  # チェック対象を限定
exclude = ["^build/", "^.venv/"]
```

### Q2: CI で pytest が import エラー

```yaml
# python -m pytest を使う
- run: python -m pytest -v
```

### Q3: requirements.txt が自動更新されない

```yaml
# permissionsを確認
permissions:
  contents: write  # 必須
```

### Q4: auto-fix が起動しない

```yaml
# outcome を正しく設定
- id: pytest
  continue-on-error: true  # || true は不要
  run: pytest
```

---

## まとめ

この設計書に従えば、任意のPythonプロジェクトに以下を導入できます：

✅ 自律的コード修正
✅ 完全な再現性
✅ 包括的なテスト
✅ 自動化されたCI/CD
✅ Claude Code統合
✅ 研究用途に最適化

**実装時間の目安**:
- 最小構成: 5-10分
- 推奨構成: 30-60分
- 完全構成: 2-3時間

**次のステップ**:
1. このドキュメントを新しいリポジトリにコピー
2. チェックリストに従って実装
3. `make ci` でローカルテスト
4. `claude/**` ブランチでpushして動作確認
