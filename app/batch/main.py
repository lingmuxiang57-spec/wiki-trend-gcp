import json
import os
import time
import urllib.parse

import requests
import yaml
from google.cloud import storage
from datetime import datetime, timedelta, timezone
from google.cloud import bigquery

# 設定（コードに直書きせず、環境変数から読む。第2引数は既定値）
CONFIG_PATH = os.environ.get("CONFIG_PATH", "config/articles.yaml")
MODE = os.environ.get("MODE", "daily")  
USER_AGENT = os.environ.get("USER_AGENT", "...")  # 例：ツール名/0.1 (連絡先)
BUCKET = os.environ.get("BUCKET")  # GCS のバケット名
BQ_DATASET = os.environ.get("BQ_DATASET", "wiki_trend")  # BigQuery のデータセット名
API_BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"

                     # → "20261110"（文字列に変換）


def load_articles(path):
    """記事名とカテゴリのリストを返す
    [{"article": 記事名, "category": カテゴリ}, ...] の形式
    """
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["articles"]


def fetch_pageviews(article, start, end):
    """指定した記事の指定期間の閲覧数を返す
    戻り値は日付ごとの閲覧数のリスト
    [{"date": 日付, "views": 閲覧数}, ...] の形式
    """
    # API の URL を組み立てる
    # 例: https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/記事名/daily/開始日/終了日
    encoded_article = urllib.parse.quote(article, safe="")
    url = f"{API_BASE}/en.wikipedia/all-access/user/{encoded_article}/daily/{start}/{end}"

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()  # エラーがあれば例外を投げる

    data = response.json()
    results = []
    for item in data.get("items", []):
        ts = item["timestamp"]  # 例: "2023010100"
        date = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"  # "YYYY-MM-DD" 形式に変換
        results.append({"date": date, "views": item["views"]})
    return results

def save_to_gcs(client, bucket_name, date, records):
    """1日分のレコードを NDJSON にして GCS の raw/{date}.json に保存する"""
    # 1件ずつ JSON 文字列にして、改行でつなげる（NDJSON）
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    body = "\n".join(lines) + "\n"

    blob_name = f"raw/{date}.json"
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(body, content_type="application/json")
    print(f"Saved {len(records)} records to gs://{bucket_name}/{blob_name}")
    return f"gs://{bucket_name}/{blob_name}"


def get_date_range(mode):
    """MODE に応じて開始日と終了日を返す"""
    today = datetime.now(timezone.utc).date()
    if mode == "daily":
        # 昨日
        end = today - timedelta(days=1)
        start = today - timedelta(days=3)
    elif mode == "backfill":
        # 先週の月曜日から日曜日まで
        end = today - timedelta(days=1)  
        start = today - timedelta(days=today.weekday() + 500)  # 今日の500日前
    else:
        raise ValueError(f"Unknown MODE: {mode}")
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")

def load_to_staging(bq_client, uris):
    """GCS の NDJSON を BigQuery の staging テーブルにロードする"""
    dataset_id = BQ_DATASET
    table_id = "pageviews_staging"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # 上書き
    )

    load_job = bq_client.load_table_from_uri(
        uris, f"{dataset_id}.{table_id}", job_config=job_config
    )
    load_job.result()  # 完了まで待つ

    print(f"Loaded {len(uris)} files into {dataset_id}.{table_id}")

def merge_staging(bq_client):
    """staging テーブルの内容を本番テーブルにマージする"""
    query = """
    MERGE INTO `wiki_trend.pageviews` T
    USING `wiki_trend.pageviews_staging` S
    ON T.date = S.date AND T.article = S.article
    WHEN MATCHED THEN
      UPDATE SET views = S.views, category = S.category
    WHEN NOT MATCHED THEN
      INSERT (date, article, category, views) VALUES (S.date, S.article, S.category, S.views);
    """
    query_job = bq_client.query(query)
    query_job.result()  # 完了まで待つ

    print("Merged staging into main table")


def main():
    if not BUCKET:
        raise SystemExit("環境変数 BUCKET が設定されていません")

    client = storage.Client()  # ADC で認証される。1回だけ作って使い回す
    bq_client = bigquery.Client()  # ADC で認証される。1回だけ作って使い回す

    articles = load_articles(CONFIG_PATH)
    print(f"Loaded {len(articles)} articles from {CONFIG_PATH}")

    start, end = get_date_range(MODE)

    by_date = {}
    
    for article in articles:
        views = fetch_pageviews(article["article"], start, end)
        for v in views:
            record = {
                "date": v["date"],
                "article": article["article"],
                "category": article["category"],
                "views": v["views"]
            }
            if v["date"] not in by_date:
                by_date[v["date"]] = []
            by_date[v["date"]].append(record)

        time.sleep(1)  # API へのリクエスト間隔を空ける

    uris = []
    for date, records in by_date.items():
        # print(date, len(records))
        # GCS に保存
        uri = save_to_gcs(client, BUCKET, date, records)
        uris.append(uri)
    if not uris:
        raise SystemExit("No data to load into BigQuery")
    load_to_staging(bq_client, uris)
    merge_staging(bq_client)

if __name__ == "__main__":
    main()