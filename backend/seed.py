from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()

    if not User.query.filter_by(email_address="admin@gingerly.com").first():
        admin = User(
            first_name="Super",
            last_name="Admin",
            email_address="admin@gingerly.com",
            phone_number="08000000001",
            role="admin",
            is_superuser=True,
            plan="free",
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin created: admin@gingerly.com / admin123 (admin + superuser)")
    else:
        print("Admin already exists")
