from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import MetaData

csrf = CSRFProtect()
db = SQLAlchemy(
    # Our ideal naming convention
    metadata=MetaData(
        naming_convention={
            "ix": "ix_%(column_0N_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(constraint_name)s",
            "fk": "%(table_name)s_%(column_0_name)s_fkey",
            "pk": "%(table_name)s_pkey",
        }
    )
)
mail = Mail()
