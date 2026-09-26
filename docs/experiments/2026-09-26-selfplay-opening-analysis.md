# 新米長玉 自己対局序盤分析

## 対象データ

| データ | 局数 | 新米長玉の成績 | スコア率 |
|---|---:|---:|---:|
| `shin-book-off-vs-normal-depth15-100games` | 100 | 25勝56敗19分 | 34.5% |
| `shin-book-on-vs-normal-depth15-100games` | 100 | 32勝56敗12分 | 38.0% |
| 合計 | 200 | 57勝112敗31分 | 36.2% |

## 先後別

| 新米長玉の手番 | 局数 | 勝 | 敗 | 分 | スコア率 |
|---|---:|---:|---:|---:|---:|
| 先手 | 100 | 36 | 47 | 17 | 44.5% |
| 後手 | 100 | 21 | 65 | 14 | 28.0% |

## 頻出する序盤手順

指し手はUSI形式。スコア率は、その手順が現れた対局における新米長玉の値。
局数が少ない枝は強さの根拠にせず、深く読む候補の選別に使う。

### 4手目まで

| 局数 | スコア率 | 手順 |
|---:|---:|---|
| 55 | 33.6% | `7g7f 5a6b 2h6h 1c1d` |
| 51 | 43.1% | `5i4h 3c3d 7g7f 7a6b` |
| 28 | 48.2% | `5i4h 3c3d 7g7f 8b4b` |
| 18 | 19.4% | `7g7f 5a6b 2h6h 5c5d` |
| 13 | 19.2% | `7g7f 5a6b 2h6h 8c8d` |
| 12 | 29.2% | `7g7f 5a6b 2h6h 7a7b` |
| 8 | 50.0% | `5i4h 3c3d 2g2f 2b3c` |
| 8 | 50.0% | `5i4h 3c3d 2g2f 4a3b` |
| 3 | 0.0% | `5i4h 3c3d 2g2f 3a3b` |

### 6手目まで

| 局数 | スコア率 | 手順 |
|---:|---:|---|
| 28 | 44.6% | `5i4h 3c3d 7g7f 7a6b 2g2f 6c6d` |
| 16 | 21.9% | `7g7f 5a6b 2h6h 5c5d 3i3h 3a4b` |
| 11 | 22.7% | `7g7f 5a6b 2h6h 1c1d 5i4h 1d1e` |
| 9 | 50.0% | `5i4h 3c3d 7g7f 7a6b 2g2f 4a3b` |
| 9 | 55.6% | `5i4h 3c3d 7g7f 8b4b 9g9f 4c4d` |
| 8 | 18.8% | `7g7f 5a6b 2h6h 8c8d 5i4h 1c1d` |
| 7 | 35.7% | `5i4h 3c3d 7g7f 7a6b 2g2f 8c8d` |
| 7 | 35.7% | `7g7f 5a6b 2h6h 1c1d 6g6f 1d1e` |
| 7 | 7.1% | `7g7f 5a6b 2h6h 1c1d 6g6f 7a7b` |
| 6 | 41.7% | `7g7f 5a6b 2h6h 7a7b 5i4h 1c1d` |

### 8手目まで

| 局数 | スコア率 | 手順 |
|---:|---:|---|
| 11 | 40.9% | `5i4h 3c3d 7g7f 7a6b 2g2f 6c6d 2f2e 6b6c` |
| 9 | 44.4% | `5i4h 3c3d 7g7f 7a6b 2g2f 6c6d 6i7h 4c4d` |
| 9 | 16.7% | `7g7f 5a6b 2h6h 5c5d 3i3h 3a4b 5i4h 4b5c` |
| 7 | 35.7% | `5i4h 3c3d 7g7f 7a6b 2g2f 8c8d 6i7h 4c4d` |
| 7 | 21.4% | `7g7f 5a6b 2h6h 1c1d 5i4h 1d1e 6g6f 7a7b` |
| 5 | 30.0% | `5i4h 3c3d 7g7f 7a6b 2g2f 4a3b 6i7h 4c4d` |
| 4 | 75.0% | `5i4h 3c3d 7g7f 7a6b 2g2f 6c6d 2f2e 2b8h+` |
| 4 | 25.0% | `5i4h 3c3d 7g7f 7a6b 2g2f 6c6d 4g4f 6b6c` |
| 4 | 50.0% | `5i4h 3c3d 7g7f 8b4b 9g9f 4c4d 9f9e 5a6b` |
| 3 | 66.7% | `5i4h 3c3d 7g7f 8b4b 9g9f 4c4d 9f9e 3a3b` |

### 10手目まで

| 局数 | スコア率 | 手順 |
|---:|---:|---|
| 6 | 8.3% | `7g7f 5a6b 2h6h 5c5d 3i3h 3a4b 5i4h 4b5c 4h3i 1c1d` |
| 5 | 40.0% | `5i4h 3c3d 7g7f 7a6b 2g2f 6c6d 2f2e 6b6c 3i3h 4a3b` |
| 4 | 37.5% | `5i4h 3c3d 7g7f 7a6b 2g2f 6c6d 6i7h 4c4d 7i6h 6b6c` |
| 4 | 37.5% | `7g7f 5a6b 2h6h 1c1d 5i4h 1d1e 6g6f 7a7b 7i7h 6b7a` |
| 3 | 66.7% | `5i4h 3c3d 7g7f 7a6b 2g2f 6c6d 2f2e 2b8h+ 7i8h 6b6c` |
| 3 | 50.0% | `5i4h 3c3d 7g7f 7a6b 2g2f 6c6d 6i7h 4c4d 3i3h 6b6c` |
| 3 | 33.3% | `7g7f 5a6b 2h6h 5c5d 3i3h 3a4b 5i4h 4b5c 4h3i 7a7b` |

