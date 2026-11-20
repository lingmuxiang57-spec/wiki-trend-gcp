# Phase 0
## 学んだこと
- プロジェクト名とプロジェクトIDは別物なので、混同しないようにする
- アカウントについても同様に、メールアドレス（Googleアカウント）と請求アカウントIDを混同しないようにする

## 詰まったこと
### 1. プロジェクトIDを間違えた
- 原因：プロジェクトIDを入れるべきところに、プロジェクト名（表示名）を入れてしまっていた
- 解決：`gcloud projects list` で正しいプロジェクトIDを確認した

### 2. アカウントIDを間違えた
- 原因：`--billing-account=` に、請求アカウントIDではなくメールアドレスを入れてしまっていた
- 解決：`gcloud billing accounts list` で請求アカウントIDを確認した

### 3. 請求アカウントが紐づいていなかった
- 気づいたきっかけ：`gcloud billing accounts list` の結果が `Listed 0 items` だった
- 原因：請求アカウント自体をまだ作成していなかった
- 解決：コンソールの画面から請求アカウントを作成した

### 4. PowerShell でカンマを含む引数が壊れた
- 状況：`gcloud billing budgets create` で予算アラートを作成しようとした
- エラー：`argument --threshold-rule: invalid ... value: 'percent=1.0 basis=forecasted-spend'`
- 原因：PowerShell はクォートしていないカンマを配列の区切りとして扱うため、引数が分割されて gcloud に渡っていた
- 解決：引数全体をシングルクォートで囲んだ（`'--threshold-rule=...'`）

## 次に活かすこと
- IDを入れる前は、`gcloud projects list` / `gcloud billing accounts list` などの list コマンドで確認する

# Phase 1
## 確認・記録した項目
- PORT：コンソールのリビジョン →「コンテナ」で、コンテナポートが `8080` になっていることを確認した（[画像](images/コンテナポート番号.png)）
- 環境変数：`APP_ENV=prod` を設定し、`/health` が `{"status":"healthy","env":"prod"}` を返すことを確認した。未設定のときは既定値の `local` が返った（[画像](images/コンテナポート番号.png)）
- コールドスタート：放置後の1回目は **約3,176ms**、直後の2回目は **約548ms**（[1回目](images/コールドスタート1回目.png) / [2回目](images/コールドスタート2回目.png)）
- Cloud Logging：`gcloud run services logs read` で、`GET 200 .../health` のリクエストログと、uvicorn の起動ログ（`Started server process` → `Uvicorn running on http://0.0.0.0:8080`）が確認できた（[画像](images/Cloud_Logging.png)）
- 認証あり／なし：`allUsers` の `roles/run.invoker` を外すと、認証なしは `403 Forbidden`、IDトークン付きは `200 OK` になった

## 詰まったこと
### 1. Docker をインストールしたのに `docker` が認識されない
- エラー：`用語 'docker' は、コマンドレット、関数、…として認識されません`
- 原因：インストール先と PATH の反映のタイミング
- 解決：PowerShell を開き直したら認識された

### 2. pip install で他のライブラリが壊れた
- エラー：`dify-plugin 0.7.4 requires pydantic>=2.8.2, but you have pydantic 1.10.27 which is incompatible.` など
- 原因：`requirements.txt` で古いバージョン（`fastapi==0.68.0` / `uvicorn==0.15.0`）を指定していた
- 解決：新しいバージョン（`fastapi==0.136.1` / `uvicorn==0.46.0`）に固定し直した

### 3. Dockerfile のビルドエラー
- エラー：`FROM requires either one or three arguments` / `COPY requires at least two arguments`
- 原因：Dockerfile の中身に誤りがあった
  - `FROM` にイメージ名がなく `3.13` だけになっていた（`python: 3.13-slim` のように `:` の後にスペースを入れてもエラーになった）
  - `COPY` の引数が1つしかなかった（コピー元とコピー先の2つが必要）。また、`api` フォルダでビルドしているのに `api/` を付けていた
