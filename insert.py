import sqlite3

dbname = "master.sqlite"


def create_tables(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            JAN INTEGER NOT NULL UNIQUE,
            name TEXT,
            tax INTEGER DEFAULT 10 CHECK (tax >= 0),
            price INTEGER,
            stock INTEGER)
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS permissions(
            permission_level INTEGER PRIMARY KEY NOT NULL UNIQUE,
            permission_name TEXT)
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS staffs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staffCode INTEGER NOT NULL UNIQUE,
            name TEXT,
            password TEXT,
            permission INTEGER,
            FOREIGN KEY(permission) REFERENCES permissions(permission_level))
        """
    )


# 【実装予定】itemsDataに入力する前にチェックディジットをチェックする
def is_valid_jan_code(jan_code_str):
    def calculate_checksum(numbers):
        accumulated_sum, multiplier = 0, 3
        for number in reversed(numbers):
            accumulated_sum += int(number) * multiplier
            multiplier = 1 if multiplier == 3 else 3
        return accumulated_sum

    numbers = list(jan_code_str[:-1])  # JANコードからチェックディジットを除いたリスト
    expected_cd = calculate_checksum(numbers) % 10
    expected_cd = 10 - expected_cd if expected_cd != 0 else 0
    actual_cd = int(jan_code_str[-1])  # 入力されたJANコードのチェックディジット

    return expected_cd == actual_cd

def upsert_items_data(cur):
    items_data = [
        (4953103254350, "EDT-TMEX10", 10, 1562, 10),
        (4901411133157, "ｷﾘﾝ晴れ風缶350ml×6", 8, 1014, 10),
        (4901411133133, "ｷﾘﾝ晴れ風缶350ml", 8, 185, 10),
        (4901411133171, "ｷﾘﾝ晴れ風缶500ml", 8, 246, 10),
        (4901411133164, "ｷﾘﾝ晴れ風缶350ml×6×4", 8, 4017, 10),
        (4901004061331, "ｱｻﾋｱｻﾋｵﾌ缶350ml×6×4", 8, 3127, 10),
        (4901411133195, "ｷﾘﾝ晴れ風缶500ml×6", 8, 1375, 10),
        (4901004061324, "ｱｻﾋｱｻﾋｵﾌ缶350ml×6", 8, 791, 10),
        (4901004057686, "ｱｻﾋ富士山缶350ml", 8, 190, 10),
        (4901004061300, "ｱｻﾋｱｻﾋｵﾌ缶500ml×6×4", 8, 4438, 10),
        (4901411133225, "ｷﾘﾝ晴れ風缶500ml×6×4", 8, 5422, 10),
        (4901004057693, "ｱｻﾋ富士山缶350ml×6", 8, 1102, 10),
        (4901004061294, "ｱｻﾋｱｻﾋｵﾌ缶500ml×6", 8, 1131, 10),
        (4904230073536, "ｱｻﾋGINONﾚﾓﾝ缶350ml", 8, 107, 10),
        (4901777413290, "BARPomum和梨&ｼﾞﾝﾄﾆｯｸ350ml", 8, 128, 10),
        (4901880211141, "黒ﾗﾍﾞﾙｴｸｽﾄﾗﾌﾞﾘｭｰ350ml×6", 8, 1047, 10),
        (4904230073574, "ｱｻﾋGINONｸﾞﾚｰﾌﾟﾌﾙｰﾂ缶350ml", 8, 107, 10),
        (4901004061638, "ｱｻﾋ食彩缶340ml×6", 8, 1311, 10),
        (4901880210564, "ヱﾋﾞｽｼﾄﾗｽﾌﾞﾗﾝ缶350ml×6", 8, 1472, 10),
        (4901777411227, "茉莉花ｼﾞｬｽﾐﾝ茶割･JJ缶335ml", 8, 148, 10),
        (4901870647233, "CGCｲﾝﾍﾟﾘｱﾙｶﾞｰﾄﾞ700ml", 8, 983, 10),
        (4901880211134, "黒ﾗﾍﾞﾙｴｸｽﾄﾗﾌﾞﾘｭｰ缶500ml", 8, 254, 10),
        (4901777415690, "友達がやってるﾊﾞｰｼﾞﾝﾄﾆｯｸ350ml", 8, 134, 10),
        (4901880210557, "ｻｯﾎﾟﾛヱﾋﾞｽｼﾄﾗｽﾌﾞﾗﾝ350ml", 8, 249, 10),
        (4904230073512, "ｱｻﾋGINONﾚﾓﾝ缶500ml", 8, 153, 10),
        (4901777415362, "友達がやってるﾊﾞｰﾗﾑｺｰﾗ350ml", 8, 134, 10),
        (4901411131597, "ｷﾘﾝｽﾌﾟﾘﾝｸﾞﾊﾞﾚｰ豊潤350ml×6", 8, 1439, 10),
        (4901004061690, "ｱｻﾋ食彩缶340ml", 8, 230, 10),
        (4901004061256, "ｱｻﾋｱｻﾋｵﾌ缶500ml", 8, 202, 10),
        (4901880211127, "黒ﾗﾍﾞﾙｴｸｽﾄﾗﾌﾞﾘｭｰ缶350ml", 8, 185, 10),
        (4904230073550, "ｱｻﾋGINONｸﾞﾚｰﾌﾟﾌﾙｰﾂ缶500ml", 8, 153, 10),
        (4901004061607, "ｱｻﾋ食彩缶485ml×6", 8, 1748, 10),
        (4901777409804, "-196無糖ｵﾚﾝｼﾞ&ﾚﾓﾝ350ml", 8, 103, 10),
        (4901004061270, "ｱｻﾋｱｻﾋｵﾌ缶350ml", 8, 143, 10),
        (4901411131733, "ｽﾌﾟﾘﾝｸﾞﾊﾞﾚｰｼﾙｸｴｰﾙ350ml×6", 8, 1450, 10),
        (4904230073192, "ｱｻﾋ贅沢搾りﾌﾟﾚﾐｱﾑぶどう缶350ml", 8, 134, 10),
        (4901411131832, "ｽﾌﾟﾘﾝｸﾞﾊﾞﾚｰｼﾞｬﾊﾟﾝｴｰﾙ350ml×6", 8, 1446, 10),
        (4901777415218, "ｻﾞﾌﾟﾚﾐｱﾑﾓﾙﾂそよ風ｴｰﾙ350ml×6", 8, 1125, 10),
        (4901777415195, "ｻﾞﾌﾟﾚﾐｱﾑﾓﾙﾂそよ風ｴｰﾙ缶350ml", 8, 200, 10),
        (4901777409828, "-196無糖ｵﾚﾝｼﾞ&ﾚﾓﾝ500ml", 8, 145, 10),
        (4901411130194, "麒麟百年極み仕立てﾚﾓﾝｻﾜｰ缶350ml", 8, 136, 10),
        (4930391140763, "菊水ふなぐち限定大吟醸生原酒200ml", 8, 392, 10),
        (4901880211042, "ヱﾋﾞｽｼﾄﾗｽﾌﾞﾗﾝ景品付350ml×4", 8, 944, 10),
        (4901777409767, "-196無糖ﾀﾞﾌﾞﾙｼｰｸヮｰｻｰ350ml", 8, 103, 10),
        (4901870647219, "CGCSP無糖ﾚﾓﾝｻﾜｰ500ml", 8, 136, 10),
        (4902102155076, "ｺｶｺｰﾗ檸檬堂ﾚﾓﾝ濃いめ缶350ml", 8, 142, 10),
        (4901411130279, "麒麟百年極み仕立てｸﾞﾚﾌﾙｻﾜｰ缶350ml", 8, 136, 10),
        (4902102155090, "ｺｶｺｰﾗ檸檬堂ﾚﾓﾝ濃いめ缶500ml", 8, 184, 10),
        (4901004061812, "ｱｻﾋｽｰﾊﾟｰﾄﾞﾗｲｽﾏｰﾄ缶355ml", 8, 196, 10),
        (4901777412347, "こだわり酒場のお茶ｻﾜｰ伊右衛門350ml", 8, 105, 10),
        (4901411130293, "麒麟百年極み仕立てｸﾞﾚﾌﾙｻﾜｰ缶500ml", 8, 185, 10),
        (4901411131573, "ｷﾘﾝｽﾌﾟﾘﾝｸﾞﾊﾞﾚｰ豊潤350ml", 8, 244, 10),
        (4902102154390, "ｺｶｺｰﾗｼﾞｬｯｸ&ｺｰｸｾﾞﾛｼｭｶﾞｰ350ml", 8, 193, 10),
        (4901777409781, "-196無糖ﾀﾞﾌﾞﾙｼｰｸヮｰｻｰ500ml", 8, 146, 10),
        (4901777411999, "無添加のおいしいﾜｲﾝ｡黒ぶどうﾎﾟﾘ1.8L", 8, 1057, 10),
        (4901411131795, "ｽﾌﾟﾘﾝｸﾞﾊﾞﾚｰｼﾞｬﾊﾟﾝｴｰﾙ缶350ml", 8, 244, 10),
        (4901880211165, "ﾆｯﾎﾟﾝのｼﾝ･ﾚﾓﾝｻﾜｰ350ml×6", 8, 644, 10),
        (4901777412361, "こだわり酒場のお茶ｻﾜｰ伊右衛門500ml", 8, 147, 10),
        (4901004061683, "ｱｻﾋ食彩缶485ml", 8, 299, 10),
        (4971650205571, "菊正宗灘のしぼりたて生貯蔵酒2L", 8, 874, 10),
        (4901870647196, "CGCSP無糖ﾚﾓﾝｻﾜｰ350ml", 8, 97, 10),
        (4901411121451, "本搾りﾌﾟﾚﾐｱﾑ4種のﾚﾓﾝと日向夏350ml", 8, 135, 10),
        (4901411121499, "本搾りﾌﾟﾚﾐｱﾑ3種の柑橘とｼｰｸヮｰｻｰ350", 8, 132, 10),
        (4901411130231, "麒麟百年極み仕立てﾚﾓﾝｻﾜｰ缶500ml", 8, 184, 10),
        (4901004061652, "ｵﾘｵﾝ75BEERﾎﾜｲﾄ缶350ml", 8, 268, 10),
        (4901411131696, "ｽﾌﾟﾘﾝｸﾞﾊﾞﾚｰｼﾙｸｴｰﾙ缶350ml", 8, 245, 10),
        (4901777410756, "ほろよい苺さくらんぼ缶350ml", 8, 106, 10),
        (4904230073420, "贅沢搾りﾌﾟﾚﾐｱﾑﾗｲﾁ期間限定缶350ml", 8, 138, 10),
        (4901411122090, "ｷﾘﾝ氷結無糖ｳﾒ7度缶350ml", 8, 111, 10),
        (4901411121475, "本搾りﾌﾟﾚﾐｱﾑ4種のﾚﾓﾝと日向夏500ml", 8, 182, 10),
        (4901411131634, "ｷﾘﾝｽﾌﾟﾘﾝｸﾞﾊﾞﾚｰ豊潤500ml", 8, 323, 10),
        (4962840968383, "JｰCRAFTTRIPじゃばらｻﾜｰ350ml", 8, 139, 10),
        (4901411122137, "ｷﾘﾝ氷結無糖ｳﾒ7度缶500ml", 8, 158, 10),
        (4901411131856, "ｽﾌﾟﾘﾝｸﾞﾊﾞﾚｰｼﾞｬﾊﾟﾝｴｰﾙ缶500ml", 8, 316, 10),
        (4901411130651, "ｷﾘﾝ上々焼酎ｿｰﾀﾞ梅缶350ml", 8, 143, 10),
        (4901411121536, "本搾りﾌﾟﾚﾐｱﾑ3種の柑橘とｼｰｸヮｰｻｰ500", 8, 185, 10),
        (4901777413603, "ﾄﾘﾊｲｸﾗﾌﾄｺｰﾗ缶350ml", 8, 148, 10),
        (4901411130675, "ｷﾘﾝ上々焼酎ｿｰﾀﾞ梅缶500ml", 8, 193, 10),
        (4936790540715, "富永神戸居留地ﾊｲﾎﾞｰﾙ缶340ml", 8, 118, 10),
        (4901777411081, "ﾌﾟﾚﾓﾙｻｽﾃﾅﾌﾞﾙｱﾙﾐ350ml", 8, 204, 10),
        (4904670496216, "ﾀｶﾗ焼酎ﾊｲﾎﾞｰﾙ特製ｺｰﾗ割り5度350ml", 8, 108, 10),
        (4971980789260, "すご焼酎ﾊｲﾎﾞｰﾙ絶妙ﾌﾞﾚﾝﾄﾞ甲乙350ml", 8, 102, 10),
        (4905846118666, "ﾁｮｰﾔ梅ﾘｯﾁﾎﾞﾄﾙ缶300ml", 8, 212, 10),
        (4901777410909, "ｻﾝﾄﾘｰ春の白桃ﾁｭｰﾊｲ350ml", 8, 109, 10),
        (4901777411470, "ｻﾝﾄﾘｰ春の白ぶどうﾁｭｰﾊｲ350ml", 8, 108, 10),
        (4902102155014, "ｺｶｺｰﾗ檸檬堂さっぱり定番缶350ml", 8, 138, 10),
        (4901411131757, "ｽﾌﾟﾘﾝｸﾞﾊﾞﾚｰｼﾙｸｴｰﾙ缶500ml", 8, 322, 10),
        (4901777413450, "ｻﾞ･ｳｰヴｧﾚｯﾄﾞﾍﾟｯﾄ720ml", 8, 536, 10),
        (4904670497688, "ﾀｶﾗ焼酎ﾊｲﾎﾞｰﾙ特製ｺｰﾗ割り5度500ml", 8, 150, 10),
        (4904230073475, "ﾆｯｶ弘前生ｼｰﾄﾞﾙ紅玉びん200ml", 8, 274, 10),
        (4901777413566, "ｻﾞ･ｳｰヴｧﾎﾜｲﾄﾍﾟｯﾄ720ml", 8, 529, 10),
        (4901777411975, "無添加のおいしいﾜｲﾝ黒ぶどうﾎﾟﾘ720ml", 8, 524, 10),
        (4962840968369, "JｰCRAFTTRIP日向夏ｻﾜｰ350ml", 8, 140, 10),
        (4901880210854, "ｸﾗﾌﾄｽﾊﾟｲｽｿｰﾀﾞ旬の彩り缶500ml", 8, 151, 10),
        (4973480346844, "CYTﾌﾛﾝﾃﾗｽﾊﾟｰｸﾘﾝｸﾞ缶280ml", 8, 299, 10),
        (4901880210847, "ｸﾗﾌﾄｽﾊﾟｲｽｿｰﾀﾞ旬の彩り缶350ml", 8, 114, 10),
    ]
    for item in items_data:
        # 既存データの更新
        cur.execute(
            """
            UPDATE items
            SET name = ?, tax = ?, price = ?, stock = ?
            WHERE JAN = ?
            """,
            (item[1], item[2], item[3], item[4], item[0])
        )
        # 更新された行がなければ、新規挿入
        if cur.rowcount == 0:
            cur.execute(
                """
                INSERT INTO items (JAN, name, tax, price, stock)
                VALUES (?, ?, ?, ?, ?)
                """,
                item
            )


def upsert_staffs_data(cur):
    staffs_data = [
        (11112, "テストユーザー1", "password1", 1),
        (11113, "テストユーザー2", "password2", 3),
        (11114, "テストユーザー3", "password3", 3),
        (11115, "テストユーザー4", "password4", 5),
        (11116, "テストユーザー5", "password5", 5),
        (11117, "テストユーザー6", "password6", 5),
        (11118, "テストユーザー7", "password7", 5),
        (11119, "テストユーザー8", "password8", 6),
        (11120, "テストユーザー9", "password9", 6),
        (11121, "テストユーザー10", "password10", 6),
    ]
    for staff in staffs_data:
        # 既存データの更新
        cur.execute(
            """
            UPDATE staffs
            SET name = ?, password = ?, permission = ?
            WHERE staffCode = ?
            """,
            (staff[1], staff[2], staff[3], staff[0])
        )
        # 更新された行がなければ、新規挿入
        if cur.rowcount == 0:
            cur.execute(
                """
                INSERT INTO staffs (staffCode, name, password, permission)
                VALUES (?, ?, ?, ?)
                """,
                staff
            )

def upsert_permissions_data(cur):
    permissions_data = [
        (1, "SystemAdmin"),
        (2, "Reserved1"),
        (3, "StoreManager"),
        (4, "Reserved2"),
        (5, "A_Staff"),
        (6, "B_Staff"),
    ]
    for permission_level, permission_name in permissions_data:
        # まず、UPDATEを試みる
        cur.execute(
            "UPDATE permissions SET permission_name = ? WHERE permission_level = ?",
            (permission_name, permission_level),
        )
        # 更新が行われなかった場合、INSERTを試みる
        if cur.rowcount == 0:
            cur.execute(
                "INSERT INTO permissions(permission_level, permission_name) VALUES (?, ?)",
                (permission_level, permission_name),
            )

def setup_database():
    try:
        with sqlite3.connect(dbname) as conn:
            cur = conn.cursor()
            # 外部キー制約を有効
            cur.execute("PRAGMA foreign_keys = ON")
            # トランザクション区間開始
            cur.execute("BEGIN TRANSACTION")

            create_tables(cur)
            upsert_permissions_data(cur)
            upsert_items_data(cur)
            upsert_staffs_data(cur)

            conn.commit()
            print("Successfully setup the database!")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")


setup_database()
