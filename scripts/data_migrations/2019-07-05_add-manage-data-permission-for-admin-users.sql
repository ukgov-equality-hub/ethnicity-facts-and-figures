update users set capabilities = array_append(capabilities,'manage_data_sources') where user_type = 'ADMIN_USER' and not(capabilities @> ARRAY['manage_data_sources'::varchar])
