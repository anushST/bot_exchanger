from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()

def connect(connect_string, logger):
    try:
        engine = create_engine(connect_string)
        engine.connect()
        session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return engine, session
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
