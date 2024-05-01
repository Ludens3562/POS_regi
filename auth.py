import sqlite3
import bcrypt
import global_value as g


class Authentication:
    def __init__(self):
        self.dbname = "master.sqlite"

    def connect_db(self):
        return sqlite3.connect(self.dbname)

    def logon(self):
        with self.connect_db() as conn:
            cur = conn.cursor()
            g.staffCode = input("\n社員コードを入力してください:")
            cur.execute("SELECT * FROM staffs WHERE staffCode = ?", (g.staffCode,))
            row = cur.fetchone()
            if row:
                print("\n" + row[2] + "としてログインしました")
                return
            else:
                print("無効な入力です\n")
                return self.logon()

    def logoff(self):
        g.staffCode = ""
        print("ログオフしました。\n\n\n\n\n")

    def check_permission(self, staffCode, requireLevel):
        with self.connect_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT permission_level FROM staffs WHERE staffCode = ?", (staffCode,))
            row = cur.fetchone()
            if row:
                if row[0] <= requireLevel:
                    return True
                elif row[0] > requireLevel:
                    return False
            else:
                return None

    def verify_password(self, input_password, stored_password_hash):
        input_password_bytes = input_password.encode("utf-8")
        stored_password_hash_bytes = stored_password_hash
        return bcrypt.checkpw(input_password_bytes, stored_password_hash_bytes)
