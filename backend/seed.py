"""
Seed script - creates one user per role + a couple of demo devices so the
project is immediately testable after setup. Run: python seed.py
"""
from datetime import datetime
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.device import Device
from app.models.enums import RoleEnum
from app.core.security import hash_password
import app.models  # noqa

Base.metadata.create_all(bind=engine)
db = SessionLocal()

demo_users = [
    ("tech1", "Password123!", RoleEnum.TECHNICIAN, "Ravi Kumar", "9876543210"),
    ("mgmt1", "Password123!", RoleEnum.OVERALL_MANAGEMENT, None, None),
    ("quality1", "Password123!", RoleEnum.QUALITY, None, None),
    ("design1", "Password123!", RoleEnum.DESIGN, None, None),
    ("admin1", "Password123!", RoleEnum.ADMIN, None, None),
]

for username, password, role, name, phone in demo_users:
    if not db.query(User).filter(User.username == username).first():
        db.add(User(username=username, hashed_password=hash_password(password),
                     role=role, technician_name=name, phone_number=phone))

demo_devices = [
    ("DEV-90612", "AC-Model-X1", "SR-001", datetime(2023, 1, 15)),
    ("DEV-90613", "AC-Model-X1", "SR-001", datetime(2023, 1, 20)),
    ("DEV-90700", "AC-Model-Z2", "SR-007", datetime(2022, 6, 1)),
]
for device_id, model, serial, mfg_date in demo_devices:
    if not db.query(Device).filter(Device.device_id == device_id).first():
        db.add(Device(device_id=device_id, product_model=model, serial_range=serial,
                       manufacturing_date=mfg_date, status="ACTIVE"))

db.commit()
db.close()
print("Seed complete. Demo users (password 'Password123!' for all):")
for u, *_ in demo_users:
    print(f"  - {u}")
print("Demo devices: DEV-90612, DEV-90613, DEV-90700")
