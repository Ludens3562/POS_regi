from SalesRegister import SalesRegister, ReturnRegister, TransactionHistory, CashRegister
from StoreMaster import StoreMaster
from auth import Authentication
from insert import table_master
import directSQL
import global_value as g

auth = Authentication()
sales_register = SalesRegister()
return_register = ReturnRegister()
cash_register = CashRegister(sales_register)
history = TransactionHistory()
store_master = StoreMaster()
DB_master = table_master()


def top_page():
    while True:
        print("\n===業務選択===")
        print(
            "1.売上登録\n2.返品処理\n3.保留呼び出し\n4.ジャーナル検索\n5.レジ締め処理\n6.中間締め処理\n7.マスターメンテ\n8.SQL実行\n9.DBメンテ\n10.ログオフ\n11.終了"
        )
        mode = input("業務選択：")
        if mode == "1":
            sales_register.register_sales()
            break
        elif mode == "2":
            return_register.return_process()
            break
        elif mode == "3":
            sales_register.resume_hold_checkout()
            break
        elif mode == "4":
            history.search_transactions()
            break
        elif mode == "5":
            cash_register.close_register()
        elif mode == "6":
            cash_register.intermediate_reconciliation()
        elif mode == "7":
            if auth.check_permission(g.staffCode, 5):
                print("\n権限チェックOK")
                store_master.maintenance_page()
            else:
                print("\n権限が足りません")
                break
        elif mode == "8":
            directSQL.main()
            break
        elif mode == "9":
            DB_master.main_menu()
            break
        elif mode == "10":
            auth.logoff()
            main()
        elif mode == "11":
            print("\nお疲れさまでした！")
            exit()
        else:
            pass


def main():
    auth.logon()
    top_page()


if __name__ == "__main__":
    main()
