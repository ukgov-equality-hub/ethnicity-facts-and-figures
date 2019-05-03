UPDATE dimension_chart SET settings_and_source_data = jsonb_set(settings_and_source_data::JSONB, '{chartFormat, chart_title}', to_jsonb(title));

UPDATE dimension_table SET settings_and_source_data = jsonb_set(settings_and_source_data::JSONB, '{tableValues, table_title}', to_jsonb(title));
