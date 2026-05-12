from sqlalchemy import func
from sqlalchemy.engine import Engine


def format_month(date_col, engine: Engine):
    dialect = engine.dialect.name

    if dialect == "sqlite":
        return func.strftime("%Y-%m", date_col)
    elif dialect == "postgresql":
        return func.to_char(date_col, "YYYY-MM")
    else:
        raise NotImplementedError(f"Unsupported dialect: {dialect}")
