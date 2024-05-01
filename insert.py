import sqlite3
import csv
from pathlib import Path


class DatabaseConnector:
    def __init__(self):
        self.master_dbname = "master.sqlite"
        self.sales_dbname = "salesHistory.sqlite"

    def connect(self, db_type="master"):
        if db_type == "sales":
            return sqlite3.connect(self.sales_dbname)
        return sqlite3.connect(self.master_dbname)


class table_master:
    def __init__(self):
        self.db_connector = DatabaseConnector()

    def main_menu(self):
        items_csv_path = "csv//items.csv"
        staffs_csv_path = "csv//staffs.csv"
        while True:
            print("\n==DBメンテメニュー==")
            print(
                "1. データベースをセットアップ\n2. 商品データをCSVからアップサート\n3. スタッフデータをCSVからアップサート\n4. 終了"
            )
            choice = input("選択:")
            with self.db_connector.connect() as conn:
                cur = conn.cursor()

            if choice == "1":
                self.setup_database()

            elif choice == "2":
                if self.check_file_existence(items_csv_path):
                    self.upsert_items_data_from_csv(cur, items_csv_path)
                    conn.commit()
                    print("商品データのアップサートが完了しました。")

            elif choice == "3":
                if self.check_file_existence(staffs_csv_path):
                    self.upsert_staffs_data_from_csv(cur, staffs_csv_path)
                    conn.commit()
                    print("スタッフデータのアップサートが完了しました。")

            elif choice == "4":
                print("プログラムを終了します")
                break

            else:
                print("無効な選択")

    def setup_database(self):
        with self.db_connector.connect() as conn:
            cur = conn.cursor()
            try:
                # cur.execute("PRAGMA FOREIGN KEY = ON")
                self.create_master_DB(cur)
                self.create_sales_DB()
                self.upsert_permissions_data(cur)
                print("データベースのセットアップが完了しました！")
            except sqlite3.Error as e:
                print(f"データベースセットアップ中にエラーが発生しました: {e}")

    def create_master_DB(self, cur):
        try:
            cur.execute("PRAGMA foreign_keys = ON")
            cur.execute("BEGIN TRANSACTION")
            cur.execute(  # itemsテーブルの作成
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

            cur.execute(  # permissionsテーブルの作成
                """
                CREATE TABLE IF NOT EXISTS permissions(
                    permission_level INTEGER PRIMARY KEY,
                    permission_name TEXT)
                """
            )

            cur.execute(  # staffsテーブルの作成
                """
                CREATE TABLE IF NOT EXISTS staffs(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    staffCode INTEGER NOT NULL UNIQUE,
                    name TEXT,
                    password TEXT,
                    permission_level INTEGER,
                    FOREIGN KEY ('permission_level') REFERENCES 'permissions' (permission_level))
                """
            )
            cur.execute("COMMIT TRANSACTION")
        except Exception as e:
            cur.execute("ROLLBACK TRANSACTION")
            print(f"マスターテーブルの作成中にエラーが発生しました: {e}")

    def create_sales_DB(self):
        with self.db_connector.connect("sales") as conn:
            try:
                cur = conn.cursor()
                cur.execute("BEGIN TRANSACTION")
                cur.execute(  # Transactionsテーブルの作成
                    """
                    CREATE TABLE IF NOT EXISTS `Transactions` (
                        `transaction_id` INTEGER PRIMARY KEY AUTOINCREMENT,
                        `sales_type` INTEGER,
                        `date` DATETIME,
                        `staffCode` INTEGER,
                        `purchase_points` INTEGER,
                        `total_tax_amount` INTEGER,
                        `total_base_price` INTEGER,
                        `total_amount` INTEGER,
                        `deposit` INTEGER,
                        `change` INTEGER
                    )
                    """
                )
                cur.execute(  # sales_itemテーブルの作成
                    """
                    CREATE TABLE IF NOT EXISTS `sales_item` (
                        `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                        `transaction_id` INTEGER NOT NULL,
                        `JAN` INTEGER,
                        `product_name` TEXT,
                        `unit_price` INTEGER,
                        `tax_rate` INTEGER,
                        `amount` INTEGER,
                        FOREIGN KEY (`transaction_id`) REFERENCES `Transactions`(`transaction_id`)
                    )
                    """
                )
                cur.execute(  # hold_transactionsテーブルの作成
                    """
                    CREATE TABLE IF NOT EXISTS hold_transactions(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATETIME,
                        purchase_items TEXT)
                    """
                )
                cur.execute("COMMIT TRANSACTION")
            except sqlite3.Error as e:
                cur.execute("ROLLBACK TRANSACTION")
                print(f"salesHistryテーブル作成中にエラーが発生しました: {e}")

    def upsert_permissions_data(self, cur):
        try:
            cur.execute("BEGIN TRANSACTION")
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
                cur.execute("COMMIT TRANSACTION")
        except Exception as e:
            cur.execute("ROLLBACK TRANSACTION")
            print(f"権限テーブルのアップサート中にエラーが発生しました: {e}")

    def calculate_checksum(self, numbers):
        accumulated_sum, multiplier = 0, 3
        for number in reversed(numbers):
            accumulated_sum += int(number) * multiplier
            multiplier = 1 if multiplier == 3 else 3
        return accumulated_sum

    def is_valid_jan_code(self, jan_code_str):
        numbers = list(jan_code_str[:-1])
        expected_cd = self.calculate_checksum(numbers) % 10
        expected_cd = 10 - expected_cd if expected_cd != 0 else 0
        actual_cd = int(jan_code_str[-1])
        return expected_cd == actual_cd

    def check_file_existence(self, file_path):
        if Path(file_path).exists():
            return True
        else:
            print(f"指定されたファイルが見つかりません: {file_path}")
            return False

    def upsert_items_data_from_csv(self, cur, csv_path):
        try:
            with open(csv_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # ヘッダー行をスキップ
                for row in reader:
                    jan_code_str = str.strip(row[0])
                    if self.is_valid_jan_code(jan_code_str):
                        cur.execute(
                            "UPDATE items SET name = ?, tax = ?, price = ?, stock = ? WHERE JAN = ?",
                            (row[1], int(row[2]), int(row[3]), int(row[4]), int(row[0])),
                        )
                        if cur.rowcount == 0:
                            cur.execute(
                                "INSERT INTO items (JAN, name, tax, price, stock) VALUES (?, ?, ?, ?, ?)",
                                (int(row[0]), row[1], int(row[2]), int(row[3]), int(row[4])),
                            )
                    else:
                        print(f"不正なJANコードのため、データの挿入をスキップします\nJAN:{jan_code_str}")
        except Exception as e:
            print(f"商品データアップサート中にエラーが発生しました: {e}")

    def upsert_staffs_data_from_csv(self, cur, csv_file_path):
        try:
            with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # ヘッダー行をスキップ
                for row in reader:
                    staff_code, name, password, permission = row
                    cur.execute(
                        "UPDATE staffs SET name = ?, password = ?, permission_level = ? WHERE staffCode = ?",
                        (name, password, permission, staff_code),
                    )
                    if cur.rowcount == 0:
                        cur.execute(
                            "INSERT INTO staffs (staffCode, name, password, permission_level) VALUES (?, ?, ?, ?)",
                            (staff_code, name, password, permission),
                        )
        except Exception as e:
            print(f"スタッフデータアップサート中にエラーが発生しました: {e}")


def main():
    tableMaster = table_master()
    tableMaster.main_menu()


if __name__ == "__main__":
    main()
