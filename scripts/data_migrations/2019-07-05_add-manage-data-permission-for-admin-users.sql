update users set capabilities = array_append(capabilities,'manage_data_sources') where user_type IN ('ADMIN_USER', 'DEV_USER') and not(capabilities @> ARRAY['manage_data_sources'::varchar])
