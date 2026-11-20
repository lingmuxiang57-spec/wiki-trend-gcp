from fastapi import FastAPI, HTTPException, Query
from google.cloud import bigquery
import os
app_env = os.environ.get('APP_ENV', "local")

app = FastAPI()
BQ_DATASET = os.environ.get("BQ_DATASET", "wiki_trend")  # BigQuery のデータセット名
bq = bigquery.Client()  # BigQuery クライアントを作成


@app.get("/health")
async def health_check():
    return {"status": "healthy", "env": app_env}
@app.get("/articles")
def list_articles():
    sql=f"""
    SELECT DISTINCT category, article
    FROM {BQ_DATASET}.pageviews
    ORDER BY category, article
    """
    rows = bq.query(sql).result()
    return [dict(row) for row in rows]
@app.get("/trend")
def get_trend(
    article: str,
    days: int = Query(30, ge=1, le=90),
):
    sql = f"""
    SELECT date, views, ma7
    FROM {BQ_DATASET}.v_ma7
    WHERE article = @article
      AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL @days DAY)
    ORDER BY date
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("article", "STRING", article),
            bigquery.ScalarQueryParameter("days", "INT64", days),
        ]
    )
    rows = list(bq.query(sql, job_config=job_config).result())

    if not rows:
        raise HTTPException(status_code=404, detail="Article not found")
    return [dict(row) for row in rows]
@app.get("/ranking")
def get_ranking(
    category: str,
    days: int = Query(30, ge=1, le=90),
):
    sql = f"""
    WITH t AS (
      SELECT
        article,
        category,
        SUM(IF(date >  DATE_SUB(CURRENT_DATE(), INTERVAL @days DAY), views, 0)) AS recent,
        SUM(IF(date >  DATE_SUB(CURRENT_DATE(), INTERVAL @days * 2 DAY)
           AND date <= DATE_SUB(CURRENT_DATE(), INTERVAL @days DAY), views, 0)) AS prev
      FROM {BQ_DATASET}.pageviews
      WHERE category = @category
      GROUP BY article, category
    )
    SELECT *,
      SAFE_DIVIDE(recent, prev) - 1 AS yoy,
      RANK() OVER (ORDER BY SAFE_DIVIDE(recent, prev) DESC) AS rnk
    FROM t
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("category", "STRING", category),
            bigquery.ScalarQueryParameter("days", "INT64", days),
        ]
    )
    rows = list(bq.query(sql, job_config=job_config).result())

    if not rows:
        raise HTTPException(status_code=404, detail="Category not found")
    return [dict(row) for row in rows]
