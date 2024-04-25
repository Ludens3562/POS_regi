import sqlite3

dbname = "master.sqlite"
def connect_db():
    return sqlite3.connect(dbname)

class StoreMaster:
    def maintenance_page(self):
        print("\n==マスターメンテナンスメニュー==")
        print("1.商品登録・変更\n2.登録削除\n3.入庫処理")
        mode = input("業務選択:")
        if mode == "":
            pass
        elif mode == "1":
            self.register_or_update_item()
        elif mode == "2":
            self.delete_item()
        elif mode == "3":
            self.receive_stock()
        else:
            print("無効な選択です。")
            self.maintenance_page()

    def update_item(self, JAN):
        with connect_db() as conn:
            self.cur = conn.cursor()
            print("\n更新する項目を選択してください:")
            print("1: 商品名\n2: 税率\n3: 税抜価格\n4: 初期在庫")
            choice = input("選択:")
            self.cur.execute("SELECT name, JAN, tax, price, stock FROM items WHERE JAN = ?", (JAN,))
            item = self.cur.fetchone()
            if choice == "1":
                print(f"\n現在の商品名: {item[0]}")
                name = input("新しい商品名: ")
                self.cur.execute("UPDATE items SET name = ? WHERE JAN = ?", (name, JAN))
                conn.commit()
                print("商品名を更新しました")
            elif choice == "2":
                print(f"\n現在の税率: {item[2]}")
                tax = input("新しい税率: ")
                self.cur.execute("UPDATE items SET tax = ? WHERE JAN = ?", (tax, JAN))
                conn.commit()
                print("税率を更新しました")
            elif choice == "3":
                print(f"\n現在の税抜価格: {item[3]}")
                price = input("新しい税抜価格: ")
                self.cur.execute("UPDATE items SET price = ? WHERE JAN = ?", (price, JAN))
                conn.commit()
                print("税抜き価格を更新しました")
            elif choice == "4":
                print(f"\n現在の在庫数: {item[4]}")
                stock = input("新しい在庫数: ")
                self.cur.execute("UPDATE items SET stock = ? WHERE JAN = ?", (stock, JAN))
                conn.commit()
                print("在庫数を更新しました")
            elif choice == "":
                self.register_or_update_item()
            else:
                print("無効な選択")
            self.update_item(item[1])

    def register_or_update_item(self):
        print("\n=商品登録・変更=")
        with connect_db() as conn:
            self.cur = conn.cursor()
            JAN = input("登録・更新を行うJANを入力:")
            if JAN == "":
                self.maintenance_page()
            self.cur.execute("SELECT stock FROM items WHERE JAN = ?", (JAN,))
            row = self.cur.fetchone()
            if row:
                print("登録済みJANコードのため更新を行います")
                self.update_item(JAN)
            else:
                print("\n登録のないJANコードのため新規登録を行います")
                name = input("商品名:")
                tax = input("税率:")
                price = input("税抜価格:")
                stock = input("初期在庫:")
                
                print(f"\n登録情報:\nJAN: {JAN}\n商品名: {name}\n税率: {tax}\n税抜価格: {price}\n初期在庫: {stock}\n")
                confirm = input("上記の情報で登録しますか？(Y/n): ")
                if confirm.lower() == "y" or confirm == "":
                    self.cur.execute(
                        "INSERT INTO items(JAN, name, tax, price, stock) values(?, ?, ?, ?, ?)",
                        (JAN, name, tax, price, stock),
                    )
                    conn.commit()
                    print("商品情報を登録しました")
                    self.maintenance_page()
                else:
                    print("商品情報の登録をキャンセルしました")
                    self.maintenance_page()

    def delete_item(self):
        print("\n=登録削除=")
        with connect_db() as conn:
            self.cur = conn.cursor()
            JAN = input("削除するJAN:")
            if JAN == "":
                self.maintenance_page()
            self.cur.execute("SELECT * FROM items WHERE JAN = ?", (JAN,))
            row = self.cur.fetchone()
            if row:
                confirm = input("上記の登録情報を削除しますか？(Y/n): ")
                if confirm.lower() in ["y", ""]:
                    self.cur.execute("DELETE FROM items WHERE JAN = ?", (JAN,))
                    conn.commit()
                    print("データを削除しました。")
                    self.delete_item()
                else:
                    print("削除をキャンセルしました")
                    self.delete_item()
            else:
                print("該当するデータはありません")
                self.delete_item()

    def receive_stock(self):
        print("\n=入庫処理=")
        with connect_db() as conn:
            self.cur = conn.cursor()
            JAN = input("JAN:")
            if JAN == "":
                self.maintenance_page()
            self.cur.execute("SELECT stock FROM items WHERE JAN = ?", (JAN,))
            row = self.cur.fetchone()
            if row:
                print("現在在庫:" + str(row[0]))
                stock_after = input("更新後在庫:")
                self.cur.execute("UPDATE items SET stock = ? WHERE JAN = ?", (stock_after, JAN))
                conn.commit()
                print("在庫数を更新しました")
                self.receive_stock()
            else:
                print("該当するデータはありません")
                self.receive_stock()