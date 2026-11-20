CREATE OR REPLACE VIEW wiki_trend.v_wow AS
SELECT
  date,
  article,
  category,
  views,
  LAG(views, 7) OVER (
    PARTITION BY article
    ORDER BY date
  ) AS views_prev_week,
    SAFE_DIVIDE(views, LAG(views, 7) OVER (
    PARTITION BY article
    ORDER BY date
  )) - 1 AS wow
FROM wiki_trend.pageviews