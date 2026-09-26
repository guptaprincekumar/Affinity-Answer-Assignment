-- Q2.2: Which type of wheat has the longest DNA sequence?
--
-- Wheat is the genus Triticum, so rows are matched on the species name
-- starting with 'Triticum' (same genus-matching pattern as Q2.1). Each
-- rfamseq row carries the sequence length; sorting by it and keeping
-- the top row gives the wheat type owning the longest sequence.
--
-- Result when run against the public Rfam database (Sep 2026):
--   Triticum durum (durum wheat), length = 836,514,780

SELECT tx.species, rf.length AS sequence_length
FROM rfamseq rf
JOIN taxonomy tx ON rf.ncbi_id = tx.ncbi_id
WHERE tx.species LIKE 'Triticum %'
ORDER BY rf.length DESC
LIMIT 1;
