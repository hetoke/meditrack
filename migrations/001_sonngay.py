from sqlalchemy import text


def migrate(engine):
    with engine.begin() as conn:
        columns = {row[1] for row in conn.execute(text("PRAGMA table_info(chidinh)"))}
        if "SoNgay" not in columns:
            conn.execute(text("ALTER TABLE chidinh ADD COLUMN SoNgay INTEGER NOT NULL DEFAULT 1"))
            if "KhongTinhTien" in columns:
                conn.execute(text("UPDATE chidinh SET SoNgay = 0 WHERE KhongTinhTien = 1"))
                conn.execute(text("ALTER TABLE chidinh DROP COLUMN KhongTinhTien"))
