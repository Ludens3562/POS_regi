import sqlite3
from SalesRegister import SalesRegister
from InventoryManagement import InventoryManagement

dbname = "master.sqlite"

def connect_db():
    return sqlite3.connect(dbname)

def top_page():
    print("\n===業務選択===")
    print("1.売上登録\n2.マスターメンテ\n3.ログオフ\n4.終了")
    mode = input("業務選択：")
    if mode == "1":
        sales_register = SalesRegister()
        sales_register.register_sales()
    elif mode == "2":
        Inventory_Management = InventoryManagement()
        if check_permission(staffCode, 1):
            print("\n権限チェックOK")
            Inventory_Management.maintenance_page()
        else:
            print("\n権限が足りません")
            top_page()
    elif mode == "3":
        print("ログオフしました\n\n\n\n\n")
        logon()
    elif mode == "4":
        print("\nお疲れさまでした！")
        exit
    else:
        print("\n無効な選択")
        top_page()


def logon():
    with connect_db() as conn:
        cur = conn.cursor()
        global staffCode
        staffCode = input("\n従業員CDを入力:")
        cur.execute("SELECT * FROM staffs WHERE staffCode = ?", (staffCode,))
        row = cur.fetchone()
        if row:
            print("\n" + row[2] + " としてログオン済み")
            top_page()
        else:
            print("無効な入力\n")
            logon()


def check_permission(staffCode, requireLevel):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT permission FROM staffs WHERE staffCode = ?", (staffCode,))
        row = cur.fetchone()
        if row:
            if row[0] <= requireLevel:
                return True
            elif row[0] > requireLevel:
                return False
        else:
            return None


def main():
    logon()


if __name__ == "__main__":
    main()
