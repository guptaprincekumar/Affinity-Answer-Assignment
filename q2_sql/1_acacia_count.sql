-- Q2.1: How many types of Acacia plants can be found in the taxonomy table?
--
-- Every taxonomy row whose species name starts with the genus "Acacia"
-- counts as one type (includes subspecies/varieties, e.g. "Acacia aneura
-- var. tenuis", which are still distinct types of Acacia).
--
-- Result when run against the public Rfam database (Sep 2026): 326

SELECT COUNT(*) AS acacia_types
FROM taxonomy
WHERE species LIKE 'Acacia %';
