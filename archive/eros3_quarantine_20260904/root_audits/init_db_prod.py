from backend.database.engine import Base, engine
import backend.database.models.company
import backend.database.models.user

print("=== CREATING TABLES FOR WORKER/API ===")
Base.metadata.create_all(bind=engine)
print("TABLES CREATED SUCCESSFULLY")
