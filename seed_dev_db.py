import random
from datetime import datetime, timedelta, date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, HoSo, DonThuoc, ChiDinh, Thuoc

MEDICINES = [
    ("Paracetamol 500mg", 5000),
    ("Amoxicillin 500mg", 8000),
    ("Azithromycin 250mg", 12000),
    ("Omeprazole 20mg", 15000),
    ("Metformin 500mg", 10000),
    ("Amlodipine 5mg", 18000),
    ("Atorvastatin 20mg", 25000),
    ("Losartan 50mg", 20000),
    ("Cetirizine 10mg", 6000),
    ("Ibuprofen 400mg", 7000),
    ("Diclofenac 50mg", 5000),
    ("Clarithromycin 250mg", 14000),
    ("Cefixime 200mg", 22000),
    ("Pantoprazole 40mg", 16000),
    ("Rabeprazole 10mg", 13000),
    ("Domperidone 10mg", 4000),
    ("Loperamide 2mg", 6000),
    ("Salbutamol inhaler", 35000),
    ("Prednisolone 5mg", 3000),
    ("Dexamethasone 0.5mg", 2500),
    ("Methylprednisolone 4mg", 8000),
    ("Tramadol 50mg", 9000),
    ("Codeine 30mg", 11000),
    ("Gabapentin 300mg", 20000),
    ("Pregabalin 75mg", 30000),
    ("Duloxetine 30mg", 35000),
    ("Sertraline 50mg", 28000),
    ("Escitalopram 10mg", 32000),
    ("Haloperidol 5mg", 7000),
    ("Diazepam 5mg", 4000),
    ("Lorazepam 2mg", 6000),
    ("Zolpidem 10mg", 15000),
    ("Furosemide 40mg", 5000),
    ("Spironolactone 25mg", 8000),
    ("Hydrochlorothiazide 25mg", 4000),
    ("Bisoprolol 5mg", 12000),
    ("Metoprolol 50mg", 10000),
    ("Propranolol 40mg", 6000),
    ("Verapamil 40mg", 9000),
    ("Nifedipine 10mg", 7000),
    ("Clopidogrel 75mg", 22000),
    ("Warfarin 5mg", 8000),
    ("Heparin 5000IU", 45000),
    ("Enoxaparin 40mg", 65000),
    ("Insulin Glargine", 120000),
    ("Metformin 850mg", 12000),
    ("Gliclazide 80mg", 8000),
    ("Glimepiride 2mg", 15000),
    ("Pioglitazone 15mg", 18000),
    ("Sitagliptin 100mg", 45000),
]

FIRST_NAMES = [
    "Nguyen", "Tran", "Le", "Pham", "Hoang",
    "Vu", "Vo", "Dang", "Bui", "Do",
    "Mai", "Lý", "Duong", "Ngo", "Quach",
]

MIDDLE_NAMES_M = ["Van", "Minh", "Duc", "Huu", "Ngoc", "Xuan", "Tuan", "Quang", "Dinh", "Hoang", ""]
MIDDLE_NAMES_F = ["Thi", "Minh", "Ngoc", "Thuy", "Ngoc", "Kim", "Thi", "Thu", "Mai", "Huong", ""]

GIVEN_NAMES_M = [
    "Anh", "Huy", "Nam", "Tuan", "Khanh", "Dung", "Quang", "Hung", "Tien", "Dat",
    "Long", "Hieu", "Khoa", "Bao", "Nghia", "Manh", "Tri", "Nhat", "Phuc", "Loi",
]
GIVEN_NAMES_F = [
    "Linh", "Trang", "Phuong", "Thao", "Hoa", "Lan", "Mai", "Nhi", "Yen", "Ha",
    "Ngoc", "Cam", "Diep", "Khanh", "Nhung", "Huyen", "Thanh", "Tuyen", "Quyen", "Giang",
]

DOSE_PATTERNS = [
    [1, 0, 1, 0, 1, 0, 1],   # morning + afternoon + evening
    [1, 0, 0, 0, 1, 0, 1],   # morning + afternoon + evening
    [1, 0, 1, 0, 0, 0, 1],   # morning + lunch + evening
    [1, 1, 0, 0, 1, 1, 0],   # morning + lunch (after meal)
    [0, 0, 1, 0, 0, 0, 1],   # lunch + evening
    [1, 0, 0, 0, 0, 0, 0],   # morning only
    [0, 0, 0, 0, 0, 0, 1],   # evening only
    [1, 0, 1, 0, 1, 0, 0],   # morning + lunch + afternoon
    [0.5, 0, 0.5, 0, 0.5, 0, 0.5],  # half dose 4x
    [1, 0, 0, 0, 1, 0, 0],   # morning + afternoon
]