- 解決：`FROM python:3.13-slim` に直し、`COPY` をコピー元・コピー先の2つの引数にして `api/` を外した

### 4. `http://localhost:8080/health` が開けない
- 原因：コンテナが動いていなかった（Dockerfile のビルドが失敗していた）
- 解決：Dockerfile の中身を修正し、ビルドを成功させた

### 4-2. `http://0.0.0.0:8080` がブラウザで開けない
- 原因：`0.0.0.0` は「すべての入り口で待ち受ける」というサーバー側の設定値で、ブラウザでアクセスする宛先ではない
- 解決：`http://localhost:8080/health` を開いた

### 5. `port is already allocated`
- 原因：前に `docker run` で起動したコンテナがまだ動いていて、PC の 8080 番を使ったままだった。同じポートを2つのコンテナで同時に使うことはできない
- 解決：`docker ps` で動いているコンテナを確認し、`docker stop` で古いコンテナを止めた

### 6. `The required property [project] is not currently set`
- 原因：gcloud のプロジェクトが未設定だった
- 解決：`gcloud config set project pantarhei-wiki-trend-20261116` を実行した

### 7. Cloud Run のデプロイで `Image ... not found`
- 原因：`main.py` を直して `docker build` はしたが、`v2` の名前を付けて Artifact Registry に push していなかったため、Cloud Run が `v2` を取りに行っても見つからなかった
- 解決：`docker tag` で `v2` を付けて `docker push` し、その後にデプロイし直した

### 8. Cloud Run で `env` が `prod` ではなく `local` になった
- 原因：Cloud Run に環境変数が設定されていなかった
- 解決：環境変数だけを追加した（`gcloud run services update --update-env-vars=APP_ENV=prod`）

## 学んだこと
- Cloud Run はイメージを Artifact Registry から取ってくるので、コードを変えたら「build → tag → push → deploy」の4ステップが必要
- Cloud Run の公開・非公開は `allUsers` に `roles/run.invoker` を付けるかどうかという IAM の設定で、再デプロイなしで切り替えられる
- pip をグローバル環境に入れると、他のプロジェクトとバージョンがぶつかる。Docker や venv はこれを防ぐためのもの

## 次に活かすこと
- 作業を始める前に `gcloud config list` で、アカウント・プロジェクト・リージョンを確認する
- デプロイの前に `gcloud artifacts docker images list --include-tags` で、イメージが push されているか確認する
- Python のライブラリは venv の中に入れ、グローバル環境を汚さない

# Phase 2
## 実施した内容
- `app/config/articles.yaml` に20記事とカテゴリを定義（コードに記事名を書かない）
- `app/batch/main.py`：Wikimedia Pageviews API（`en.wikipedia` / `all-access` / `user` / `daily`）から取得し、日付ごとに NDJSON にして `gs://pantarhei-wiki-trend-20261116-raw/raw/YYYY-MM-DD.json` に保存
- `MODE` 環境変数で `daily`（前日分）と `backfill`（過去1年分）を切り替え。日付は UTC 基準
- backfill を実行し、365ファイルを保存
- コンテナ化して Artifact Registry に push し、Cloud Run Jobs（`wiki-batch`）として実行（`1 / 1 complete`）
- Job 専用のサービスアカウント `wiki-batch` を作成し、バケット単位で `roles/storage.objectUser` だけを付与。鍵ファイルは作成していない

## 詰まったこと
### 1. `articles.yaml` が読み込めない
- エラー：`yaml.scanner.ScannerError: while scanning a block scalar`
- 原因：課題README の Markdown の表をそのまま貼り付けていて、YAML の書き方になっていなかった（`|` は YAML では特別な記号）
- 解決：`articles:` の下に、`- category:` / `article:` の形のリストで書き直した

### 2. `FileNotFoundError: 'config/articles.yaml'`
- 原因：相対パスは、`main.py` の場所ではなく実行したときのカレントフォルダを起点に解釈される。`batch` フォルダの中から実行していた
- 解決：`config/` があるフォルダから `python batch/main.py` を実行した

