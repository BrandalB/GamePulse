-- Portable SQL: SQLite and PostgreSQL (PostgreSQL uses CAST(price AS NUMERIC) for currency analysis).
-- Total games, review count and weighted positive share
SELECT COUNT(*) AS titles,
       SUM(COALESCE(review_count,0)) AS total_reviews,
       1.0*SUM(COALESCE(positive,0))/NULLIF(SUM(COALESCE(review_count,0)),0) AS positive_review_share
FROM games;

-- New releases by year
SELECT release_year, COUNT(*) AS released_titles
FROM games WHERE release_year IS NOT NULL
GROUP BY release_year ORDER BY release_year;

-- Genre distribution; multi-label genres can overlap
SELECT gg.genre, COUNT(*) AS titles,
       SUM(COALESCE(g.review_count,0)) AS reviews,
       AVG(CASE WHEN g.price>0 THEN g.price END) AS mean_paid_price
FROM game_genres gg JOIN games g ON g.appid=gg.appid
GROUP BY gg.genre ORDER BY titles DESC;

-- Heavily reviewed games (more than 1,000 reviews)
SELECT name, review_count, positive_rate, price, owners_low, owners_high
FROM games WHERE review_count>=1000
ORDER BY review_count DESC LIMIT 25;

-- Games without valid ownership estimates
SELECT COUNT(*) AS owner_range_missing
FROM games WHERE owners_low IS NULL OR owners_high IS NULL;

-- Catalog cohorts are NOT historic revenue or historic review snapshots.

-- Annual genre release counts. Game counts overlap across genres.
SELECT gg.genre, g.release_year, COUNT(DISTINCT g.appid) AS release_count,
       SUM(COALESCE(g.review_count,0)) AS snapshot_review_count
FROM game_genres gg JOIN games g ON g.appid=gg.appid
WHERE g.release_year BETWEEN 2019 AND 2024
GROUP BY gg.genre, g.release_year
ORDER BY gg.genre, g.release_year;

-- Raw publisher-field footprint. Multi-credit comma-separated values
-- remain grouped as raw strings; use gamepulse.market.entity_summary
-- to explode contributor lists in Python.
SELECT publishers, COUNT(*) AS title_count,
       SUM(COALESCE(review_count,0)) AS snapshot_reviews
FROM games
WHERE publishers IS NOT NULL AND TRIM(publishers) <> ''
GROUP BY publishers
ORDER BY title_count DESC LIMIT 25;

-- Pricing tiers vs observed review activity (not actual revenue).
SELECT CASE WHEN price=0 THEN 'Free'
            WHEN price<=5 THEN '$0.01–5'
            WHEN price<=15 THEN '$5–15'
            WHEN price<=30 THEN '$15–30'
            WHEN price<=60 THEN '$30–60' ELSE '$60+' END AS price_tier,
       COUNT(*) AS games,
       SUM(COALESCE(positive,0)) AS positive_reviews,
       SUM(COALESCE(review_count,0)) AS all_reviews
FROM games
WHERE price>=0 AND review_count>=100
GROUP BY price_tier ORDER BY games DESC;

-- Example screening logic
SELECT appid,name,price,review_count,positive_rate
FROM games
WHERE review_count BETWEEN 100 AND 5000 AND positive_rate >= 0.90
ORDER BY positive_rate DESC, review_count DESC LIMIT 25;
