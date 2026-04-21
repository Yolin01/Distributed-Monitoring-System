from app.database import SessionLocal
from app.models import User
from app.security import hash_password

def create_admin():
    """Crée l'utilisateur admin automatiquement s'il n'existe pas"""
    db = SessionLocal()
    try:
        # Vérifier si admin existe déjà
        admin_exists = db.query(User).filter(User.username == "admin").first()
        
        if not admin_exists:
            admin = User(
                username="admin",
                hashed_password=hash_password("admin123"),
                role="admin"
            )
            db.add(admin)
            db.commit()
            print("Admin créé automatiquement (admin/admin123)")
        else:
            print(" Admin existe déjà")
    except Exception as e:
        print(f" Erreur création admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()