### 3. User-Agent のエラー
- エラー：`UnicodeEncodeError: 'latin-1' codec can't encode characters`
- 原因：User-Agent に「連絡先」という日本語をそのまま入れていた。HTTP ヘッダーには ASCII しか使えない
- 解決：実際の連絡先（半角英数字）に置き換えた

### 4. `timeout` に `socket.timeout` が入っていた
- 原因：`timeout=timeout` と書いたため、エディタが `from socket import timeout`（例外クラス）を自動で追加した。requests には秒数を渡す必要がある
- 解決：import を削除し、`timeout=30` にした

### 5. GCS に保存したファイルが NDJSON になっていなかった
- 原因：`json.dumps(records)` でリスト全体を1つの JSON 配列にしていた。BigQuery が読めるのは1行1レコードの NDJSON
- 解決：1件ずつ `json.dumps` して、`"\n".join(...)` で改行でつなげた

### 6. `Unknown MODE: backfill`
- 原因：`get_date_range` に `backfill` の分岐がなく、課題にない `weekly` の分岐が入っていた
- 解決：`weekly` を `backfill`（365日前〜前日）に書き換えた

### 7. Docker の `COPY` でファイルが見つからない
- エラー：`Could not open requirements file: [Errno 2] No such file or directory: 'batch/requirements.txt'`
- 原因：`COPY` のコピー先を `.` にしていたので、ファイルが `/app/` の直下に置かれ、`/app/batch/` を探す `RUN` や `CMD` と食い違っていた
- 解決：コピー先を `batch/` や `config/` にして、イメージの中もローカルと同じ構成にした

### 8. `failed to connect to the docker API`
- 原因：Docker Desktop（エンジン）が起動していなかった。`docker` コマンド（クライアント）とエンジンは別のもの
- 解決：Docker Desktop を起動し、`docker version` で `Server:` が表示されることを確認した

### 9. ローカルの Docker で `DefaultCredentialsError`
- 原因：ローカルの ADC の認証情報は PC の中にあり、隔離されたコンテナからは見えない。Cloud Run Jobs では、紐付けたサービスアカウントの認証情報が自動で使われる
- 解決：ローカルの Docker では API の取得部分までを確認し、GCS への保存は Cloud Run Jobs で確認した

### 10. Cloud Run Jobs で `環境変数 BUCKET が設定されていません`
- 原因：`--set-env-vars=MODE=daily,BUCKET=...` のカンマを PowerShell が配列の区切りとして解釈し、`MODE` の値が `daily BUCKET=...` になっていた（Phase 0 の4番と同じ仕組み）
- 解決：Cloud Logging でアプリのメッセージを確認し、`jobs describe` で実際の値を確認した。引数全体をシングルクォートで囲んで `jobs update` し直した

## 学んだこと
- 同じコードでも、実行環境によって認証の出どころが違う（ローカルは ADC、Cloud Run はサービスアカウント）。そのため、鍵ファイルを作らずに済む
- API へのリクエストは記事単位で期間をまとめて取得し、保存は日付単位に組み替えることで、リクエスト数を抑えられる（1年分でも20リクエスト）
- Cloud Run Jobs は Service と違い、HTTP の待ち受けが不要で、処理が終わったら終了する

## 次に活かすこと
- Job が失敗したら、まず Cloud Logging でアプリのメッセージを確認し、次に `describe` で実際の設定値を確認する
- Docker の `COPY` は、コピー元（PC 側）とコピー先（イメージ側）を区別して考える
- 書いたコードは1つ書くたびに実行し、出力を確認してから次に進む

