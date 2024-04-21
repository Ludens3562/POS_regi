import pandas as pd
import warnings

warnings.simplefilter("ignore", FutureWarning)

sum_price = 0
cnt = 0
while True:
    barcode = input("バーコードリーダーで商品をリードしてください...")
    df = pd.read_csv("p.csv")

    if str(49) in barcode:
        gendata = df[df["code"].astype(str).str.contains(str(barcode))]
        # print(str(gendata))

        # それぞれのデータ読み込み
        each_price = int(gendata["price"])
        sum_price += int(each_price)
        cnt += 1
        each_product = str(gendata["product"].values[0])
        print(each_product + "は" + str(each_price) + "円です。")
        print(str(cnt) + "点で現在の合計" + str(sum_price) + "円です。")

    if str(28) in barcode:
        print(
            "ポイントカード、ありがとうございます。お会計は"
            + str(sum_price)
            + "円になります。"
        )
