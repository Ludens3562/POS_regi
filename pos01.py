import pandas as pd


while True:
    barcode=input("バーコードリーダーでリードしてください") 
    df=pd.read_csv("p.csv")
    
    if str(49)  in barcode:
        gendata=df[df["code"].astype(str).str.contains(str(barcode))]
        #print(barcode+"です！")
        print(str(gendata))
        
        result=df[df["code"]==barcode]
        print(result)
         