## 新米長玉側から見た序盤の評価低下候補

新米長玉エンジンが指す直前の評価値を、同じエンジンによる2手後の評価値と比較する。
間には新米長玉の着手と相手の応手が一つずつ含まれるため、どちらが原因かはこの表だけでは
確定できない。深い再解析を行う局面候補として扱う。mate評価は除外する。

| 低下 | 評価値 | 手数 | 指し手 | 結果 | 対局 |
|---:|---:|---:|---|---:|---|
| -287 | -137 → -424 | 32 → 34 | `4b5a 8f8e 8d8e` | 勝 | shin-book-on-vs-normal-depth15-100games: pair 28 / game 2 |
| -270 | +102 → -168 | 23 → 25 | `6f6e 2b7g+ 8i7g` | 負 | shin-book-on-vs-normal-depth15-100games: pair 23 / game 1 |
| -266 | -354 → -620 | 35 → 37 | `7i6h 4e8i 8e8d` | 負 | shin-book-off-vs-normal-depth15-100games: pair 10 / game 1 |
| -254 | +18 → -236 | 35 → 37 | `P*8b P*2h 8b8a+` | 負 | shin-book-off-vs-normal-depth15-100games: pair 48 / game 1 |
| -238 | -142 → -380 | 38 → 40 | `6a7b 8e7c+ 8a7c` | 負 | shin-book-off-vs-normal-depth15-100games: pair 9 / game 2 |
| -228 | -233 → -461 | 22 → 24 | `3a4b 7f7e 5c5d` | 負 | shin-book-off-vs-normal-depth15-100games: pair 23 / game 2 |
| -225 | -168 → -393 | 36 → 38 | `4d9i+ L*8d 8b9b` | 負 | shin-book-off-vs-normal-depth15-100games: pair 12 / game 2 |
| -221 | -218 → -439 | 28 → 30 | `2b3a 6h6f 3a1c` | 分 | shin-book-off-vs-normal-depth15-100games: pair 49 / game 2 |
| -202 | -370 → -572 | 38 → 40 | `B*3c 2b3c+ 2a3c` | 負 | shin-book-off-vs-normal-depth15-100games: pair 13 / game 2 |
| -196 | -29 → -225 | 30 → 32 | `4b5c 3i3h 7c7d` | 負 | shin-book-off-vs-normal-depth15-100games: pair 21 / game 2 |
| -196 | -142 → -338 | 33 → 35 | `7h6h 6g6h 6i6h` | 負 | shin-book-on-vs-normal-depth15-100games: pair 23 / game 1 |
| -183 | -322 → -505 | 37 → 39 | `2d2i 8f8b 5e6f` | 負 | shin-book-on-vs-normal-depth15-100games: pair 25 / game 1 |
| -179 | +75 → -104 | 31 → 33 | `7g5i 6a6b 3i2h` | 勝 | shin-book-off-vs-normal-depth15-100games: pair 39 / game 1 |
| -179 | +88 → -91 | 9 → 11 | `8h7g 5c5d 2h8h` | 負 | shin-book-off-vs-normal-depth15-100games: pair 41 / game 1 |
| -177 | +55 → -122 | 27 → 29 | `B*5e 4f4c 8e8d` | 負 | shin-book-on-vs-normal-depth15-100games: pair 5 / game 1 |
| -177 | +8 → -169 | 34 → 36 | `2a3c 4e4d 8b8c` | 負 | shin-book-on-vs-normal-depth15-100games: pair 11 / game 2 |
| -173 | +7 → -166 | 17 → 19 | `3g3f 4d4e 2i3g` | 負 | shin-book-off-vs-normal-depth15-100games: pair 20 / game 1 |
| -172 | -128 → -300 | 11 → 13 | `8h2b+ 3a2b 7f7e` | 負 | shin-book-on-vs-normal-depth15-100games: pair 2 / game 1 |
| -172 | -150 → -322 | 35 → 37 | `B*5e P*2c 2d2i` | 負 | shin-book-on-vs-normal-depth15-100games: pair 25 / game 1 |
| -171 | +84 → -87 | 37 → 39 | `B*7g 4b3b 4f4e` | 負 | shin-book-off-vs-normal-depth15-100games: pair 5 / game 1 |

## 短手数の参照対局

内容の良し悪しを示す選定ではない。詳細確認を始めるための小さな候補集合。

| 新米長玉の手番 | 結果 | 手数 | 対局 |
|---|---:|---:|---|
| 先手 | 勝 | 101 | shin-book-off-vs-normal-depth15-100games: pair 29 / game 1 |
| 先手 | 負 | 76 | shin-book-off-vs-normal-depth15-100games: pair 48 / game 1 |
| 後手 | 勝 | 114 | shin-book-on-vs-normal-depth15-100games: pair 23 / game 2 |
| 後手 | 負 | 91 | shin-book-on-vs-normal-depth15-100games: pair 6 / game 2 |

## 初期所見

- 200局合算のスコア率は、先手44.5%に対して後手28.0%だった。専用定跡の
  最初の対象は、成績差が大きい後手の初手`5a6b`側を優先する。
- 後手では全100局が`7g7f 5a6b 2h6h`から始まった。4手目が`5c5d`の18局は
  19.4%、`8c8d`の13局は19.2%で、深い再解析の候補になる。
- `7g7f 5a6b 2h6h 5c5d 3i3h 3a4b 5i4h 4b5c 4h3i 1c1d`まで一致した
  6局は8.3%だった。標本が小さいため悪い手順とは断定せず、分岐前後の候補手を
  MultiPVで比較する。
- 評価低下表は浅い探索で見つけた調査対象であり、指し手の採否には使わない。
  まず代表的な勝敗を盤面として確認し、その後に重要局面だけ深く再解析する。
