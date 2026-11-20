# 課題：Google Cloud で「毎日自動で回るデータ分析基盤」を作る

# 課題OJT担当者
@realmadridmarcelo (田中一馬)

# 課題目的
* **Google Cloud の基礎を、手を動かしながら一通りキャッチアップする**
    * これまでローカルPCで完結していた開発を、クラウド上で「動かし続ける」形に引き上げる。
    * プロジェクト・IAM・課金といった土台から、Cloud Run / Cloud Storage / BigQuery / Cloud Scheduler など主要サービスまでを、実際に使える状態にする。
* **「ローカルで動く」と「クラウドで動く」の違いを体感で理解する**
    * コンテナ・環境変数・認証（サービスアカウント）・ログ・権限など、クラウドならではの考え方を、詰まりながら身につける。
* **データサイエンティストとして「分析をサービスとして届ける」視点を持つ**
    * 分析そのものはシンプルでよい。データを自動で集め、蓄積し、誰でも結果を見られる状態にするまでを一人で走り切る。
* **未経験技術の自走キャッチアップ能力を確認する**
    * 「公式Doc → 最小サンプル → 自分の基盤に組込み → 詰まりを切り分けて解決」を自走できるか。

# 課題概要
**公開データを毎日自動で取得 → Cloud Storage に保存 → BigQuery に蓄積・集計 → 分析結果を API とダッシュボードで公開する。**

```
Cloud Scheduler（毎日）
      │
      ▼
Cloud Run Jobs（データ取得） ──► Cloud Storage（生データ）
      │
      ▼
BigQuery（蓄積・SQL集計）
      │
      ├──► Cloud Run Service（FastAPI：分析結果API）── 公開URL
      └──► Looker Studio（ダッシュボード）
```

題材データは **Wikimedia Pageviews API**（Wikipedia 記事の日次閲覧数・APIキー不要）を使う。
テーマは **「データベース・オントロジー・グラフデータのトレンド」**。oarth に関わる技術領域で、どの技術の注目度が上がっている／下がっているのかを可視化する。

## 対象記事（英語版 Wikipedia・20記事）

閲覧数が多く記事が揃っている英語版（`en.wikipedia`）を対象とする。`article` 列は API に渡す記事タイトルそのもの。`category` は集計用に BigQuery にも持たせること。

| # | category | article | 概要 |
|---|---|---|---|
| 1 | オントロジー・セマンティックWeb | `Ontology_(information_science)` | 情報科学におけるオントロジー |
| 2 | オントロジー・セマンティックWeb | `Semantic_Web` | セマンティックWeb |
| 3 | オントロジー・セマンティックWeb | `Resource_Description_Framework` | RDF（トリプルによるデータ表現） |
| 4 | オントロジー・セマンティックWeb | `Web_Ontology_Language` | OWL（オントロジー記述言語） |
| 5 | オントロジー・セマンティックWeb | `SPARQL` | RDF向けクエリ言語 |
| 6 | グラフデータ | `Knowledge_graph` | ナレッジグラフ |
| 7 | グラフデータ | `Graph_database` | グラフデータベース |
| 8 | グラフデータ | `Neo4j` | 代表的なグラフDB製品 |
| 9 | グラフデータ | `Cypher_(query_language)` | グラフDB向けクエリ言語 |
| 10 | グラフデータ | `Graph_neural_network` | グラフニューラルネットワーク |
| 11 | AI × データベース | `Vector_database` | ベクトルデータベース |
| 12 | AI × データベース | `Retrieval-augmented_generation` | RAG（検索拡張生成） |
| 13 | リレーショナル・NoSQL | `Relational_database` | リレーショナルデータベース |
| 14 | リレーショナル・NoSQL | `SQL` | SQL |
| 15 | リレーショナル・NoSQL | `PostgreSQL` | PostgreSQL |
| 16 | リレーショナル・NoSQL | `NoSQL` | NoSQL |
| 17 | リレーショナル・NoSQL | `MongoDB` | 代表的なドキュメントDB製品 |
| 18 | 分析基盤 | `Data_warehouse` | データウェアハウス |
| 19 | 分析基盤 | `Data_lake` | データレイク |
| 20 | 分析基盤 | `DuckDB` | 組み込み型の分析用DB |

※ 対象記事はコードに直書きせず、設定ファイル（YAML / JSON 等）で管理し、追加・削除がコード変更なしでできるようにすること。

## 技術スタック（固定）

| 用途 | 技術 |
|------|------|
| 開発環境 | Python / Docker / `gcloud` CLI |
| データ取得のバッチ | Cloud Run Jobs |
| 定期実行 | Cloud Scheduler |
| 生データ保存 | Cloud Storage |
| データ蓄積・集計 | BigQuery |
| 分析結果API | FastAPI + Cloud Run Service |
| コンテナ管理 | Artifact Registry |
| シークレット・権限 | Secret Manager / IAM（サービスアカウント） |
| 監視 | Cloud Logging / Cloud Monitoring |
| CI/CD（Phase 6） | Cloud Build（GitHub 連携） |
| 可視化 | Looker Studio |

