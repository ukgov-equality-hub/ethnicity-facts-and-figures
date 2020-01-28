


docker exec publisher_db createdb -U postgres rdcms_test

docker exec -it publisher_db /bin/bash
createdb -U postgres rdcms_test

psql -U postgres

\q
exit;

docker exec publisher ./docker/import_db.sh
