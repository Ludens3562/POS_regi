import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import global_value as g


class DatabaseConnector:
    def __init__(self):
        self.master_dbname = "master.sqlite"
        self.sales_dbname = "salesHistory.sqlite"

    def connect(self, db_type="master"):
        if db_type == "sales":
            return sqlite3.connect(self.sales_dbname)
        return sqlite3.connect(self.master_dbname)


class SalesRegister:
    def __init__(self):
        self.db_connector = DatabaseConnector()
        self.purchased_items = []

    def is_barcode_valid(self, barcode):
        with self.db_connector.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT JAN FROM items WHERE JAN = ?", (barcode,))
            return bool(cur.fetchone())

    def get_item_info(self, barcode):
        with self.db_connector.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM items WHERE JAN = ?", (barcode,))
            return cur.fetchone()

    def register_sales(self):
        self.purchased_items = []
        while True:
            barcode = input("JAN入力: ")
            if barcode == "":
                self.complete_sales()
                return
            elif self.is_barcode_valid(barcode):
                self.purchased_items.append(barcode)
            else:
                print("無効な入力\n")

    def complete_sales(self):
        sales_type = 1  # 1: 通常売上 2.返品
        if not self.purchased_items:
            print("商品が登録されていません。JANコードを入力してください\n")
            self.register_sales()
            return
        tax_total, price_total, sub_total = self.calculate_totals()
        purchase_points = len(self.purchased_items)
        print(f"\n点数： {purchase_points}点")
        print(f"税抜き価格: {price_total}円\n消費税相当額: {tax_total}円\n合計金額: {sub_total}円")
        change, deposit = self.process_payment(sub_total)
        print(f"\nお釣り: {change}円\n---会計終了---\n")
        self.update_stock()
        self.register_transaction(
            sales_type, datetime, g.staffCode, purchase_points, tax_total, price_total, sub_total, deposit, change
        )
        self.register_sales()

    def calculate_totals(self):
        tax_total = price_total = 0
        for barcode in self.purchased_items:
            item = self.get_item_info(barcode)
            if item:
                tax_total += (item[3] / 100) * item[4]
                price_total += item[4]
        tax_total = Decimal(str(tax_total)).quantize(Decimal("0"), ROUND_HALF_UP)
        return int(tax_total), int(price_total), int(tax_total + price_total)

    def process_payment(self, sub_total):
        while True:
            try:
                deposit = int(input("預かり金を入力: "))
                if deposit < sub_total:
                    print("\n金額が不足しています")
                else:
                    return deposit - sub_total, deposit
            except ValueError:
                print("\n無効な入力")

    def update_stock(self):
        with self.db_connector.connect() as conn:
            cur = conn.cursor()
            for barcode in self.purchased_items:
                cur.execute("UPDATE items SET stock = stock - 1 WHERE JAN = ?", (barcode,))
            conn.commit()

    def register_transaction(
        self, sales_type, date, staffCode, purchase_points, tax_total, price_total, sub_total, deposit, change
    ):
        with self.db_connector.connect("sales") as conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO Transactions (sales_type, date, staffCode, purchase_points, total_tax_amount, total_base_price, total_amount, deposit, change) 
                            VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?)""",
                    (sales_type, staffCode, purchase_points, tax_total, price_total, sub_total, deposit, change),
                )
                transaction_id = cur.lastrowid

                # トランザクションの詳細を登録
                self.register_transaction_details(transaction_id, conn)  # コネクションを引数として渡す

                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e

    def register_transaction_details(self, transaction_id, conn):
        for barcode in self.purchased_items:
            item = self.get_item_info(barcode)
            if item:
                JAN, product_name, tax_rate, unit_price = item[1], item[2], item[3], item[4]
                amount = unit_price + (unit_price * tax_rate / 100)
                amount = Decimal(str(amount)).quantize(Decimal("0"), ROUND_HALF_UP)

                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO sales_item (transaction_id, JAN, product_name, unit_price, tax_rate, amount) 
                            VALUES (?, ?, ?, ?, ?, ?)""",
                    (transaction_id, JAN, product_name, unit_price, tax_rate, int(amount)),
                )