# 課題詳細

## 背景
弊社はAI構築を主軸としており、モデルや分析を「ローカルで作って終わり」ではなく、クラウド上で継続的に動かしてお客様に届けることが求められます。
データサイエンティスト・AIエンジニアとして働くうえでも、クラウドの基礎体力はどの現場でも前提になります。
本課題では分析の高度さは問わず、**クラウド上にデータ基盤を一人で構築・運用できること** をゴールとします。

## やること（課題時間：約25時間目安）

各フェーズの終わりにメンター（田中）へ進捗を共有してください。
また、各フェーズで **「学んだこと・詰まったこと・どう解決したか」を `docs/catchup_log.md` に記録** してください（評価対象です）。

### Phase 0: クラウドの土台を理解する（約3h）
* 以下を自分の言葉でまとめる（`docs/gcp_basics.md`）。
    * プロジェクト・リージョン・課金の仕組み、無料枠
    * IAM（ユーザー / サービスアカウント / ロール）の考え方と「最小権限の原則」
    * IaaS / PaaS / サーバーレスの違いと、Cloud Run がどこに位置するか
* `gcloud` CLI をセットアップし、ログイン・プロジェクト設定まで行う。
* **予算アラート** を設定する（意図しない課金を防ぐ習慣をつける）。

### Phase 1: Docker と Cloud Run 入門（約4h）
* ローカルで Docker をインストールし、簡単な FastAPI アプリ（`/health` を返すだけ）をコンテナで動かす。
* そのコンテナを Artifact Registry に push し、Cloud Run Service にデプロイして公開URLから叩けることを確認する。
* 以下を確認・記録する。
    * ポート（`PORT` 環境変数）、環境変数の渡し方、コールドスタート
    * Cloud Logging でアプリのログを見る方法
    * 認証あり / なし（`--allow-unauthenticated`）の違い

### Phase 2: データ取得バッチと Cloud Storage（約4h）
* Wikimedia Pageviews API から、上記20記事の日次閲覧数を取得する Python スクリプトを作る。
    * 初回は **過去1年分をまとめて取得（バックフィル）** し、以降の定期実行では前日分だけを取得する。
    * `agent=user`（bot を除く）を指定すること。
* 取得結果（JSON / CSV）を Cloud Storage に日付ごとに保存する（例: `gs://<bucket>/raw/2026-10-01.json`）。
* スクリプトをコンテナ化し、**Cloud Run Jobs** として実行できるようにする。
* Job 用の **専用サービスアカウント** を作り、必要な権限（Storage への書き込み等）だけを付与する。

### Phase 3: BigQuery へのデータ蓄積と SQL 集計（約4h）
* Cloud Storage の生データを BigQuery のテーブルにロードする処理を、Phase 2 の Job に組み込む。
    * **同じ日を2回実行してもデータが重複しない** ようにする（冪等性：MERGE 文や日付パーティションの上書きなど）。
* BigQuery 上で SQL による集計を行う。
    * 記事ごとの7日移動平均、前週比、月次の合計
    * カテゴリ別の合計と、カテゴリ内でのシェアの推移（例: グラフデータ領域で Neo4j と Knowledge graph のどちらが伸びているか）
    * 直近3か月で前年同期比の伸びが大きい記事のランキング、急上昇した日の検出
* パーティション分割・クエリのスキャン量（=料金）の確認方法を理解する。

### Phase 4: 定期実行と監視（約3h）
* Cloud Scheduler で Job を毎日自動実行する。
* Job が失敗したときに気づける仕組みを入れる（Cloud Monitoring のアラートでメール通知、など）。
* 少なくとも **3日分以上の自動実行の実績** をログとデータで示す。

### Phase 5: 分析結果の公開（約4h）
* BigQuery の集計結果を返す FastAPI アプリを作り、Cloud Run Service にデプロイする。
    * `GET /health`
    * `GET /articles` … 対象記事とカテゴリの一覧
    * `GET /trend?article=Knowledge_graph&days=30` … 指定期間の閲覧数と移動平均
    * `GET /ranking?category=グラフデータ&days=90` … 指定カテゴリ内の伸び率ランキング
* API から BigQuery を読むときは、鍵ファイルではなく **Cloud Run に紐付けたサービスアカウント** で認証する。
* Looker Studio で BigQuery に接続し、推移が一目でわかるダッシュボードを作る。
    * カテゴリでの絞り込みと、「今伸びている技術」が一目でわかる表示を入れること。
