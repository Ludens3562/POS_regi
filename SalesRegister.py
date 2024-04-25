import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

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
        # DatabaseConnectorのインスタンスを直接作成
        self.db_connector = DatabaseConnector()
        self.purchased_items = []
        self.sales_type = 1
        self.staffCode = 11112
        self.purchase_points = 0

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
        if not self.purchased_items:
            print("商品が登録されていません。JANコードを入力してください\n")
            self.register_sales()
            return
        tax_total, price_total, sub_total = self.calculate_totals()
        print(f"税抜き価格: {price_total}円\n消費税相当額: {tax_total}円\n合計金額: {sub_total}円")
        change, deposit = self.process_payment(sub_total)
        print(f"\nお釣り: {change}円\n---会計終了---\n")
        self.update_stock()
        self.register_transaction(self.sales_type, datetime, self.staffCode, self.purchase_points, tax_total, price_total, sub_total, deposit, change)
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

    def register_transaction(self, sales_type, date, staffCode, purchase_points, tax_total, price_total, sub_total, deposit, change):
        with self.db_connector.connect("sales") as conn:
            try:
                cur = conn.cursor()
                cur.execute("""INSERT INTO Transactions (sales_type, date, staffCode, purchase_points, total_tax_amount, total_base_price, total_amount, deposit, change) 
                            VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?)""",
                            (sales_type, staffCode, purchase_points, tax_total, price_total, sub_total, deposit, change))
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
                cur.execute("""INSERT INTO sales_item (transaction_id, JAN, product_name, unit_price, tax_rate, amount) 
                            VALUES (?, ?, ?, ?, ?, ?)""", (transaction_id, JAN, product_name, unit_price, tax_rate, int(amount)))