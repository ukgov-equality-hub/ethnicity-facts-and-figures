SELECT guid, measure_id, cell_row, ROW_NUMBER() OVER(PARTITION BY guid, cell_row ORDER BY full_table_row) AS cell_col, cell_value FROM (
SELECT *, ROW_NUMBER() OVER() AS full_table_row FROM (
SELECT guid, measure_id, cell_row, json_array_elements_text(rows_json) AS cell_value FROM (
SELECT *, ROW_NUMBER() OVER(PARTITION BY guid ORDER BY original_row_number) AS cell_row FROM (
SELECT *, ROW_NUMBER() OVER() AS original_row_number FROM (
SELECT  
guid, measure_id, 
json_array_elements(json_extract_path(chart_source_data,'data'))  AS rows_json
        FROM db_dimension 
        WHERE chart_source_data IS NOT NULL
) AS basic
) AS with_original_rows
) AS with_cell_row
) AS with_full_cell_breakdown
) AS with_full_table_row