from sqlalchemy import text

from db.session import engine


def main():
    with engine.begin() as conn:
        columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(ChiDinh)"))
        }

        if "KhongTinhTien" in columns:
            print("KhongTinhTien already exists.")
            return

        conn.execute(
            text(
                "ALTER TABLE ChiDinh "
                "ADD COLUMN KhongTinhTien INTEGER NOT NULL DEFAULT 0"
            )
        )
        print("Added KhongTinhTien to chidinh.")


if __name__ == "__main__":
    main()
