from SalesRegister import SalesRegister
from SalesRegister import ReturnRegister
from SalesRegister import TransactionHistory
from StoreMaster import StoreMaster
from auth import Authentication
import directSQL
import global_value as g

auth = Authentication()


def top_page():
    print("\n===業務選択===")
    print("1.売上登録\n2.マスターメンテ\n3.ログオフ\n4.終了\n5.返品処理\n6.ジャーナル検索\n7.SQL直接実行")
    mode = input("業務選択：")
    if mode == "1":
        sales_register = SalesRegister()
        sales_register.register_sales()
    elif mode == "2":
        Store_Master = StoreMaster()
        if auth.check_permission(g.staffCode, 5):
            print("\n権限チェックOK")
            Store_Master.maintenance_page()
        else:
            print("\n権限が足りません")
            top_page()
    elif mode == "3":
        auth.logoff()
        main()
    elif mode == "4":
        print("\nお疲れさまでした！")
        exit
    elif mode == "5":
        return_register = ReturnRegister()
        return_register.return_process()
    elif mode == "6":
        history = TransactionHistory()
        history.search_transactions()
    elif mode == "7":
        directSQL.main()
    else:
        print("\n無効な選択")
        top_page()


def main():
    auth.logon()
    top_page()


if __name__ == "__main__":
    main()
