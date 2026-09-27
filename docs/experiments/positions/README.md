# 解析局面定義

このディレクトリには、`tools/analyze_positions.py`へ渡す局面定義JSONを実験系統ごとに保存します。
各JSONは初期局面からのUSI指し手列、局面ID、必要に応じて強制探索する`searchmoves`を記録します。

- `historical/`: 本家米長玉の棋譜と現代化した本家系
- `original/`: 7筋構想などのオリジナル系
- `anti-fourth-file-rook/`: 初手6八飛に対する初期の対策解析
- `book/`: 専用定跡の候補選定に使う局面

解析結果の大きなJSONはGit管理外の`results/`に保存し、実験レポートからチェックサムで参照します。
