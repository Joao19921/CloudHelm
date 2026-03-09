from app.db.session import SessionLocal
from app.services.cloud_catalog_service import CloudMasterEngine


def run_sync():
    db = SessionLocal()
    try:
        engine = CloudMasterEngine()
        synced, exported_file = engine.sync_database(
            db=db,
            providers=["aws", "gcp", "azure"],
            limit_per_provider=30,
        )
        print("Sync concluido:", synced)
        print("Arquivo exportado:", exported_file)
    finally:
        db.close()


if __name__ == "__main__":
    run_sync()
