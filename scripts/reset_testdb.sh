dropdb rdcms_test
createdb rdcms_test
python << EOF
from tests.conftest import db_migration
db_migration()
EOF
