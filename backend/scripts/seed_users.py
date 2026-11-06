"""Create (or reset) one test user per staff role and print the credentials.

Safe to run many times: an existing user with the same email gets its
password, role and active status reset to the values below.

Run from inside backend/:
    venv\\Scripts\\python.exe scripts\\seed_users.py
"""

import sys
from pathlib import Path

# Make the backend package importable when running this script directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import Perdorues
from app.db.session import SessionLocal

TEST_USERS = [
    {"emri": "Arta", "mbiemri": "Krasniqi", "email": "admin@vushtrri.rks-gov.net",
     "password": "Admin!2026", "role": "admin"},
    {"emri": "Agim", "mbiemri": "Berisha", "email": "inspektor@vushtrri.rks-gov.net",
     "password": "Inspektor!2026", "role": "inspektor"},
    {"emri": "Drita", "mbiemri": "Gashi", "email": "drejtor@vushtrri.rks-gov.net",
     "password": "Drejtor!2026", "role": "drejtor"},
]


def main():
    with SessionLocal() as db:
        for data in TEST_USERS:
            user = db.scalar(select(Perdorues).where(Perdorues.email == data["email"]))
            if user is None:
                user = Perdorues(email=data["email"])
                db.add(user)
                action = "u krijua"
            else:
                action = "u rivendos"
            user.emri = data["emri"]
            user.mbiemri = data["mbiemri"]
            user.role = data["role"]
            user.password_hash = hash_password(data["password"])
            user.aktiv = True
            print(f"{data['role']:<10} {data['email']:<34} {data['password']:<16} ({action})")
        db.commit()


if __name__ == "__main__":
    main()
