CREATE TABLE
  wiki_trend.pageviews (date DATE, article STRING, category STRING, views INT64)
PARTITION BY
  date
CLUSTER BY
  category, article;
