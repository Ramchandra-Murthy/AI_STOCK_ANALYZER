from backend.database.engine import Base, engine
import backend.database.models.company
import backend.database.models.user

print("=== REGISTERED SQLALCHEMY TABLES ===")
for name in Base.metadata.tables:
    print(name)

print("=== CREATING TABLES ===")
Base.metadata.create_all(bind=engine)
print("CREATE_OK")

print("=== DATABASE TABLE CHECK ===")
with engine.connect() as conn:
    result = conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    for row in result:
        print(row[0])
