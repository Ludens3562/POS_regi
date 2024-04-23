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
                break
            cur.execute("SELECT * FROM items WHERE JAN = ?", (barcode,))
            row = cur.fetchone()
            if row:
                # print(str(row[4]))
                total += row[4]
            else:
                print("該当するデータはありません。")


def master_maintenance():
    print("\n1.商品登録・変更\n2.登録削除\n3.在庫修正")
    mode = input("業務選択:")
    if mode == "1":
        register_or_update_item()
    elif mode == "2":
        delete_item()
    elif mode == "3":
        update_stock()


def register_or_update_item():
    print("商品登録・変更")
    with connect_db() as conn:
        cur = conn.cursor()
        JAN = input("JAN:")
        name = input("商品名:")
        tax = input("税率:")
        price = input("税抜価格:")
        stock = input("初期在庫:")
        cur.execute(
            "INSERT INTO items(JAN, name, tax, price, stock) values(?, ?, ?, ?, ?)", (JAN, name, tax, price, stock)
        )


def delete_item():
    print("登録削除")
    with connect_db() as conn:
        cur = conn.cursor()
        JAN = input("JAN:")
        cur.execute("DELETE FROM items WHERE JAN = ?", (JAN,))


def update_stock():
    print("在庫修正")
    with connect_db() as conn:
        cur = conn.cursor()
        JAN = input("JAN:")
        cur.execute("SELECT stock FROM items WHERE JAN = ?", (JAN,))
        row = cur.fetchone()
        print(row)
        if row:
            print("現在在庫:" + str(row[0]))
            stock_after = input("更新後在庫:")
            cur.execute("UPDATE items SET stock = ? WHERE JAN = ?", (stock_after, JAN))


def main():
    print("1.売上登録\n2.マスターメンテ")
    mode = input("業務選択：")
    if mode == "1":
        register_sales()
    elif mode == "2":
        master_maintenance()


if __name__ == "__main__":
    main()
