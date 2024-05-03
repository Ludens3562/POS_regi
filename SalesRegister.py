import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import global_value as g


def back_to_main():
    import main

    main.top_page()


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
        print("\n==売上登録==")
        while True:
            barcode = input("JAN入力: ")
            if barcode == "":
                if self.purchased_items:
                    self.checkout_options()
                else:
                    back_to_main()
            elif self.is_barcode_valid(barcode):
                self.purchased_items.append(barcode)
            else:
                print("無効な入力\n")

    def checkout_options(self):
        print("\n=小計メニュー=")
        print("1. 会計修正\n2. 会計中止\n3. 会計保留\n4. 登録に戻る\n空白で支払い入力に進む")
        choice = input("\n入力:")
        if choice == "1":
            self.remove_items()
            self.checkout_options()
        elif choice == "2":
            self.cancel_checkout()
        elif choice == "3":
            self.hold_checkout()
        elif choice == "4":
            self.register_sales()
        elif choice == "":
            self.complete_sales()
        else:
            print("無効な選択肢です。もう一度入力してください。")
            self.checkout_options()

    def remove_items(self):
        print("削除する商品の番号を入力してください (カンマ区切りで複数可)")
        for i, barcode in enumerate(self.purchased_items, start=1):
            item = self.get_item_info(barcode)
            print(f"{i}. {item[1]} ￥{item[4]} {item[2]} ")
        indices = input("> ").split(",")
        indices = [int(index) for index in indices if index.isdigit()]
        indices.sort(reverse=True)
        for index in indices:
            if 1 <= index <= len(self.purchased_items):
                self.purchased_items.pop(index - 1)
            else:
                print(f"{index}は無効な番号です")
        if not self.purchased_items:
            # リストが空の場合は会計を中止
            print("すべての商品が削除されました")
            self.cancel_checkout()
            return
        self.checkout_options()

    def cancel_checkout(self):
        print("\n会計を中止します")
        self.purchased_items = []
        self.register_sales()

    def hold_checkout(self):
        with self.db_connector.connect("sales") as conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO hold_transactions (date, purchase_items)
                        VALUES (datetime('now'), ?)""",
                    (str(self.purchased_items),),
                )
                conn.commit()
                print("\n会計が保留されました\n")
            except Exception as e:
                conn.rollback()
                raise e
        back_to_main()

    def resume_hold_checkout(self):
        with self.db_connector.connect("sales") as conn:
            cur = conn.cursor()
            hold_id = input("保留ID:")
            try:
                if hold_id == "":
                    back_to_main()
                else:
                    # 保留テーブルから保留idをキーにしたデータを取得
                    cur.execute("SELECT purchase_items FROM hold_transactions WHERE id = ?", (hold_id,))
                    result = cur.fetchone()
                    if not result:
                        print("指定されたIDの会計は存在しません。")
                        self.resume_hold_checkout()
                    # 取得結果を購入リストに復元
                    self.purchased_items = eval(result[0])
                    print(f"\n保留会計が復元されました。登録された商品数: {len(self.purchased_items)}")
                    # 保留データを削除
                    cur.execute("DELETE FROM hold_transactions WHERE id = ?", (hold_id,))
                    conn.commit()
                    self.checkout_options()
            except Exception as e:
                conn.rollback()
                print("エラーが発生しました: ", e)
                back_to_main()

    def complete_sales(self):
        tax_total, price_total, sub_total = self.calculate_totals()
        purchase_points = len(self.purchased_items)
        print(f"\n点数： {purchase_points}点")
        print(f"税抜き価格: {price_total}円\n消費税相当額: {tax_total}円\n合計金額: {sub_total}円")
        deposit, change = self.process_payment(sub_total)
        print(f"\nお釣り: {change}円\n---会計終了---\n")
        self.update_stock()
        self.register_transaction(1, purchase_points, tax_total, price_total, sub_total, deposit, change)
        self.purchased_items = []
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
                    return deposit, deposit - sub_total
            except ValueError:
                print("\n無効な入力")

    def update_stock(self):
        with self.db_connector.connect() as conn:
            cur = conn.cursor()
            for barcode in self.purchased_items:
                cur.execute("UPDATE items SET stock = stock - 1 WHERE JAN = ?", (barcode,))
            conn.commit()

    def register_transaction(self, sales_type, purchase_points, tax_total, price_total, sub_total, deposit, change):
        with self.db_connector.connect("sales") as conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO Transactions (sales_type, date, staffCode, purchase_points, total_tax_amount, total_base_price, total_amount, deposit, change) 
                            VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?)""",
                    (sales_type, g.staffCode, purchase_points, tax_total, price_total, sub_total, deposit, change),
                )
                transaction_id = cur.lastrowid

                for barcode in self.purchased_items:
                    item = self.get_item_info(barcode)
                    if item:
                        JAN, product_name, tax_rate, unit_price = item[1], item[2], item[3], item[4]
                        amount = unit_price + (unit_price * tax_rate / 100)
                        amount = Decimal(str(amount)).quantize(Decimal("0"), ROUND_HALF_UP)

                        cur.execute(
                            """INSERT INTO sales_item (transaction_id, JAN, product_name, unit_price, tax_rate, amount) 
                                    VALUES (?, ?, ?, ?, ?, ?)""",
                            (str(transaction_id).zfill(4), JAN, product_name, unit_price, tax_rate, int(amount)),
                        )

                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e


