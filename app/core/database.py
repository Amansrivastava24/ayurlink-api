from sqlmodel import create_engine, SQLModel, Session
from app.core.config import settings

# Create the database engine using the URL from our settings
# connect_args is needed for SQLite, but good practice to keep for other DBs
engine = create_engine(str(settings.DATABASE_URL), echo=True)

def init_db():
    """
    Initializes the database and creates all tables defined by SQLModel models.
    """
    print("Initializing database and creating tables...")
    SQLModel.metadata.create_all(engine)
    print("Database initialization complete.")

def get_session():
    """
    Dependency function to get a database session for each request.
    """
    with Session(engine) as session:
        yield session