class ReturnRegister:
    def __init__(self):
        self.db_connector = DatabaseConnector()

    def return_process(self):
        with self.db_connector.connect("sales") as conn:
            cur = conn.cursor()
            transaction_id = input("トランザクションIDを入力してください: ")
            cur.execute("SELECT sales_type FROM Transactions WHERE transaction_id = ?", (transaction_id,))
            row = cur.fetchone()
            if row:
                sales_type = row[0]
                if sales_type != 1:
                    print("返品処理は売上データ以外に実行できません")
                    return self.return_process()

            return_type = input("全返品の場合は1を、一部返品の場合は2を入力してください: ")

            if return_type == "1":
                self.full_return(transaction_id)
            elif return_type == "2":
                self.partial_return(transaction_id)
            else:
                print("無効な入力です。")
                return

    def full_return(self, transaction_id):
        with self.db_connector.connect("sales") as conn:
            try:
                items = self._get_transaction_items(transaction_id, conn)
                self._process_items(transaction_id, conn, items, full_return=True)
                self._register_negative_transaction(transaction_id, conn)
                conn.commit()
            except Exception as e:
                conn.rollback()
                print("返品処理に失敗しました。", e)

    def partial_return(self, transaction_id):
        with self.db_connector.connect("sales") as conn:
            try:
                items = self._get_transaction_items(transaction_id, conn)
                items = self._select_partial_items(items)
                self._process_items(transaction_id, conn, items, full_return=False)
                conn.commit()
            except Exception as e:
                conn.rollback()
                print("返品処理に失敗しました。", e)

    def _get_transaction_items(self, transaction_id, conn):
        cur = conn.cursor()
        cur.execute(
            "SELECT id, JAN, product_name, unit_price, tax_rate, amount FROM sales_item WHERE transaction_id = ?",
            (transaction_id,),
        )
        return cur.fetchall()

    def _process_items(self, transaction_id, conn, items, full_return):
        cur = conn.cursor()
        unit_price_sum, tax_sum, amount_sum = 0, 0, 0

        for item in items:
            cur.execute(
                "INSERT INTO sales_item (transaction_id, JAN, product_name, unit_price, tax_rate, amount) VALUES (?, ?, ?, ?, ?, ?)",
                (transaction_id, item[1], item[2], -item[3], item[4], -item[5]),
            )
            unit_price_sum += item[3]
            tax_sum += (item[4] / 100) * item[3]
            amount_sum += item[5]

        tax_sum = int(Decimal(str(tax_sum)).quantize(Decimal("0"), ROUND_HALF_UP))

        if not full_return:
            self._register_refund_transaction(len(items), tax_sum, unit_price_sum, amount_sum, conn)

    def _register_negative_transaction(self, transaction_id, conn):
        cur = conn.cursor()
        cur.execute(
            "SELECT purchase_points, total_tax_amount, total_base_price, total_amount FROM Transactions WHERE transaction_id = ?",
            (transaction_id,),
        )
        row = cur.fetchone()
        self._register_refund_transaction(row[0], row[1], row[2], row[3], conn)

    def _register_refund_transaction(self, purchase_points, total_tax_amount, total_base_price, total_amount, conn):
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO Transactions (sales_type, date, staffCode, purchase_points, total_tax_amount, total_base_price, total_amount, deposit, change)
                    VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?)""",
            (2, g.staffCode, -purchase_points, -total_tax_amount, -total_base_price, -total_amount, 0, total_amount),
        )
        print(f"返金額: {total_amount}円")

    def _select_partial_items(self, items):
        print("返品する商品を選んでください:")
        for i, item in enumerate(items, 1):
            print(f"{str(i).zfill(2)}. {item[1]} {item[2]} (金額: {item[5]}円)")
        selected_items = input("返品する商品番号をカンマ区切りで入力してください（例: 1,3）: ")
        selected_indexes = [int(x) - 1 for x in selected_items.split(",")]
        return [items[i] for i in selected_indexes]


class TransactionHistory:
    def __init__(self):
        self.db_connector = DatabaseConnector()

    def search_transactions(self):
        with self.db_connector.connect("sales") as conn:
            query = self._build_query()
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            self._display_transactions(rows)

    def _build_query(self):
        print("検索条件を入力してください。")
        conditions = []

        transaction_id = input("トランザクションID (空白の場合は全件検索): ")
        if transaction_id:
            conditions.append(f"transaction_id = {transaction_id}")

        sales_type = input("売上タイプ (1: 通常売上, 2: 返品, 空白: 全て): ")
        if sales_type:
            conditions.append(f"sales_type = {sales_type}")

        date_from = input("開始日 (YYYY-MM-DD, 空白の場合は指定なし): ")
        date_to = input("終了日 (YYYY-MM-DD, 空白の場合は指定なし): ")
        if date_from and date_to:
            conditions.append(f"date BETWEEN '{date_from}' AND '{date_to}'")
        elif date_from:
            conditions.append(f"date >= '{date_from}'")
        elif date_to:
            conditions.append(f"date <= '{date_to}'")

        staffCode = input("スタッフコード (空白の場合は全て): ")
        if staffCode:
            conditions.append(f"staffCode = '{staffCode}'")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM Transactions WHERE {where_clause} ORDER BY date ASC"
        return query

    def _display_transactions(self, rows):
        if not rows:
            print("検索結果はありません。")
            return

        print("{:<6} {:<9} {:<13} {:8} {:<8} {:<7} {:<6} {:<6} {:<7}".format(
            "ID", "売上タイプ", "日付", "スタッフコード", "点数", "税額", "税抜価格", "税込価格", "釣銭"
        ))
        print("-" * 110)

        for row in rows:
            transaction_id, sales_type, date, staffCode, purchase_points, total_tax_amount, total_base_price, total_amount, deposit, change = row
            print("{:<10} {:<10} {:<20} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
                transaction_id, sales_type, date, staffCode, purchase_points, total_tax_amount, total_base_price, total_amount, deposit
            ))

        print("-" * 110)