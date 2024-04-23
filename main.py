import sqlite3

dbname = "items.sqlite"
conn = sqlite3.connect(dbname)
cur = conn.cursor()

print("1.売上登録\n2.マスターメンテ")
mode = input("業務選択：")
if mode == "1":
    total = 0
    while True:
        barcode = input("JAN入力:")
        if barcode == "":
            print("total:" + str(total))
            break
        cur.execute("SELECT * FROM items WHERE JAN = ?", (barcode,))
        row = cur.fetchone()
        print(row)
        if row:
            total = total + row[0]
        else:
            print("該当するデータはありません。")
elif mode == "2":
    print("\n1.商品登録・変更\n2.登録削除\n3.在庫修正")
    mode = input("業務選択:")
    if mode == "1":
        print("商品登録・変更")
        JAN = input("JAN:")
        name = input("商品名:")
        tax = input("税率:")
        price = input("税抜価格:")
        stock = input("初期在庫:")
        cur.execute(
            "INSERT INTO items(JAN, name, tax, price, stock) values(?, ?, ?, ?, ?)", (JAN, name, tax, price, stock)
        )
        conn.commit()
    elif mode == "2":
        print("登録削除")
        JAN = input("JAN:")
        cur.execute("DELETE FROM items WHERE JAN = ?", (JAN,))
        conn.commit()
    elif mode == "3":
        print("在庫修正")
        JAN = input("JAN:")
        cur.execute("SELECT stock FROM items WHERE JAN = ?", (JAN,))
        row = cur.fetchone()
        print(row)
        if row:
            print("現在在庫:" + str(row[0]))
            stock_after = input("更新後在庫:")
            cur.execute("UPDATE items SET stock = ? WHERE JAN = ?", (stock_after, JAN))
            conn.commit()
        else:
            print("該当するデータはありません。")


cur.close()
conn.close()