# Phase 3
## 実施した内容
- データセット `wiki_trend`（`asia-northeast1`）に、本体テーブル `pageviews`（`date DATE, article STRING, category STRING, views INT64`）を作成。`date` で日単位パーティション、`category, article` でクラスタリング（`app/sql/create_table.sql`）
- 冪等なロード：GCS → ステージングテーブル `pageviews_staging` に毎回入れ替えでロード（`WRITE_TRUNCATE`）→ `date` + `article` をキーに本体へ `MERGE`（`app/sql/create_staging.sql` / `app/sql/merge.sql`）
- `app/batch/main.py` に、GCS 保存後のロードと MERGE を組み込み、Cloud Run Jobs（`wiki-batch:v2`）で実行（`1 / 1 complete`）
- Job の SA `wiki-batch` に、プロジェクト単位で `roles/bigquery.jobUser`、データセット `wiki_trend` 単位で `roles/bigquery.dataEditor` を付与
- 集計ビューを6本作成（`app/sql/v_*.sql`）
  - `v_ma7`：7日移動平均
  - `v_wow`：前週比
  - `v_monthly`：月次合計
  - `v_category_share`：カテゴリ合計とシェア
  - `v_yoy_ranking`：直近3か月の前年同期比ランキング
  - `v_spike`：急上昇日（`views` が7日移動平均の2倍を超えた日）

## 確認・記録した項目
- 冪等性：本体 10,040 行（502日 × 20記事）。MERGE を2回実行しても、Job を実行しても 10,040 行のままで、日付と記事が重なる行は0件
- スキャン量（dry run）：全期間の `SELECT *` は **621,476 bytes**、`WHERE date >= '2026-11-01'` で絞ると **21,046 bytes**（約 1/30）。17日 ÷ 502日 ≈ 3.4% なので、パーティションで該当日だけを読んでいることが確認できた
- 自動リトライ：権限エラーで失敗した Job は、初回 + リトライ3回の計4回実行されていた（Job の既定 `maxRetries: 3`）

## 詰まったこと
### 1. `bq load` を2回実行したら、1日あたりの件数が 20 → 40 になった
- 原因：`bq load` は既定で「追加（append）」なので、同じファイルを2回ロードすると同じ行が2つずつ入る
- 解決：ステージングを毎回入れ替えでロード（`--replace`）し、`MERGE` で本体に反映する形にした

### 2. MERGE をしたのに、本体が 20,080 行のままだった
- 原因：MERGE は「これから重複が生まれること」は防げるが、すでにある重複は消せない。本体を `TRUNCATE` せずに MERGE していた
- 気づいたきっかけ：MERGE の影響行数が、1日分（20行）のはずなのに 40 だった
- 解決：`TRUNCATE` で本体を空にしてから、MERGE し直した

### 3. Cloud Run Jobs で `403 Access Denied ... Permission bigquery.tables.create denied`
- 原因：Job の SA に、データセットへの書き込み権限（`bigquery.dataEditor`）がなかった。`jobUser` はジョブを実行する権利だけで、データを触る権利は別
- 解決：データセット `wiki_trend` に `bigquery.dataEditor` を付けた

### 4. `bq add-iam-policy-binding` で権限が付かなかった
- 原因：データセット単位の IAM を操作する `bq` のコマンドは、許可リスト（allowlisting）に登録されたプロジェクトでしか使えなかった
- 解決：コンソールで SQL の `GRANT ... ON SCHEMA ... TO "serviceAccount:..."` を実行して付けた

### 5. PowerShell で `create_staging.sql` と打ったら「認識されません」のエラーになった
- 原因：`.sql` ファイルはプログラムではないので、PowerShell では実行できない。SQL を実行するのは BigQuery
- 解決：BigQuery コンソールのエディタに中身を貼って実行した（PowerShell からなら `Get-Content -Raw ... | bq query --use_legacy_sql=false`）

### 6. 集計 SQL で `Syntax error: Unclosed identifier literal`
- 原因：列名が間違っていた
- 解決：正しい列名にした

## 学んだこと
- MERGE は新しい重複を防ぐが、既存の重複は消さない。最初にデータをきれいにしておく必要がある
- パーティション列で `WHERE` を絞ると、読むデータ量（＝料金）が減る。dry run（`bq query --dry_run`）で、実行前に確かめられる
- ファイルを直しただけでは BigQuery のビューは変わらない。`CREATE OR REPLACE VIEW` を実行し直す必要がある

