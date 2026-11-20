CREATE OR REPLACE VIEW wiki_trend.v_ma7 AS
SELECT
  date,
  article,
  category,
  views,
  AVG(views) OVER (
    PARTITION BY article
    ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS ma7
FROM wiki_trend.pageviews