# ドキュメント管理AI Agent

OpenAI Agent SDKとLangFuseを使用した契約書生成・管理システムです。

## 機能

- 📄 **賃貸契約書生成**: 物件情報から賃貸契約書を自動生成
- 📋 **業務委託契約書生成**: 業務内容から業務委託契約書を自動生成
- 🔍 **高度な検索機能**: 契約書の内容とメタデータから全文検索
- 🤖 **AI品質評価**: LLM-as-a-Judgeによる契約書の品質評価
- 🌐 **Web UI**: 直感的なブラウザベースのインターフェース
- 🔌 **REST API**: プログラムからの直接利用
- 💾 **ローカル保存**: 生成した契約書をローカルに保存・管理
- 📊 **LangFuseトレース**: LLM呼び出しのログ収集とトレース管理
- 🖥️ **CLI インターフェース**: 使いやすいコマンドライン操作

## 環境構築

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成し、以下の環境変数を設定してください：

```
OPENAI_API_KEY=your_openai_api_key_here
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=http://localhost:3000
```

### 3. LangFuseの起動

```bash
docker-compose up -d
```

初回起動後、http://localhost:3000 でLangFuseの管理画面にアクセスし、アカウントを作成してAPIキーを取得してください。

## 使用方法

### Web UI（推奨）

最も使いやすいインターフェースです：

```bash
python web_app.py
```

ブラウザで表示されるURLにアクセスして以下の機能が利用できます：
- 契約書作成フォーム
- 契約書一覧・検索
- AI品質評価
- 一括処理

### CLI操作

#### 賃貸契約書の生成

```bash
python ai_agent.py rental
```

対話形式で以下の情報を入力：
- 物件名
- 所在地
- 賃料
- 敷金
- 礼金
- 貸主氏名
- 借主氏名

#### 業務委託契約書の生成

```bash
python ai_agent.py service
```

対話形式で以下の情報を入力：
- 業務内容
- 報酬
- 委託者会社名
- 委託者代表者名
- 受託者名

#### 契約書一覧の表示

```bash
# 全ての契約書を表示
python ai_agent.py list

# 賃貸契約書のみ表示
python ai_agent.py list --type rental

# 業務委託契約書のみ表示
python ai_agent.py list --type service
```

#### ヘルプの表示

```bash
python ai_agent.py --help
```

### REST API

プログラムからの直接利用：

```python
import requests

# 賃貸契約書作成
response = requests.post("http://localhost:8081/api/rental", json={
    "property_name": "サンプルマンション101号室",
    "address": "東京都渋谷区...",
    "rent": "100000",
    "deposit": "200000",
    "key_money": "100000",
    "period": "2年",
    "landlord_name": "田中太郎",
    "tenant_name": "山田花子"
})

# 契約書検索
contracts = requests.get("http://localhost:8081/api/search?query=東京都").json()

# AI評価実行
evaluation = requests.post("http://localhost:8081/api/evaluate", json={
    "file_name": "rental_contract_20250101_120000.txt"
}).json()
```

## ファイル構造

```
AI_agent/
├── ai_agent.py              # メインCLIアプリケーション
├── web_app.py               # FastAPI Webアプリケーション
├── start_web.py             # Web起動用スクリプト
├── agent/
│   ├── __init__.py
│   ├── document_agent.py       # OpenAI SDK統合エージェント
│   ├── contract_judge.py       # LLM-as-a-Judge評価システム
│   ├── document_storage.py     # ファイル管理・検索機能
│   ├── prompts.py             # プロンプトテンプレート
│   └── builder.py             # 従来のビルダー（後方互換）
├── templates/               # Webテンプレート
├── contracts/               # 生成された契約書の保存先
│   ├── rental/             # 賃貸契約書
│   └── service/            # 業務委託契約書
├── docker-compose.yml       # LangFuse用Docker設定
├── requirements.txt         # Python依存関係
└── .env.example            # 環境変数テンプレート
```

## AI評価システム

### 評価項目（各1-10点）

1. **法的適合性**: 日本法への準拠度
2. **完整性**: 必要条項の網羅性
3. **明瞭性**: 条文の理解しやすさ
4. **リスク管理**: 双方のリスク配慮
5. **実用性**: 実際の運用における有効性

### 評価結果

- **総合スコア**: 1-100点
- **段階評価**: A（優秀）〜F（要改善）
- **強み・弱点**: 具体的な分析
- **改善提案**: 実践的なアドバイス
- **法的懸念点**: 専門的な指摘

## LangFuseでのモニタリング

生成された契約書の作成プロセスは全てLangFuseでトレースされ、以下の情報を確認できます：

- LLM呼び出しの詳細
- 入力プロンプト
- 生成結果
- 処理時間
- コスト情報
- AI評価プロセス

管理画面: http://localhost:3000

## トラブルシューティング

### OpenAI APIキーエラー
`.env`ファイルに正しいAPIキーが設定されているか確認してください。

### LangFuse接続エラー
Docker Composeが正常に起動しているか確認してください：
```bash
docker-compose ps
```

### Web起動エラー
```bash
# 利用可能ポート確認
netstat -tulpn | grep :808

# 別ポートで起動
python web_app.py  # 自動ポート検出
```

### ファイル保存エラー
`contracts/`ディレクトリの書き込み権限を確認してください。