import random
from datetime import datetime, timedelta, date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, HoSo, DonThuoc, ChiDinh, Thuoc

FIRST_NAMES = [
    "Nguyen", "Tran", "Le", "Pham", "Hoang",
    "Vu", "Vo", "Dang", "Bui", "Do"
]

MIDDLE_NAMES = [
    "Van", "Thi", "Minh", "Duc", "Huu", ""
]

GIVEN_NAMES = [
    "Anh", "Huy", "Nam", "Linh", "Trang",
    "Phuong", "Thao", "Tuan", "Khanh", "Dung",
    "Quang", "Hoa", "Lan", "Hung", "Tien"
]

DB_URL = "sqlite:///clinic_stress.db"

NUM_MEDICINES = 100
NUM_PATIENTS = 5000
PRESCRIPTIONS_PER_PATIENT = 100
MAX_MED_PER_PRESCRIPTION = 20

PATIENT_BATCH = 200  # commit every 200 patients


def create_session():
    engine = create_engine(DB_URL, echo=False)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def seed_medicines(session):
    print("Seeding medicines...")

    meds = [
        Thuoc(Ten=f"Medicine_{i}", Gia=random.randint(5, 100))
        for i in range(NUM_MEDICINES)
    ]

    session.bulk_save_objects(meds)
    session.commit()

    # fetch lightweight tuples only
    return session.query(Thuoc.ThuocID, Thuoc.Gia).all()


def seed_data(session, medicines):
    print("Seeding patients + prescriptions...")

    for p in range(NUM_PATIENTS):
        first = random.choice(FIRST_NAMES)
        middle = random.choice(MIDDLE_NAMES)
        given = random.choice(GIVEN_NAMES)
        full_name = f"{first} {middle} {given}".strip()
        hoso = HoSo(
            Ten=full_name,
            GivenName=full_name.split()[-1].lower(),
            NamSinh=random.randint(1950, 2020),
            DiaChi="Stress Address",
            DienThoai=f"09{random.randint(10000000,99999999)}",
            TienCan="",
            NgayMoHoSo=date.today()
        )
        session.add(hoso)
        session.flush()  # get HoSoID

        for _ in range(PRESCRIPTIONS_PER_PATIENT):

            don = DonThuoc(
                HoSoID=hoso.HoSoID,
                NgayLap=datetime.now() - timedelta(days=random.randint(0, 365)),
                MoTa="Stress Test",
                TienToa=0
            )
            session.add(don)
            session.flush()

            med_count = random.randint(1, MAX_MED_PER_PRESCRIPTION)

            chi_batch = []
            total_cost = 0

            for _ in range(med_count):
                thuoc_id, price = random.choice(medicines)

                doses = [random.randint(0, 2) for _ in range(7)]
                total_cost += sum(doses) * float(price)

                chi_batch.append(
                    ChiDinh(
                        DonThuocID=don.DonThuocID,
                        ThuocID=thuoc_id,
                        SangTruocAn=doses[0],
                        SangSauAn=doses[1],
                        TruaTruocAn=doses[2],
                        TruaSauAn=doses[3],
                        ChieuTruocAn=doses[4],
                        ChieuSauAn=doses[5],
                        Toi=doses[6],
                    )
                )

            don.TienToa = total_cost

            session.bulk_save_objects(chi_batch)

        # Commit every batch
        if (p + 1) % PATIENT_BATCH == 0:
            session.commit()
            print(f"Committed {p+1} patients...")

    session.commit()
    print("Done seeding.")


def main():
    session = create_session()
    medicines = seed_medicines(session)
    seed_data(session, medicines)
    session.close()


if __name__ == "__main__":
    main()
