import sqlite3

dbname = "salesHistory.sqlite"


def create_tables(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS `Transactions` (
            `transaction_id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `sales_type` INTEGER,
            `date` DATETIME,
            `staffCode` INTEGER,
            `purchase_points` INTEGER,
            `total_tax_amount` INTEGER,
            `total_base_price` INTEGER,
            `total_amount` INTEGER,
            `deposit` INTEGER,
            `change` INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS `sales_item` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `transaction_id` INTEGER NOT NULL,
            `JAN` INTEGER,
            `product_name` TEXT,
            `unit_price` INTEGER,
            `tax_rate` INTEGER,
            `amount` INTEGER,
            FOREIGN KEY (`transaction_id`) REFERENCES `Transactions`(`transaction_id`)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hold_transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATETIME,
            purchase_items TEXT)
        """
    )


def setup_database():
    try:
        with sqlite3.connect(dbname) as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA foreign_keys = ON")
            cur.execute("BEGIN TRANSACTION")
            create_tables(cur)
            conn.commit()
            print("Successfully setup the database!")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")


setup_database()