## 次に活かすこと
- 何がいつ実行されたかは、BigQuery のジョブの履歴（`bq ls -j` / コンソールの「個人の履歴」）で後から追える
- 権限エラーが出たら、エラー文の「拒否された権限名」と「対象（プロジェクト／データセット）」を読んで、どのロールをどこに付けるかを決める
- SQL は、まず `SELECT` だけで実行して数字を確かめてから、ビューにする

# Phase 4
## 実施した内容
- Cloud Scheduler のジョブ `wiki-batch-daily` を作成。毎日 15:00（`Asia/Tokyo`、cron `0 15 * * *`）に、Cloud Run Admin API の `jobs/wiki-batch:run` を POST で呼ぶ
- Scheduler 専用の SA `wiki-scheduler` を作成し、Job `wiki-batch` だけに `roles/run.invoker` を付与。Scheduler は OAuth トークン（`cloud-platform` スコープ）でこの SA として API を呼ぶ
  - 起動役（`wiki-scheduler`）と実行役（`wiki-batch`）を分けたので、Scheduler の SA は GCS や BigQuery に触れない
- 前日分の公開遅れ対策として、`MODE=daily` の取得範囲を「3日前〜昨日」に変更し、`wiki-batch:v3` として反映
- Cloud Monitoring で、メールの通知チャネルとアラートポリシー `wiki-batch failed` を作成（指標 `run.googleapis.com/job/completed_execution_count`、`result = failed`、5分間の合計が 0 より大きい）
- `gcloud run jobs execute ... --update-env-vars=MODE=broken` で、その回だけわざと失敗させ、通知メールが届くことを確認

## 確認・記録した項目
- Scheduler 経由の実行：`RUN BY` が `wiki-scheduler@...` の実行が ✔（`1 / 1`）になった
- 公開の遅れ：2026-11-20 12:36（日本時間）の時点では、11-19 分は20記事中15記事しか公開されていなかった（`Saved 15 records`）。翌日の実行で、3日分の範囲に入って取り直される
- 失敗通知：Job が失敗してから **約5〜8分**でメールが届いた。リトライを含めて4回失敗したが、メールは **1通**だった（同じインシデントとしてまとめられた）
- 3日分の自動実行の実績：（実行履歴・ログ・日付ごとの件数を記入）

## 詰まったこと
### 1. `add-iam-policy-binding` で `PERMISSION_DENIED: Permission denied on 'locations/asis-northeast1' (or it may not exist)`
- 原因：リージョン名を `asis` と打ち間違えていた。GCP は、存在しないものを指定したときも「権限がない」と同じ文言を返すことがある
- 解決：`asia-northeast1` に直した

### 2. `INVALID_ARGUMENT: Invalid service account (wiki-schedulerpantarhei-...)`
- 原因：SA のメールアドレスの `@` が抜けていた（打ち忘れ、または PowerShell が `@` を特別な記号として扱った）
- 解決：`'--member=serviceAccount:...'` のように、引数全体をシングルクォートで囲んだ

