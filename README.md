# POSシステム概要

## システム起動方法
①【データベースが存在しない場合】insert.pyとcreate_HistoryDB.pyを実行し、データベースファイルmaster.sqliteとsalesHistory.sqliteを作成する<br>
②main.pyを実行しログインする（従業員CDは「11112」から１０人分作成されている）<br>
③レジを打つ<br>
### 詳細仕様<br>
・マスターメンテ機能はpermission1以上<br>
・全ユーザーの初期パスワードは「1234」
・ユーザー名と所有権限一覧<br>
![image](https://github.com/koukou123456/Pos/assets/91433734/c934c327-e9a2-4d15-81a8-aae4fb10f374)
<br><br>

## 実装予定（だいたい優先度順）<br>
- 機能のメンテ<br>
 ↳ ・[消費税計算関数の修正](https://github.com/Ludens3562/POS_regi/issues/1)<br>
 ↳ ・分割したファイルの整理（例：insert.pyとcreate_HistoryDB.pyの統合）<br>
 ↳ ・import周りの整理<br>
 ↳ ・権限をグローバル変数に格納し、権限チェック時のメソッド呼び出しを廃止する<br>
 ↳ ・返品時のロギング
- 一括出荷　入荷システム<br>
## 実装済み機能
- ジャーナル機能<br>
- 返品機能<br>
- csv取り込み<br>
   ↳差分更新機能<br>
- 保留機能 → 画像解析からの商品カート代わりにも使えるような機能<br>
- 権限制御の充実<br>
- ジャーナル検索
<br>
### 便利機能
DBの中身見るならこれいれると便利になると思う<br>
```
名前: SQLite Viewer
ID: qwtel.sqlite-viewer
説明: SQLite Viewer for VSCode
バージョン: 0.3.13
パブリッシャー: Florian Klampfer
VS Marketplace リンク: https://marketplace.visualstudio.com/items?itemName=qwtel.sqlite-viewer
```
