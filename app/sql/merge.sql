MERGE INTO `wiki_trend.pageviews` T
USING `wiki_trend.pageviews_staging` S
ON T.date = S.date AND T.article = S.article
WHEN MATCHED THEN
  UPDATE SET views = S.views, category = S.category
WHEN NOT MATCHED THEN
  INSERT (date, article, category, views) VALUES (S.date, S.article, S.category, S.views);