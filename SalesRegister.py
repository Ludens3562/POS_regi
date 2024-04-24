import sqlite3
from decimal import Decimal, ROUND_HALF_UP

dbname = "master.sqlite"

def connect_db():
    return sqlite3.connect(dbname)


class SalesRegister:
    def __init__(self):
        self.purchased_items = []

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

    def register_sales(self):  # 商品の登録と会計の開始点
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

                change = self.process_payment(sub_total)
                print(f"\nお釣り: {change}円")
                print("---会計終了---\n")

                self.update_stock()
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
        return tax_total, price_total, sub_total

    def process_payment(self, sub_total):  # 支払い処理
        while True:
            try:
                deposit = int(input("預かり金を入力: "))
                if deposit < sub_total:
                    print("\n金額が不足しています")
                else:
                    return deposit - sub_total  # おつりを返す
            except ValueError:
                print("\n無効な入力です。数字を入力してください。")

    def update_stock(self):  # 在庫の更新
        with connect_db() as conn:
            cur = conn.cursor()
            for barcode in self.purchased_items:
                cur.execute("UPDATE items SET stock = stock - 1 WHERE JAN = ?", (barcode,))
            conn.commit()