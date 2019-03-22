-- This removes chart and table titles from the settings blob for all existing charts and tables, because
-- this information is now stored in a dedicated column.

UPDATE dimension_chart SET settings_and_source_data = (settings_and_source_data::JSONB #- '{chartFormat,chart_title}')::JSON;
UPDATE dimension_chart SET chart_object = (chart_object::JSONB #- '{title}')::JSON;

UPDATE dimension_table SET settings_and_source_data = (settings_and_source_data::JSONB #- '{tableValues,table_title}')::JSON;
UPDATE dimension_table SET table_object = (table_object::JSONB #- '{header}')::JSON;
