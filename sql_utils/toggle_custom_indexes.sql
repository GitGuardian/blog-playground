UPDATE
    pg_index
SET
    indisvalid = %s
WHERE
    indexrelid IN (
        SELECT
            indexrelid
        FROM
            pg_index
        WHERE
            indexrelid::regclass::text ILIKE '%%idx');
