import sqlite3

def execute_sql_command(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    while True:
        sql_command = input("SQLコマンドを入力してください（終了するには'exit'と入力）: ")
        if sql_command.lower() == "exit":
            print("データベースセッションを終了します")
            break
        try:
            cursor.execute(sql_command)
            if sql_command.strip().lower().startswith("select"):
                for row in cursor.fetchall():
                    print(row)
            else:
                conn.commit()
                print("成功しました")
        except sqlite3.Error as e:
            print(f"エラーが発生しました: {e}")
    conn.close()

def main():
    while True:
        db_choice = input("操作するデータベースを選択してください（1: マスター, 2: 販売履歴, 3: 終了）: ")
        if db_choice == "1":
            print("マスターに接続します")
            execute_sql_command("master.sqlite")
        elif db_choice == "2":
            print(" 販売履歴に接続します")
            execute_sql_command("salesHistory.sqlite")
        elif db_choice.lower() == "3":
            print("プログラムを終了します")
            break
        else:
            print("無効な入力。")

if __name__ == "__main__":
    main()