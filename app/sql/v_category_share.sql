CREATE OR REPLACE VIEW wiki_trend.v_category_share AS
SELECT category, SUM(views) AS total,
  SUM(views) / SUM(SUM(views)) OVER () AS share
FROM wiki_trend.pageviews
GROUP BY category
