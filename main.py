import sqlite3

dbname = "items.sqlite"


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
    print("\n1.商品登録・変更\n2.登録削除\n3..入庫処理")
    mode = input("業務選択:")
    if mode == "":
        main()
    elif mode == "1":
        register_or_update_item()
    elif mode == "2":
        delete_item()
    elif mode == "3":
        update_stock()


def register_or_update_item():
    print("\n商品登録・変更")
    with connect_db() as conn:
        cur = conn.cursor()
        JAN = input("JAN:")
        cur.execute("SELECT stock FROM items WHERE JAN = ?", (JAN,))
        row = cur.fetchone()
        if row:
            print("そのJANコードはすでに登録済みです")
            master_maintenance()
            # ここに更新処理を書く
        else:
            None
        name = input("商品名:")
        tax = input("税率:")
        price = input("税抜価格:")
        stock = input("初期在庫:")

        print(f"\n登録情報:\nJAN: {JAN}\n商品名: {name}\n税率: {tax}\n税抜価格: {price}\n初期在庫: {stock}\n")
        confirm = input("上記の情報で登録しますか？(Y/n): ")

        if confirm == "y" or "Y" or "":
            cur.execute(
                "INSERT INTO items(JAN, name, tax, price, stock) values(?, ?, ?, ?, ?)", (JAN, name, tax, price, stock)
            )
            print("商品情報を登録しました。")
        else:
            print("商品情報の登録をキャンセルしました。")


def delete_item():
    print("\n登録削除")
    with connect_db() as conn:
        cur = conn.cursor()
        JAN = input("JAN:")
        cur.execute("SELECT * FROM items WHERE JAN = ?", (JAN,))
        row = cur.fetchone()
        if row:
            cur.execute("DELETE FROM items WHERE JAN = ?", (JAN,))
        else:
            print("該当するデータはありません。")
            delete_item()


def update_stock():
    print("\n入庫処理")
    with connect_db() as conn:
        cur = conn.cursor()
        JAN = input("JAN:")
        if JAN == "":
            master_maintenance()
        else:
            cur.execute("SELECT stock FROM items WHERE JAN = ?", (JAN,))
            row = cur.fetchone()
            print(row)
            if row:
                print("現在在庫:" + str(row[0]))
                stock_after = input("更新後在庫:")
                cur.execute("UPDATE items SET stock = ? WHERE JAN = ?", (stock_after, JAN))
            else:
                print("該当するデータはありません。")
                update_stock()


def main():
    print("\n1.売上登録\n2.マスターメンテ")
    mode = input("業務選択：")
    if mode == "1":
        register_sales()
    elif mode == "2":
        master_maintenance()


if __name__ == "__main__":
    main()
