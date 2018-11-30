from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

db = SQLAlchemy(
    metadata=MetaData(
        naming_convention={
            "ix": "ix_%(column_0_N_label)s",
            "uq": "uix_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(constraint_name)s",
            "fk": "%(table_name)s_%(column_0_N_name)s_fkey",
            "pk": "%(table_name)s_pkey",
        }
    )
)
mail = Mail()
