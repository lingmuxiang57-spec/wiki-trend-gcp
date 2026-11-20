CREATE OR REPLACE VIEW wiki_trend.v_monthly AS
SELECT DATE_TRUNC(date, MONTH) AS month, article, SUM(views) AS total
FROM `wiki_trend.pageviews`
GROUP BY month, article