* README に、ダッシュボードから読み取れるデータベース領域のトレンドを3点ほどまとめる（分析の深さは問わない）。

### Phase 6: CI/CD とまとめ（約3h）
* Cloud Build と GitHub を連携し、main ブランチへの push で API が自動デプロイされるようにする。
* README に以下をまとめる。
    * 最終的な構成図と、各サービスを選んだ理由
    * IAM（どのサービスアカウントに何の権限を付けたか、なぜ必要か）
    * 月額コストの概算と、コストを抑えるために工夫したこと
    * 詰まった箇所とどう解決したか、振り返り

## 発展課題（任意・余力があれば）
* Terraform でインフラ（バケット・データセット・サービスアカウント・Scheduler 等）をコード化する。
* 日本語版 Wikipedia（`ja.wikipedia`）の対応記事も取得し、日英で注目度の差を比較する。
* BigQuery ML で閲覧数の簡単な時系列予測（ARIMA_PLUS）を行い、API から予測値も返す。**研究で機械学習を扱っているので、ぜひ挑戦してください。** 余裕があれば、Vertex AI で学習したモデルとの比較も歓迎です。
* API に認証をかけ、社内メンバーだけが叩けるようにする（IAP や IDトークン認証など）。

## 補足
* **評価ポイント**
    * 共通コア
        1. Google Cloud のキャッチアップ / Cloud Run デプロイ完遂（公開URL）
        2. 未経験技術の自走キャッチアップ
        3. README 報告の質
    * 課題固有
        4. **クラウドの基礎理解**: IAM・サービスアカウント・課金・リージョンなどを自分の言葉で説明できるか
        5. **パイプラインの完成度**: 取得 → 保存 → 蓄積 → 公開が、人の手を介さず毎日自動で回っているか
        6. **堅牢性・運用性**: 冪等性、失敗時の通知、ログで原因を追えるか
        7. **セキュリティとコスト意識**: 最小権限、鍵を使わない認証、予算アラート、コスト見積もり
* 分析の高度さは評価対象ではありません。**クラウド上で「動き続ける」ものを作り切ること** を最優先にしてください。
* 詰まったら公式ドキュメントとエラーメッセージ・Cloud Logging を確認し、30分調べても解決しなければメンターに相談してください（何を試したかも添えて）。
* データ取得APIには過度な負荷をかけないこと（適切なリクエスト間隔・User-Agent の設定）。
* API キー・サービスアカウント鍵はリポジトリに直書きしないこと。そもそも **サービスアカウント鍵（JSON）は作らずに済む構成** を目指してください。
* 使い終わったリソースの削除方法も README に記載すること。
* **AIツールの使い方について**
    * 実装は、できるだけ AIエージェント（Claude Code / Cursor のエージェント機能 / Codex 等にコードを書かせる使い方）は使わず、自分の手で書いてください。クラウドのキャッチアップが目的なので、自分でコマンドを打ち、設定し、詰まる経験そのものが大事です。
    * 一方で、わからないことの質問・エラーメッセージの解説・概念の理解などに ChatGPT / Claude 等を使うのは大丈夫です！ どんどん活用してください。
    * いずれの場合も、コマンドや設定の意味を自分の言葉で説明できるようにしてください。

## 提出物
1. ソースコード一式（取得バッチ・API・Dockerfile・SQL・Cloud Build 設定）
2. `docs/gcp_basics.md`（クラウドの基礎まとめ）
3. `docs/catchup_log.md`（フェーズごとの学び・詰まり・解決の記録）
4. デプロイ済みAPIの公開URL と Looker Studio ダッシュボードのURL
5. 最終報告 README（構成図・IAM設計・コスト・振り返り）

提出は本ディレクトリ（`OJT/INTERN/Assignment/鈴木翔/`）配下にコミットしてください。

# 参考URL
* Google Cloud 概要: https://cloud.google.com/docs/overview
* gcloud CLI: https://cloud.google.com/sdk/docs/install
* IAM の概要: https://cloud.google.com/iam/docs/overview
* 予算アラート: https://cloud.google.com/billing/docs/how-to/budgets
* Docker 入門: https://docs.docker.com/get-started/
* Cloud Run（Python）クイックスタート: https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service
* Cloud Run Jobs: https://cloud.google.com/run/docs/create-jobs
* Cloud Scheduler: https://cloud.google.com/scheduler/docs
* Cloud Storage: https://cloud.google.com/storage/docs
* BigQuery: https://cloud.google.com/bigquery/docs
* Cloud Monitoring アラート: https://cloud.google.com/monitoring/alerts
* Cloud Build（GitHub 連携）: https://cloud.google.com/build/docs/automating-builds/github/build-repos-from-github
* Looker Studio: https://lookerstudio.google.com/
* Wikimedia Pageviews API: https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html
* FastAPI: https://fastapi.tiangolo.com/