### 3. Scheduler のジョブに `oauthToken`（Scheduler が名乗る SA）が設定されていなかった
- 原因：行の継続（`` ` ``）や `@` の扱いで、最後の引数 `--oauth-service-account-email` が落ちていた
- 気づいたきっかけ：作り直そうとして `ALREADY_EXISTS` のエラーになり、`describe` で設定を見たら `oauthToken` がなかった
- 解決：`gcloud scheduler jobs update http` で、`--oauth-service-account-email` だけを追加した

### 4. Scheduler からの初回実行で、Job が `404 Not Found` で失敗した
- 原因：Wikimedia で、前日分（11-19）のデータがまだ公開されていなかった。記事によって公開のタイミングも違った。Scheduler から Job を起動する部分は成功していた（`RUN BY` が `wiki-scheduler@...`）
- 解決：`MODE=daily` でも「3日前〜昨日」を取るようにした。取りこぼした日は翌日の実行で埋まり、MERGE があるので取り直しても重複しない

### 5. Job のイメージのタグ名が `___` になっていた
- 原因：Phase 3 で、コマンド例の `___`（穴埋めの目印）をそのまま打っていた
- 気づいたきっかけ：`gcloud run jobs describe` でイメージ名を見た
- 解決：`v3` を push して、Job を `v3` に切り替えた

### 6. `docker build` で `open Douckerfile: no such file or directory`
- 原因：ファイル名（`Douckerfile`）とイメージ名（`wili-batch`）を打ち間違えていた。イメージ名を間違えたまま進むと、古いイメージに新しいタグを付けて push してしまう危険があった
- 解決：打ち直した（Tab キーでファイル名を補完できる）

### 7. ローカルの実行で `環境変数 BUCKET が設定されていません` → 設定しようとしたら `トークン '$env:MODE' を使用できません`
- 原因：PowerShell の環境変数は、ウィンドウを閉じると消える。設定し直そうとしたら、コピーしたときに改行が消えて、複数のコマンドが1行につながっていた
- 解決：1行ずつ実行した（または `;` で区切った）

## 学んだこと
- Google の API（Cloud Run Admin API など）を呼ぶときは OAuth トークン、自分の Cloud Run Service を呼ぶときは ID トークン。宛先によって使うトークンが違う
- 失敗通知は「わざと失敗させて」確かめないと、本当に届くか分からない。`gcloud run jobs execute --update-env-vars=...` を使えば、Job の設定を変えずにその回だけ失敗させられる

## 次に活かすこと
- `@` やカンマを含む引数は、最初からシングルクォートで囲む
- エラーが出たら、どの部分（Scheduler／Job の起動／Job の中身）で失敗したかを切り分けてから直す

# Phase 5
## 実施した内容
- `api/main.py`（FastAPI）に4つのエンドポイントを実装
  - `GET /health`：動作確認
  - `GET /articles`：`pageviews` から `SELECT DISTINCT category, article`
  - `GET /trend?article=...&days=...`：ビュー `v_ma7` から、直近 N 日の `views` と7日移動平均
  - `GET /ranking?category=...&days=...`：指定カテゴリの記事を、「直近 N 日の合計 ÷ その前の N 日の合計 − 1」の伸び率で順位付け
- 利用者が入力する値（`article` / `category` / `days`）は、すべてパラメータ化クエリ（`@article` など + `ScalarQueryParameter`）で渡す。`days` は `Query(ge=1, le=90)` で範囲を制限
- 該当データが0行なら `404` を返す
- API 専用の SA `wiki-api` を作成し、データセット `wiki_trend` に `roles/bigquery.dataViewer`（読み取りだけ）、プロジェクトに `roles/bigquery.jobUser` を付与。鍵ファイルは作らず、Cloud Run に紐付けた SA で認証
- Cloud Run Service `wiki-api` としてデプロイ（https://wiki-api-32614732480.asia-northeast1.run.app）。データは Wikipedia の公開データなので、認証なしで公開した
- Looker Studio でダッシュボードを作成（[画像](images/ダッシュボード.png)）
  - カテゴリのプルダウン（フィルタ）
  - 記事ごとの閲覧数の折れ線グラフ（ビュー `v_ma7`）
  - 「今伸びている技術」の表（ビュー `v_yoy_ranking`、伸び率の降順）。表の行をクリックすると、折れ線グラフがその記事に絞られる
- ダッシュボードから読み取れるトレンドを3点、`docs/findings.md` にまとめた

## 確認・記録した項目
- 公開 URL での動作：`/health`（`env: prod`）・`/articles`（20件）・`/trend`・`/ranking` がすべて 200
- 入力のチェック：存在しない記事・カテゴリは 404、`days=9999` は 422（FastAPI が自動で返す）
- SQL インジェクション対策：`/trend?article=' OR 1=1 --` を送っても、SQL として解釈されず、ただの記事名として扱われて 404 になった
- 権限：SA `wiki-api` の権限だけで、鍵ファイルなしで BigQuery を読めた