class ReturnRegister:
    def __init__(self):
        self.db_connector = DatabaseConnector()

    def return_process(self):
        with self.db_connector.connect("sales") as conn:
            print("\n==返品処理==")
            transaction_id = input("トランザクションIDを入力してください: ")
            if transaction_id == "":
                back_to_main()
            else:
                sales_type = self._validate_transaction_type(transaction_id, conn)
                if sales_type is None:
                    self.return_process()
            return_type = input("1.全返品\n2.一部返品\n>")
            if return_type == "1":
                self._process_full_return(transaction_id, conn)
                conn.commit()
            elif return_type == "2":
                self._process_partial_return(transaction_id, conn)
                conn.commit()
            else:
                print("無効な入力です。")
            self.return_process()

    def _validate_transaction_type(self, transaction_id, conn):
        # 変更対象のsales_typeを確認　1.販売（返品可能）, 2.返品データ,  3.返品済み（返品の元取引）
        cur = conn.cursor()
        cur.execute("SELECT sales_type FROM Transactions WHERE transaction_id = ?", (transaction_id,))
        row = cur.fetchone()
        if row:
            sales_type = row[0]
            if sales_type == 3:
                print("すでに返品済みの取引です")
                return None
            elif sales_type != 1:
                print("返品処理は売上データ以外に実行できません")
                return None
            return sales_type
        else:
            print("\nトランザクションIDが見つかりません")
            return None

    def _process_full_return(self, transaction_id, conn):
        try:
            items = self._get_all_sales_items(transaction_id, conn)
            self._process_return(transaction_id, conn, items, full_return=True)
        except Exception as e:
            conn.rollback()
            print("返品処理に失敗しました", e)

    def _process_partial_return(self, transaction_id, conn):
        try:
            items = self._get_all_sales_items(transaction_id, conn)
            items = self._select_partial_items(items)  # 返品商品を選択
            self._process_return(transaction_id, conn, items, full_return=False)
        except Exception as e:
            conn.rollback()
            print("返品処理に失敗しました", e)

    def _get_all_sales_items(self, transaction_id, conn):
        cur = conn.cursor()
        # sales_itemsテーブルからtransaction_idに紐づく全ての商品を取得する
        cur.execute(
            "SELECT id, JAN, product_name, unit_price, tax_rate, amount FROM sales_item WHERE transaction_id = ?",
            (transaction_id,),
        )
        return cur.fetchall()

    def _select_partial_items(self, items):
        print("返品する商品を選んでください:")
        for i, item in enumerate(items, 1):
            print(f"{str(i).zfill(2)}. {item[1]} {item[2]} (金額: {item[5]}円)")
        selected_items = input("返品する商品番号をカンマ区切りで入力してください（例: 1,3）: ")
        selected_indexes = [int(x) - 1 for x in selected_items.split(",")]
        return [items[i] for i in selected_indexes]

    def _process_return(self, transaction_id, conn, items, full_return):
        cur = conn.cursor()
        unit_price_sum, tax_sum, amount_sum = 0, 0, 0
        for item in items:
            cur.execute(  # sales_itemテーブルの各アイテムをマイナス処理
                "INSERT INTO sales_item (transaction_id, JAN, product_name, unit_price, tax_rate, amount) VALUES (?, ?, ?, ?, ?, ?)",
                (transaction_id, item[1], item[2], -item[3], item[4], -item[5]),
            )
            unit_price_sum += item[3]
            tax_sum += (item[4] / 100) * item[3]
            amount_sum += item[5]
        # 税額の合計を四捨五入
        tax_sum = int(Decimal(str(tax_sum)).quantize(Decimal("0"), ROUND_HALF_UP))

        self._change_origin_transaction_status(transaction_id, 3, conn)
        row = self._get_transaction_data(transaction_id, conn)
        self._register_refund_transaction(row[0], tax_sum, unit_price_sum, amount_sum, conn)

    def _change_origin_transaction_status(self, transaction_id, sales_type, conn):
        cur = conn.cursor()
        cur.execute(
            "UPDATE Transactions SET sales_type = ? WHERE transaction_id = ?",
            (sales_type, transaction_id),
        )

    def _get_transaction_data(self, transaction_id, conn):
        cur = conn.cursor()
        cur.execute(
            "SELECT purchase_points, total_tax_amount, total_base_price, total_amount FROM Transactions WHERE transaction_id = ?",
            (transaction_id,),
        )
        return cur.fetchone()

    def _register_refund_transaction(self, purchase_points, total_tax_amount, total_base_price, total_amount, conn):
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO Transactions (sales_type, date, staffCode, purchase_points, total_tax_amount, total_base_price, total_amount, deposit, change)
                    VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?)""",
            (2, g.staffCode, -purchase_points, -total_tax_amount, -total_base_price, -total_amount, 0, total_amount),
        )
        print(f"返金額: {total_amount}円")


class TransactionHistory:
    def __init__(self):
        self.db_connector = DatabaseConnector()

    def search_transactions(self):
        mode, transaction_id = self._select_mode()
        with self.db_connector.connect("sales") as conn:
            query = self._build_query(mode, transaction_id)
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            self._display_transactions(rows, mode)

    def _select_mode(self):
        while True:
            mode = input("モードを選択してください (1: Transactionsのみ, 2: Transactions + sales_items): ")
            if mode in ["1", "2"]:
                if mode == "2":
                    transaction_id = input("トランザクションIDを入力してください (空白の場合は全件表示): ")
                else:
                    transaction_id = ""
                return int(mode), transaction_id
            print("無効な入力です。1または2を入力してください。")

    def _build_query(self, mode, transaction_id):
        if mode == 1:
            print("検索条件を入力してください。")
            conditions = []
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
        else:
            if transaction_id:
                query = f"SELECT * FROM Transactions WHERE transaction_id = {transaction_id} ORDER BY date ASC"
            else:
                query = "SELECT * FROM Transactions ORDER BY date ASC"
        return query

    def _display_transactions(self, rows, mode):
        self._print_header(mode)

        if not rows:
            print("検索結果はありません。")
            return

        for row in rows:
            if mode == 1:
                (transaction_id, sales_type, date, staffCode, purchase_points, total_tax_amount, total_base_price, total_amount, deposit, change) = row
                print("{:<10} {:<10} {:<20} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
                    transaction_id, sales_type, date, staffCode, purchase_points, total_tax_amount,
                    total_base_price, total_amount, deposit
                ))
            else:
                transaction_id = row[0]
                print("{:<10}".format(transaction_id))
                self._display_transaction_items(transaction_id)
            print("-" * 110)

        back_to_main()

    def _display_transaction_items(self, transaction_id):
        with self.db_connector.connect("sales") as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM sales_item WHERE transaction_id = {transaction_id}")
            items = cur.fetchall()

            if not items:
                print("商品データがありません。")
                return

            print("{:<15} {:<40} {:<10} {:<10} {:<10}".format("JAN", "商品名", "単価", "税率", "数量"))
            for item in items:
                jan, product_name, unit_price, tax_rate, amount = item[2:]
                print("{:<15} {:<40} {:<10} {:<10} {:<10}".format(jan, product_name, unit_price, tax_rate, amount))

    def _print_header(self, mode):
        if mode == 1:
            print("{:<6} {:<9} {:<13} {:8} {:<8} {:<7} {:<6} {:<6} {:<7}".format(
                "ID", "売上タイプ", "日付", "スタッフコード", "点数", "税額", "税抜価格", "税込価格", "釣銭"
            ))
        else:
            print("{:<10}".format("トランザクションID"))
        print("-" * 110)


class CashRegister:
    def __init__(self, sales_register):
        self.sales_register = sales_register
        self.db_connector = sales_register.db_connector

    def close_register(self):
        print("\n==レジ締め==")
        self.display_daily_transaction_counts()
        total_sales = self.calculate_total_sales()
        cash_amount = self.count_cash()
        shortage_or_surplus = cash_amount - total_sales

        print("\n==レジ締め==")
        print(f"総売上金額: {total_sales}円")
        print(f"現金残高: {cash_amount}円")

        if shortage_or_surplus == 0:
            print("締めは問題ありません")
            self.record_cash_register(total_sales, cash_amount, shortage_or_surplus)
        elif shortage_or_surplus > 0:
            print(f"過剰金額: {shortage_or_surplus}円")
            reason = self.handle_cash_difference(shortage_or_surplus, cash_amount)
            self.record_cash_register(total_sales, cash_amount, shortage_or_surplus, reason)
        else:
            print(f"不足金額: {abs(shortage_or_surplus)}円")
            reason = self.handle_cash_difference(shortage_or_surplus, cash_amount)
            self.record_cash_register(total_sales, cash_amount, shortage_or_surplus, reason)

        self.display_daily_transaction_counts()

    def intermediate_reconciliation(self):
        total_sales = self.calculate_total_sales()
        cash_amount = self.count_cash()
        shortage_or_surplus = cash_amount - total_sales

        print("\n=中間精算=")
        print(f"総売上金額: {total_sales}円")
        print(f"現金残高: {cash_amount}円")

        if shortage_or_surplus == 0:
            print("金額は正しいです")
        elif shortage_or_surplus > 0:
            print(f"過剰金額: {shortage_or_surplus}円")
        else:
            print(f"不足金額: {abs(shortage_or_surplus)}円")

    def calculate_total_sales(self):
        with self.db_connector.connect("sales") as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT SUM(total_amount)
                FROM Transactions
                WHERE DATE(date) = DATE('now')
            """)
            result = cur.fetchone()[0]
            return result if result else 0

    def count_cash(self):
        print("\n金種入力:")
        cash_amount = 0
        denominations = [10000, 5000, 2000, 1000, 500, 100, 50, 10, 5, 1]
        for denomination in denominations:
            count = input(f"{denomination}円の枚数: ")
            if count.isdigit():
                cash_amount += int(count) * denomination
        return cash_amount

    def handle_cash_difference(self, shortage_or_surplus, cash_amount):
        while True:
            choice = input("金額の差異がありました。再入力しますか？ (y/n) ")
            if choice.lower() == "y":
                cash_amount = self.count_cash()
                shortage_or_surplus = cash_amount - self.calculate_total_sales()
                print(f"現金残高: {cash_amount}円")
                if shortage_or_surplus == 0:
                    print("締めは問題ありません")
                    return None
                elif shortage_or_surplus > 0:
                    print(f"過剰金額: {shortage_or_surplus}円")
                else:
                    print(f"不足金額: {abs(shortage_or_surplus)}円")
            elif choice.lower() == "n":
                reason = input("差異の理由を入力してください: ")
                return reason
            else:
                print("無効な入力です。'y' または 'n' を入力してください。")

    def record_cash_register(self, total_sales, cash_amount, difference, reason=None):
        with self.db_connector.connect("sales") as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO cash_registers (date, staffCode, total_sales, cash_amount, difference, reason)
                VALUES (DATE('now'), ?, ?, ?, ?, ?)
            """, (g.staffCode, total_sales, cash_amount, difference, reason))
            conn.commit()

    def display_daily_transaction_counts(self):
        with self.db_connector.connect("sales") as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM Transactions WHERE DATE(date) = DATE('now') AND sales_type = 1) AS sales_count,
                    (SELECT COUNT(*) FROM Transactions WHERE DATE(date) = DATE('now') AND sales_type = 2) AS refund_count
            """)
            sales_count, refund_count = cur.fetchone()
            print(f"当日の売上取引件数: {sales_count}")
            print(f"当日の返品件数: {refund_count}")
