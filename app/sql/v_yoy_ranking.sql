CREATE OR REPLACE VIEW wiki_trend.v_yoy_ranking AS
WITH t AS (
  SELECT
    article,
    category,
    SUM(IF(date >  DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH), views, 0)) AS recent,
    SUM(IF(date >  DATE_SUB(CURRENT_DATE(), INTERVAL 15 MONTH)
       AND date <= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH), views, 0)) AS last_year
  FROM wiki_trend.pageviews
  GROUP BY article, category
)
SELECT *,
  SAFE_DIVIDE(recent, last_year) - 1 AS yoy,
  RANK() OVER (ORDER BY SAFE_DIVIDE(recent, last_year) DESC) AS rnk
FROM t