## 詰まったこと
### 1. `pip install -r requirements.txt` で `Invalid requirement: pip install --upgrade ...`
- 原因：`requirements.txt` に、コマンド（`pip install --upgrade google-cloud-storage`）をそのまま書いていた。`requirements.txt` には「パッケージ名==バージョン」だけを書く
- 解決：その行を削除した（API は GCS を使わないので不要だった）

### 2. `/articles` を書いたのに、`api/main.py` に反映されていなかった
- 原因：新しく `articles/main.py` という別のフォルダとファイルに書いていた。エンドポイントは、1つの FastAPI アプリ（`api/main.py` の `app`）にまとめて登録する
- 解決：`api/main.py` に移し、`articles` フォルダは削除した

### 3. `/articles` が20件ではなく、全部の行（約10,040行）を返す書き方だった
- 原因：`SELECT` に `DISTINCT` がなく、日付ごとの行がすべて返る書き方だった
- 解決：`SELECT DISTINCT category, article` にした

### 4. ブラウザで `ERR_CONNECTION_REFUSED`
- 原因：uvicorn が起動していなかった（`unexpected extra argument (app)` のエラーで止まっていた）。また、起動したあとも、`--port 8000` で起動したのに `localhost:8080` を開いていた
- 解決：正しく起動し、`--port` と同じ番号の URL を開いた

### 5. `uvicorn --reload` で、再起動が止まらなくなった
- 原因：`--reload` が `api` フォルダ全体（`.venv` を含む）を監視していて、OneDrive の同期などによる変化にも反応していた
- 解決：`--reload` を外し、コードを変えたら手で再起動するようにした

### 6. `gcloud run deploy` で `Invalid resource name [wiki^api]`
- 原因：日本語キーボードで、隣にある `-` と `^` を押し間違えていた
- 気づいたきっかけ：エラー文の `[ ]` の中に、実際に受け取った値が表示されていた
- 解決：`wiki-api` に打ち直した

### 7. `gcloud run deploy` で `Permission 'iam.serviceaccounts.actAs' denied ... (or it may not exist)`
- 原因：SA のメールアドレスの中のプロジェクト ID を `202261116` と打ち間違えていた（`2` が1つ多い）。存在しない SA を指定していた
- 解決：正しい ID に直した

### 8. `gcloud run deploy` で `Image ... wiki-api:v1 not found`
- 原因：`wiki-api` のイメージを、まだ build・tag・push していなかった（Phase 1 の7番と同じ）
- 解決：build → tag → push してから、デプロイし直した

## 学んだこと
- FastAPI では、引数に型と `Query(ge=..., le=...)` を書くだけで、入力のチェックと `422` を自動でやってくれる
- batch と API で SA を分け、batch は `dataEditor`（書き込み）、API は `dataViewer`（読み取りだけ）にすると、最小権限にできる

## 次に活かすこと
- デプロイの前に、イメージが push されているかを確認する（`gcloud artifacts docker images list --include-tags`。Phase 1 から2回目）
- `requirements.txt` やコードは、それぞれのファイルの役割（一覧なのか、コマンドなのか、どのアプリに属するのか）を意識して書く

# Phase 6
## 実施した内容
- プロジェクトを Git リポジトリにして、GitHub（`wiki-trend-gcp`）に push
  - `.gitignore` で `.venv/`・`__pycache__/`・ローカルの環境変数のファイル（`*.ps1`・`.env`）を除外
  - スクリーンショットは `docs/images/` にまとめ、push する前に全部の画像に個人情報が写っていないか確認した
  - 課題の説明文は `docs/assignments.md` に移し、直下の `README.md` は最終報告用にした
  - コミットのメールアドレスには、GitHub の非公開用アドレス（`...@users.noreply.github.com`）を使った
