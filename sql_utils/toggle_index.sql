UPDATE
    pg_index
SET
    indisvalid = %s
WHERE
    indexrelid = %s::regclass;
