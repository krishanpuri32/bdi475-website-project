.headers on
.mode column
-- types and blanks sanity
SELECT typeof(sale_price) t_price, typeof(living_area_sqft) t_sqft, typeof(baths) t_baths, COUNT(*) n FROM home_sales GROUP BY 1,2,3;
SELECT SUM(sale_date = '') blank_text_dates, SUM(sale_date IS NULL) null_dates FROM home_sales;
-- Q1: rows kept
SELECT COUNT(*) AS rows_kept FROM home_sales
WHERE sale_date IS NOT NULL AND year_built IS NOT NULL
  AND sale_price BETWEEN 10000 AND 5000000
  AND living_area_sqft BETWEEN 300 AND 8000
  AND beds BETWEEN 1 AND 7 AND baths BETWEEN 1 AND 7;
-- Q2: rows removed by the price rule at its position (after sale date and year built rules)
SELECT COUNT(*) AS removed_by_price_rule FROM home_sales
WHERE sale_date IS NOT NULL AND year_built IS NOT NULL
  AND NOT (sale_price BETWEEN 10000 AND 5000000);
-- Q3: median sale price of kept Champaign rows (average of the middle two if even)
WITH k AS (
  SELECT sale_price FROM home_sales
  WHERE city = 'Champaign' AND sale_date IS NOT NULL AND year_built IS NOT NULL
    AND sale_price BETWEEN 10000 AND 5000000
    AND living_area_sqft BETWEEN 300 AND 8000
    AND beds BETWEEN 1 AND 7 AND baths BETWEEN 1 AND 7),
o AS (SELECT sale_price, ROW_NUMBER() OVER (ORDER BY sale_price) rn, COUNT(*) OVER () n FROM k)
SELECT MAX(n) AS champaign_kept_rows, AVG(sale_price) AS champaign_median_price
FROM o WHERE rn IN ((n + 1) / 2, (n + 2) / 2);