DIAGNOSES = [
    "Viêm họng cấp",
    "Viêm phổi thùy phải",
    "Viêm amidan",
    "Viêm dạ dày mạn tính",
    "Huyết áp cao stage 1",
    "Huyết áp cao stage 2",
    "Đái tháo đường type 2",
    "Mỡ máu cao",
    "Viêm khớp dạng thấp",
    "Thoái hóa khớp gối",
    "Viêm xoang mạn",
    "Hen phế quản",
    "Trào ngược dạ dày thực quản",
    "Viêm đại tràng",
    "Tiêu chảy cấp",
    "Viêm da cơ địa",
    "Migraine",
    "Rối loạn lo âu",
    "Mất ngủ",
    "Viêm thận bể thận",
    "Sỏi thận",
    "Viêm bàng quang",
    "Viêm gan B mạn",
    "Gout",
    "Thiếu máu",
]

DB_URL = "sqlite:///clinic.db"

NUM_PATIENTS = 30
PRESCRIPTIONS_RANGE = (1, 5)
MED_PER_PRESCRIPTION = (1, 8)


def create_session():
    engine = create_engine(DB_URL, echo=False)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def seed_medicines(session):
    print("Seeding medicines...")
    meds = [Thuoc(Ten=name, Gia=price) for name, price in MEDICINES]
    session.bulk_save_objects(meds)
    session.commit()
    return session.query(Thuoc.ThuocID, Thuoc.Ten, Thuoc.Gia).all()


def seed_data(session, medicines):
    print("Seeding patients + prescriptions...")

    for p in range(NUM_PATIENTS):
        is_male = random.random() < 0.5
        first = random.choice(FIRST_NAMES)
        middle = random.choice(MIDDLE_NAMES_M if is_male else MIDDLE_NAMES_F)
        given = random.choice(GIVEN_NAMES_M if is_male else GIVEN_NAMES_F)
        full_name = f"{first} {middle} {given}".strip()

        hoso = HoSo(
            Ten=full_name,
            GivenName=given.lower(),
            NamSinh=random.randint(1955, 2005),
            DiaChi=random.choice([
                "123 Trần Hưng Đạo, Q.1, TP.HCM",
                "45 Nguyễn Huệ, Q.1, TP.HCM",
                "67 Lê Lợi, Q.Bình Thạnh, TP.HCM",
                "89 Phan Đình Phùng, Q.Phú Nhuận",
                "12 Điện Biên Phủ, Q.Bình Thạnh",
                "34 Võ Văn Tần, Q.3",
                "56 Nguyễn Đình Chiểu, Q.3",
                "78 Hai Bà Trưng, Q.1",
                "90 Nguyễn Kiệm, Q.Phú Nhuận",
                "21 Xô Viết Nghệ Tĩnh, Q.Bình Thạnh",
            ]),
            DienThoai=f"09{random.randint(10000000, 99999999)}",
            TienCan=random.choice([
                "",
                "Không có tiền căn đáng chú ý",
                "Tiểu đường gia đình (bố)",
                "Huyết áp cao (mẹ)",
                "Viêm gan B",
                "Dị ứng thuốc penicillin",
                "Đã phẫu thuật ruột thừa 2015",
            ]),
            NgayMoHoSo=date.today() - timedelta(days=random.randint(0, 365)),
        )
        session.add(hoso)
        session.flush()

        num_rx = random.randint(*PRESCRIPTIONS_RANGE)
        for rx in range(num_rx):
            don = DonThuoc(
                HoSoID=hoso.HoSoID,
                NgayLap=datetime.now() - timedelta(days=random.randint(0, 180)),
                MoTa=random.choice(DIAGNOSES),
                TienToa=0,
            )
            session.add(don)
            session.flush()

            med_count = random.randint(*MED_PER_PRESCRIPTION)
            chosen = random.sample(medicines, min(med_count, len(medicines)))

            chi_batch = []
            total_cost = 0.0

            for thuoc_id, ten, price in chosen:
                doses = random.choice(DOSE_PATTERNS)
                so_ngay = random.randint(3, 14)
                total_cost += sum(doses) * float(price) * so_ngay

                chi_batch.append(ChiDinh(
                    DonThuocID=don.DonThuocID,
                    ThuocID=thuoc_id,
                    SangTruocAn=doses[0],
                    SangSauAn=doses[1],
                    TruaTruocAn=doses[2],
                    TruaSauAn=doses[3],
                    ChieuTruocAn=doses[4],
                    ChieuSauAn=doses[5],
                    Toi=doses[6],
                    SoNgay=so_ngay,
                ))

            don.TienToa = round(total_cost)
            session.bulk_save_objects(chi_batch)

        if (p + 1) % 10 == 0:
            session.commit()
            print(f"  {p + 1}/{NUM_PATIENTS} patients...")

    session.commit()
    print("Done.")


def main():
    session = create_session()
    medicines = seed_medicines(session)
    seed_data(session, medicines)
    session.close()
    print(f"Seeded {NUM_PATIENTS} patients into {DB_URL}")


if __name__ == "__main__":
    main()
