-- Q2.3: Paginate families and their longest DNA sequence lengths.
--
-- Requirements:
--   * only families whose longest sequence is > 1,000,000
--   * sorted by that length, descending
--   * columns: family accession id, family name, max sequence length
--   * 9th page with 15 results per page -> LIMIT 15 OFFSET (9-1)*15 = 120
--
-- full_region links each family to the sequences annotated with it;
-- is_significant = 1 keeps only significant hits (as recommended in the
-- Rfam docs). Note: full_region is large, so this query takes several
-- minutes on the public server.

SELECT f.rfam_acc, f.rfam_id, MAX(rf.length) AS max_length
FROM family f
JOIN full_region fr ON fr.rfam_acc = f.rfam_acc
JOIN rfamseq rf ON rf.rfamseq_acc = fr.rfamseq_acc
WHERE fr.is_significant = 1
GROUP BY f.rfam_acc, f.rfam_id
HAVING max_length > 1000000
ORDER BY max_length DESC
LIMIT 15 OFFSET 120;
