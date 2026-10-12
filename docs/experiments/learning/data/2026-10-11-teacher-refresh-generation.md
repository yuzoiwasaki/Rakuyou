# 由来を固定した教師生成と監査：54局面・depth15

2026年10月11日、ハーネス基準 `2db6542`（開始時dirty=false）。
[探索0 dry-run](2026-10-11-teacher-refresh-dry-run.md)の後、固定対象54局面で
基準エンジンの教師探索を一度だけ実行した。全54探索が深さ15で完了し、全件をcp教師として
受け入れた。由来・コマンド・生ログ・符号・PV・保存ファイルの監査も通過した。
学習更新0、配備false。現行評価・定跡・25cp補正は維持する。

## 条件と実行

[計画](2026-10-11-teacher-refresh-plan.md)を維持し、実行用コピーの
`teacher_search_enabled` だけをtrueに変更した。追跡中の参照計画、学習／配備フラグは
変更しない。初回学習候補ではなく現在の基準paramsを使った。

- train36／validation18、各side/result層は6件／3件。対象補充・再選択なし。
- depth15／MultiPV1／Threads1／Hash64MB／ShinYonenagaGyoku ON／OwnBook OFF／Ponder OFF。
- 各局面で新規プロセス、ルート前の着手履歴を再生。最大54回、各30秒。
- runtime、対象JSONL、計画、probe、使用PythonツールのSHAを固定・記録。
  入力6ファイルを独立コピーして元／コピーの照合を行った。
- 実行マーカー `teacher-generation-attempt-v1.json` を排他的に作成。
  retry／resume／時間延長／深掘りは0。マーカーを解除せず、この実行を閉じる。

```sh
python3 tools/learning/data/refresh_teachers.py \
  results/learning-pilot/2026-10-11-teacher-refresh-preparation-v1/manifest.json \
  --plan results/learning-pilot/2026-10-11-teacher-refresh-run-v1-plan.json \
  --output results/learning-pilot/2026-10-11-teacher-refresh-run-v1 --run
```

この実行は終了済み。再実行はマーカーで拒否される。

## 生成結果

| 項目 | train | validation |
| --- | ---: | ---: |
| 完了／受入 | 36／36 | 18／18 |
| 除外／失敗 | 0／0 | 0／0 |
| 各side/result層の受入件数 | 6 | 3 |
| 上限draw由来（うち後手） | 12（6） | 6（3） |
| ルート手番側cpの範囲 | −1041〜1036 | −879〜606 |

cpは先手・後手ともルート手番側で、後手だけ符号を反転していない。
mate／bounds／特殊終端／known-win／PV内繰り返し／不合法PV／途中停止／timeout／
読み込み失敗はいずれも0。過去のcpは `archived_reference` として分離して保持した。
勝敗損失は全54件OFFで、上限drawを勝ちや正式drawに置き換えていない。

生成区間は10:36:49〜10:37:29 UTC（約40秒）。検索区間elapsed合計21.808秒、最大1.969秒。
検索時間はプロセス起動・データ読込・検証時間を含まず、速度改善の指標にはしない。
`teacher_generation_complete=true`、`training_ready=false`、更新0、配備false、test選択0。

## 独立した監査

`tools/learning/data/audit_refreshed_teachers.py` を追加。教師探索を行わず、次を保存済み結果から照合する。

- 完了した生成reportと対象54件の完全な対応、重複なし、pendingの元棋譜／root／split情報不変。
- 参照計画と実行コピーの差が探索フラグだけであること、入力の元／コピーSHA一致。
- reportのruntime・設定・probe情報と実際の固定binding、運用6件・baseline7件のSHA一致。
- 1プロセスの送信列が固定オプション・同じ着手列・`go depth 15` 1回・quitであること。
- readyok・bestmoveと保存analysisの一致、生USI infoを再解析したcp・depth・PV等の一致。
- Native replayによるルートSFEN／Huffman／手番、全PVの合法性、繰り返し履歴の確認。
- cp符号・受入／除外理由、JSONLとreportの行の完全一致、各出力SHA・集計件数の一致。

最終監査 `audit-v2.json` は54ルート＋PVを再生して全件通過。
最初の `audit-v1.json` に加え、reportヘッダーのruntime／設定／probeと教師originの照合を
追加した監査を保存した。旧監査を上書きせず、再監査にも探索は含まれない。

```sh
python3 tools/learning/data/audit_refreshed_teachers.py \
  results/learning-pilot/2026-10-11-teacher-refresh-run-v1/report.json \
  --output results/learning-pilot/2026-10-11-teacher-refresh-run-v1/audit-v2.json
```

新規5テストが通過。後手のcp符号、変更したコマンド／元情報、改変された生ログ／解析値、
不合法PV／手番不一致、繰り返しを受入れないことを確認した。

## 保存状態と判断

成果物は `results/learning-pilot/2026-10-11-teacher-refresh-run-v1/` に保持する。

| 成果物 | SHA-256 |
| --- | --- |
| `report.json` | `5b35823223c099a4233c4d4e9c99b11876fd291d14a92b9caa945c3941eb97cf` |
| `audit-v2.json` | `de27d343a78ef62a0571b12410c14567b39e461a18191f38cc546be539d4cdd4` |
| `train.teachers.jsonl` | `d6cee53a5ab79355979c5a8da50b25c9b5b1796d545ceb3b94a858768e1c7809` |
| `validation.teachers.jsonl` | `07841aa7c9707c9d7bbbad499a2bbaff038f29109b55bda827051a696b93a45f` |
| 実行用計画コピー | `28ac58f074d208f2bb8a7aed6cc178b7754b6e678dce900dbd9948ea572eadba` |
| `tools/learning/data/audit_refreshed_teachers.py` | `5d5e94700ece005881c16f21a77a7ea6aec8131aaa03594e1ff9245bdd856b50` |

生成＋監査のまとまりを完了した。この54件の新教師については現在のruntime由来を確認できた。
過去の教師全体の歴史的params同一性が証明されたわけではない。
ハーネスのgit revisionと通常releaseのビルド由来も区別し、バイナリの同一性は保存SHAで扱う。
同一基準による自己蒸留の限界、長い共通手順の相関、validation再利用、上限drawの
正式裁定がない点は残る。教師の由来確認だけで棋力や引き分け確保能力の改善とはしない。
外部バックアップは未実施。testの未使用224件は維持している。

次は新教師を読む専用の入力接続と、train36／validation18の基準静止探索末端の準備、
既存更新器につなぐ探索・更新0のdry-runを一まとまりで検証する。
既存JSONLや旧教師を上書きして取り込まず、今回の生成report／監査と新しい入力をSHAで結ぶ。
新教師を使う再学習の条件はその検証後に定め、今回は勾配更新・候補選択・配備に進まない。
