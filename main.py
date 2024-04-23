import sqlite3

dbname = "master.sqlite"


def connect_db():
    return sqlite3.connect(dbname)


def register_sales():
    total = 0
    with connect_db() as conn:
        cur = conn.cursor()
        while True:
            barcode = input("JAN入力:")
            if barcode == "":
                print("total:" + str(total))
                register_sales()
            cur.execute("SELECT * FROM items WHERE JAN = ?", (barcode,))
            row = cur.fetchone()
            if row:
                # print(str(row[4]))
                total += row[4]
            else:
                print("該当するデータはありません。")


def master_maintenance():
    print("\n==マスターメンテナンスメニュー==")
    print("1.商品登録・変更\n2.登録削除\n3.入庫処理")
    mode = input("業務選択:")
    if mode == "":
        main()
    elif mode == "1":
        register_or_update_item()
    elif mode == "2":
        delete_item()
    elif mode == "3":
        update_stock()


def update_item(cur, JAN):
    print("\n更新する項目を選択してください:")
    print("1: 商品名")
    print("2: 税率")
    print("3: 税抜価格")
    print("4: 初期在庫")
    choice = input("選択: ")

    # 現在の値を取得し、表示するためのSQLクエリを実行
    cur.execute("SELECT name, JAN, tax, price, stock FROM items WHERE JAN = ?", (JAN,))
    item = cur.fetchone()

    if choice == "1":
        print(f"\n現在の商品名: {item[0]}")
        name = input("新しい商品名: ")
        cur.execute("UPDATE items SET name = ? WHERE JAN = ?", (name, JAN))
        print("商品名を更新しました")
        update_item(cur, item[1])
    elif choice == "2":
        print(f"\n現在の税率: {item[2]}")
        tax = input("新しい税率: ")
        cur.execute("UPDATE items SET tax = ? WHERE JAN = ?", (tax, JAN))
        print("税率を更新しました")
        update_item(cur, item[1])
    elif choice == "3":
        print(f"\n現在の税抜価格: {item[3]}")
        price = input("新しい税抜価格: ")
        cur.execute("UPDATE items SET price = ? WHERE JAN = ?", (price, JAN))
        print("税抜き価格を更新しました")
        update_item(cur, item[1])
    elif choice == "4":
        print(f"\n現在の在庫数: {item[4]}")
        stock = input("新しい在庫数: ")
        cur.execute("UPDATE items SET stock = ? WHERE JAN = ?", (stock, JAN))
        print("在庫数を更新しました")
        update_item(cur, item[1])
    elif choice == "":
        register_or_update_item()
    else:
        print("無効な選択です。")
        update_item(cur, item[1])


def register_or_update_item():
    print("\n=商品登録・変更=")
    with connect_db() as conn:
        cur = conn.cursor()
        JAN = input("登録・更新を行うJANを入力:")
        if JAN == "":
            master_maintenance()
        else:
            cur.execute("SELECT stock FROM items WHERE JAN = ?", (JAN,))
            row = cur.fetchone()
            if row:
                print("登録済みJANコードのため更新を行います")
                update_item(cur, JAN)
            else:
                name = input("商品名:")
                tax = input("税率:")
                price = input("税抜価格:")
                stock = input("初期在庫:")

                print(f"\n登録情報:\nJAN: {JAN}\n商品名: {name}\n税率: {tax}\n税抜価格: {price}\n初期在庫: {stock}\n")
                confirm = input("上記の情報で登録しますか？(Y/n): ")

                if confirm.lower() == "y" or confirm == "":
                    cur.execute(
                        "INSERT INTO items(JAN, name, tax, price, stock) values(?, ?, ?, ?, ?)",
                        (JAN, name, tax, price, stock),
                    )
                    print("商品情報を登録しました。")
                    master_maintenance()
                else:
                    print("商品情報の登録をキャンセルしました。")
                    master_maintenance()
            conn.commit()


def delete_item():
    print("\n=登録削除=")
    with connect_db() as conn:
        cur = conn.cursor()
        JAN = input("JAN:")
        if JAN == "":
            master_maintenance()
        else:
            cur.execute("SELECT * FROM items WHERE JAN = ?", (JAN,))
            row = cur.fetchone()
            if row:
                # 登録情報の表示
                print(
                    f"\n登録情報:\nJAN: {row[1]}\n商品名: {row[2]}\n税率: {row[3]}\n税抜価格: {row[4]}\n在庫数: {row[5]}\n"
                )
                confirm = input("上記の登録情報を削除しますか？(Y/n): ")
                if confirm.lower() == "y":
                    cur.execute("DELETE FROM items WHERE JAN = ?", (JAN,))
                    conn.commit()
                    print("データを削除しました。")
                    delete_item()
                else:
                    print("データの削除をキャンセルしました")
                    delete_item()
            else:
                print("該当するデータはありません")
                delete_item()


def update_stock():
    print("\n=入庫処理=")
    with connect_db() as conn:
        cur = conn.cursor()
        JAN = input("JAN:")
        if JAN == "":
            master_maintenance()
        else:
            cur.execute("SELECT stock FROM items WHERE JAN = ?", (JAN,))
            row = cur.fetchone()
            if row:
                print("現在在庫:" + str(row[0]))
                stock_after = input("更新後在庫:")
                cur.execute("UPDATE items SET stock = ? WHERE JAN = ?", (stock_after, JAN))
                print("在庫数を更新しました")
                update_stock()
            else:
                print("該当するデータはありません")
                update_stock()


def main():
    print("\n===業務選択===")
    print("1.売上登録\n2.マスターメンテ\n3.終了")
    mode = input("業務選択：")
    if mode == "1":
        register_sales()
    elif mode == "2":
        master_maintenance()
    elif mode == "3":
        print("\nお疲れさまでした！")
        exit
    else:
        print("\n無効な選択")
        main()


if __name__ == "__main__":
    main()