- `cloudbuild.yaml` を作成：`docker build`（`api` フォルダ）→ `docker push`（Artifact Registry）→ `gcloud run deploy wiki-api`。イメージのタグはコミットの ID（`$SHORT_SHA`）
- Cloud Build 専用の SA `wiki-cloudbuild` を作成し、次の権限を付与
  - リポジトリ `wiki-trend` に `roles/artifactregistry.writer`（イメージの push）
  - プロジェクトに `roles/run.developer`（デプロイ。IAM は変更できない `run.admin` より小さい権限）
  - SA `wiki-api` に `roles/iam.serviceAccountUser`（`wiki-api` の SA で動くサービスをデプロイするための `actAs`）
  - プロジェクトに `roles/logging.logWriter`（ビルドのログ）
- Cloud Build のトリガー `deploy-wiki-api`（`asia-northeast1`）を作成：GitHub の main ブランチへの push で `cloudbuild.yaml` を実行

## 確認・記録した項目
- `/ranking` の並び順を直したコミット（`01358c7`）を push すると、トリガーが動き、52秒でビルドが成功（`SUCCESS`）した
- Cloud Run の `wiki-api` が、新しいリビジョンでイメージ `wiki-api:01358c7` を使うようになり、公開 URL の `/ranking` が順位の順（1〜5）に並ぶようになった
- イメージのタグがコミットの ID なので、今動いている API がどのコミットから作られたかを追える

## 詰まったこと
### 1. `.gitignore` に書いたのに、画像が commit の対象から外れなかった
- 原因：2つあった
  - `.gitignore` の区切りを `\` で書いていた。`.gitignore` では Windows でも `/` を使う
  - すでに `git add` したファイルは、`.gitignore` に書いても外れない
- 解決：`/` に直し、`git rm --cached` で commit の対象から外した（PC のファイルは残る）

### 2. スクリーンショットに、メールアドレスが写っていた
- 原因：Cloud Run の Job の一覧の「作成者」の列に、Gmail のアドレスが写っていた。一度 push すると、Git の履歴に残ってしまう
- 解決：push の前に全部の画像を確認し、その画像は GitHub に上げないことにした（`.gitignore` で除外）

### 3. `README.md` が `docs` フォルダの中に、空のファイルとしてできていた
- 原因：GitHub のトップページに表示されるのは、リポジトリの直下の `README.md`。`docs` の中だと表示されない
- 解決：直下に移した（課題の説明文は `docs/assignments.md` に移した）

### 4. 最初に書いた `cloudbuild.yaml` が、このプロジェクトの設定と合っていなかった
- 原因：ネットのサンプルをもとにしたため、次の4点が合っていなかった
  - イメージの置き場所が、古い Container Registry（`gcr.io/...`）になっていた
  - ビルドの元が `.`（リポジトリの直下）で、`Dockerfile` がある `api` フォルダではなかった
  - サービス名が `panta-rhei` で、既存の `wiki-api` ではなかった（このままだと、SA も環境変数もない別のサービスができる）
  - `images:` の書き方が違った
- 解決：これまで手で打ったコマンドと同じ値に合わせて書き直した

### 5. `gcloud builds list` で `Listed 0 items.`（実際にはビルドは成功していた）
- 原因：`--region` を付けずに実行したので、`global` の一覧を見ていた。トリガーは `asia-northeast1` に作ったので、ビルドもそちらにあった
- 解決：`--region=asia-northeast1` を付けて確認した

## 学んだこと
- CI/CD の設定（`cloudbuild.yaml`）は、これまで手で打ってきたコマンドを並べたもの。手で一度やったことがあるから、何を書けばいいか分かった
- イメージのタグをコミットの ID（`$SHORT_SHA`）にすると、動いているものがどのコミットから作られたかを追えて、手でタグを付けるときの間違い（Phase 4 の `___` タグなど）もなくなる
- Git は一度 push すると履歴に残るので、個人情報や秘密の情報は、push の前に確認して除外する必要がある

## 次に活かすこと
- `git add` のあと、commit の前に `git status` で、上げたくないファイルが入っていないかを確認する
- `.gitignore` は、最初の `git add` より前に作る
