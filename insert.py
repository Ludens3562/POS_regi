import sqlite3
import csv
from pathlib import Path

dbname = "master.sqlite"


def create_tables(cur):
    cur.execute("BEGIN TRANSACTION")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            JAN INTEGER NOT NULL UNIQUE,
            name TEXT,
            tax INTEGER DEFAULT 10 CHECK (tax >= 0),
            price INTEGER,
            stock INTEGER)
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS permissions(
            permission_level INTEGER PRIMARY KEY,
            permission_name TEXT)
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS staffs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staffCode INTEGER NOT NULL UNIQUE,
            name TEXT,
            password TEXT,
            permission INTEGER)
        """
    )
    cur.execute("COMMIT TRANSACTION")


def is_valid_jan_code(jan_code_str):
    def calculate_checksum(numbers):
        accumulated_sum, multiplier = 0, 3
        for number in reversed(numbers):
            accumulated_sum += int(number) * multiplier
            multiplier = 1 if multiplier == 3 else 3
        return accumulated_sum

    numbers = list(jan_code_str[:-1])  # JANコードからチェックディジットを除いたリスト
    expected_cd = calculate_checksum(numbers) % 10
    expected_cd = 10 - expected_cd if expected_cd != 0 else 0
    actual_cd = int(jan_code_str[-1])  # 入力されたJANコードのチェックディジット

    return expected_cd == actual_cd


def upsert_items_data_from_csv(cur, csv_path):
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # ヘッダー行をスキップ
        for row in reader:
            jan_code_str = str.strip(row[0])
            if is_valid_jan_code(jan_code_str):
                cur.execute(
                    """
                    UPDATE items
                    SET name = ?, tax = ?, price = ?, stock = ?
                    WHERE JAN = ?
                    """,
                    (row[1], int(row[2]), int(row[3]), int(row[4]), int(row[0])),
                )
                if cur.rowcount == 0:
                    cur.execute(
                        """
                        INSERT INTO items (JAN, name, tax, price, stock)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (int(row[0]), row[1], int(row[2]), int(row[3]), int(row[4])),
                    )
            else:
                print(f"不正なJANコードのため、データの挿入をスキップします\nJAN:{jan_code_str}")


def upsert_staffs_data_from_csv(cur, csv_file_path):
    with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # ヘッダー行をスキップ
        for row in reader:
            print(row)
            staff_code, name, password, permission = row
            cur.execute(
                """
                UPDATE staffs
                SET name = ?, password = ?, permission = ?
                WHERE staffCode = ?
                """,
                (name, password, permission, staff_code),
            )
            if cur.rowcount == 0:
                cur.execute(
                    """
                    INSERT INTO staffs (staffCode, name, password, permission)
                    VALUES (?, ?, ?, ?)
                    """,
                    (staff_code, name, password, permission),
                )


def upsert_permissions_data(cur):
    permissions_data = [
        (1, "SystemAdmin"),
        (2, "Reserved1"),
        (3, "StoreManager"),
        (4, "Reserved2"),
        (5, "A_Staff"),
        (6, "B_Staff"),
    ]
    for permission_level, permission_name in permissions_data:
        # まず、UPDATEを試みる
        cur.execute(
            "UPDATE permissions SET permission_name = ? WHERE permission_level = ?",
            (permission_name, permission_level),
        )
        # 更新が行われなかった場合、INSERTを試みる
        if cur.rowcount == 0:
            cur.execute(
                "INSERT INTO permissions(permission_level, permission_name) VALUES (?, ?)",
                (permission_level, permission_name),
            )


def setup_database():
    try:
        with sqlite3.connect(dbname) as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA foreign_keys = ON")

            create_tables(cur)
            upsert_permissions_data(cur)
            conn.commit()

            print("データベースのセットアップが完了しました！")

    except sqlite3.Error as e:
        cur.execute("ROLLBACK TRANSACTION")
        print(f"データベースセットアップ中にエラーが発生しました: {e}")


def check_file_existence(file_path):
    """指定されたパスのファイルの存在をチェックする"""
    if Path(file_path).exists():
        return True
    else:
        print(f"指定されたファイルが見つかりません: {file_path}")
        return False


def main_menu():
    items_csv_path = "csv//items.csv"
    staffs_csv_path = "csv//staffs.csv"
    while True:
        print("\nメインメニュー:")
        print("1. 商品データをCSVからアップサート")
        print("2. スタッフデータをCSVからアップサート")
        print("3. データベースをセットアップ")
        print("4. 終了")
        choice = input("選択してください(1-4): ")

        if choice == "1":
            if check_file_existence(items_csv_path):
                try:
                    with sqlite3.connect(dbname) as conn:
                        cur = conn.cursor()
                        upsert_items_data_from_csv(cur, items_csv_path)
                        conn.commit()
                    print("商品データのアップサートが完了しました。")
                except Exception as e:
                    print(f"商品データアップサート中にエラーが発生しました: {e}")
        elif choice == "2":
            if check_file_existence(staffs_csv_path):
                try:
                    with sqlite3.connect(dbname) as conn:
                        cur = conn.cursor()
                        upsert_staffs_data_from_csv(cur, staffs_csv_path)
                        conn.commit()
                    print("スタッフデータのアップサートが完了しました。")
                except Exception as e:
                    print(f"スタッフデータアップサート中にエラーが発生しました: {e}")
        elif choice == "3":
            setup_database()
        elif choice == "4":
            print("プログラムを終了します。")
            break
        else:
            print("無効な選択です。もう一度入力してください。")


if __name__ == "__main__":
    main_menu()
