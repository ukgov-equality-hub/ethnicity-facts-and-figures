-- This copies the chart and table titles form the settings object into its own column.

update dimension_chart set title = settings_and_source_data::json->'chartFormat'->>'chart_title'::text;

update dimension_table set title = settings_and_source_data::json->'tableValues'->>'table_title'::text;