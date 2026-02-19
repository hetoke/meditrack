from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Float, ForeignKey, DECIMAL, Text, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


# Hồ sơ
# ----------------------------
class HoSo(Base):
    __tablename__ = "hoso"

    HoSoID = Column(Integer, primary_key=True, autoincrement=True)
    Ten = Column(String, nullable=False)
    NamSinh = Column(Integer)
    DiaChi = Column(String)
    DienThoai = Column(String)
    TienCan = Column(Text)
    NgayMoHoSo = Column(Date)

    donthuocs = relationship("DonThuoc", back_populates="hoso")



# ----------------------------
# Đơn thuốc
# ----------------------------
class DonThuoc(Base):
    __tablename__ = "donthuoc"

    DonThuocID = Column(Integer, primary_key=True, autoincrement=True)
    HoSoID = Column(Integer, ForeignKey("hoso.HoSoID"), index=True)
    NgayLap = Column(DateTime)
    MoTa = Column(Text)
    TienToa = Column(DECIMAL)

    hoso = relationship("HoSo", back_populates="donthuocs")
    chidinh_list = relationship("ChiDinh", back_populates="donthuoc")


# ----------------------------
# Thuốc
# ----------------------------
class Thuoc(Base):
    __tablename__ = "thuoc"

    ThuocID = Column(Integer, primary_key=True, autoincrement=True)
    Ten = Column(String, nullable=False)
    Gia = Column(DECIMAL)

    chidinh_list = relationship("ChiDinh", back_populates="thuoc")


# ----------------------------
# Chỉ định
# ----------------------------
class ChiDinh(Base):
    __tablename__ = "chidinh"

    ChiDinhID = Column(Integer, primary_key=True, autoincrement=True)
    DonThuocID = Column(Integer, ForeignKey("donthuoc.DonThuocID"), index=True)
    ThuocID = Column(Integer, ForeignKey("thuoc.ThuocID"), index=True)

    SangTruocAn = Column(Float, default=0.0)
    SangSauAn = Column(Float, default=0.0)
    TruaTruocAn = Column(Float, default=0.0)
    TruaSauAn = Column(Float, default=0.0)
    ChieuTruocAn = Column(Float, default=0.0)
    ChieuSauAn = Column(Float, default=0.0)
    Toi = Column(Float, default=0.0)

    donthuoc = relationship("DonThuoc", back_populates="chidinh_list")
    thuoc = relationship("Thuoc", back_populates="chidinh_list")


# ----------------------------
# Setup database
# ----------------------------
# engine = create_engine("sqlite:///clinic.db", echo=True)  # echo=True = log SQL
# Session = sessionmaker(bind=engine)
# session = Session()



# records = [
#     ("Nguyễn Văn A", 1970, "Phường Cao Lãnh, Đồng Tháp", "0123456789"),
#     ("Lê Thị B", 1971, "Phường Chợ Quán, TP.HCM", "0123456788"),
#     ("Trần Lê C", 1972, "Xã Tân Long, Đồng Tháp", "0123356789")
# ]


# for name, year, address, phone in records:
#     hoso = HoSo(
#         Ten=name,
#         NamSinh=year,
#         DiaChi=address,
#         DienThoai=phone,
#         TienCan="",            # empty for now
#         NgayMoHoSo=date.today()
#     )
#     session.add(hoso)

# session.commit()
# session.close()

# print("✅ Demo hồ sơ đã được thêm vào cơ sở dữ liệu!")


