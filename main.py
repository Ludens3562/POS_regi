import sqlite3

dbname = "items.sqlite"
conn = sqlite3.connect(dbname)
cur = conn.cursor()
total = 0

# terminalで実行したSQL文と同じようにexecute()に書く
cur.execute("SELECT * FROM items")

while True:
    barcode = input("JAN入力:")
    if barcode == "":
        print("total:" + str(total))
        break
    cur.execute("SELECT * FROM items WHERE JAN = ?", (barcode,))
    row = cur.fetchone()
    if row:
        total = total + row[0]
    else:
        print("該当するデータはありません。")


cur.close()
conn.close()
