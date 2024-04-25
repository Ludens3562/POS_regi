import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

dbname = "master.sqlite"
sales_dbname = "salesHistory.sqlite"

def connect_db():
    return sqlite3.connect(dbname)

def connect_sales_db():
    return sqlite3.connect(sales_dbname)


class SalesRegister:
    def __init__(self):
        self.purchased_items = []
        self.sales_type = 1  # 例: 1 = 通常販売, 2 = 返品など、固定値やユーザー入力によって変更可能
        self.staffCode = 11112  # ここではデフォルト値を設定していますが、実際にはユーザー入力やログイン情報から取得することも考えられます。
        self.purchase_points = 0  # 例: 購入ポイント、この値も購入履歴に基づいて動的に計算することが考えられます。

    def input_barcode(self):
        return input("JAN入力: ")

    def is_barcode_valid(self, barcode):
        with connect_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT JAN FROM items WHERE JAN = ?", (barcode,))
            row = cur.fetchone()
            if row:
                return True
            else:
                return None

    def register_sales(self):
        self.purchased_items = []
        while True:
            barcode = self.input_barcode()
            if barcode == "":
                if not self.purchased_items:
                    print("商品が登録されていません。JANコードを入力してください\n")
                    continue
                tax_total, price_total, sub_total = self.calculate_totals()
                print(f"税抜き価格: {price_total}円")
                print(f"\n消費税相当額: {tax_total}円")
                print(f"合計金額: {sub_total}円")

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
                change, deposit = self.process_payment(sub_total)
                print(f"\nお釣り: {change}円")
                print("---会計終了---\n")

                self.update_stock()
                self.register_transaction(self.sales_type, datetime, self.staffCode, self.purchase_points, tax_total, price_total, sub_total, deposit, change)
                self.register_sales()  # 再帰的に関数を呼び出して新たな販売処理を始める
                return
            else:
                if self.is_barcode_valid(barcode):
                    self.purchased_items.append(barcode)
                else:
                    print("無効な入力\n")

    def calculate_totals(self):  # 合計金額の計算
        tax_total = 0
        price_total = 0
        with connect_db() as conn:
            for barcode in self.purchased_items:
                cur = conn.cursor()
                cur.execute("SELECT * FROM items WHERE JAN = ?", (barcode,))
                row = cur.fetchone()
                if row:
                    tax_total += (row[3] / 100) * row[4]
                    price_total += row[4]
        tax_total = Decimal(str(tax_total)).quantize(Decimal("0"), ROUND_HALF_UP)
        sub_total = tax_total + price_total
        return int(tax_total), int(price_total), int(sub_total)

    def process_payment(self, sub_total):  # 支払い処理
        while True:
            try:
                deposit = int(input("預かり金を入力: "))
                if deposit < sub_total:
                    print("\n金額が不足しています")
                else:
                    return deposit - sub_total , deposit
            except ValueError:
                print("\n無効な入力です。数字を入力してください。")

    def update_stock(self):  # 在庫の更新
        with connect_db() as conn:
            cur = conn.cursor()
            for barcode in self.purchased_items:
                cur.execute("UPDATE items SET stock = stock - 1 WHERE JAN = ?", (barcode,))
            conn.commit()
    
    def register_transaction(self, sales_type, date, staffCode, purchase_points, tax_total, price_total, sub_total, deposit, change):
        with connect_sales_db() as conn:
            cur = conn.cursor()
            # トランザクション情報の登録
            cur.execute("""
                INSERT INTO Transactions (sales_type, date, staffCode, purchase_points, total_tax_amount, total_base_price, total_amount, deposit, change) 
                VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?)
                """, (self.sales_type, self.staffCode, self.purchase_points, tax_total, price_total, sub_total, deposit, change))
            transaction_id = cur.lastrowid

            # 商品ごとの情報を sales_item に登録
            for barcode in self.purchased_items:
                # 商品情報の取得時だけmaster.sqliteに接続
                with connect_db() as master_conn:
                    master_cur = master_conn.cursor()
                    master_cur.execute("""
                        SELECT JAN, name, price, tax FROM items WHERE JAN = ?
                        """, (barcode,))
                    row = master_cur.fetchone()
                if row:
                    JAN, product_name, unit_price, tax_rate = row
                    # 販売価格 (amount) を計算: 単価に税率を適用
                    amount = unit_price + (unit_price * tax_rate / 100)
                    amount = Decimal(str(amount)).quantize(Decimal("0"), ROUND_HALF_UP)
                    
                    cur.execute("""
                        INSERT INTO sales_item (transaction_id, JAN, product_name, unit_price, tax_rate, amount) 
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (transaction_id, JAN, product_name, unit_price, tax_rate, int(amount)))
            conn.commit()