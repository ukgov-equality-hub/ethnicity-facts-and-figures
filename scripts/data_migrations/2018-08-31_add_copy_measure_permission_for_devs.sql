UPDATE users
SET capabilities = array_append(capabilities, 'copy_measure')
WHERE user_type = 'DEV_USER';
