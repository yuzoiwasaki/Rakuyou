#!/usr/bin/env python3

"""Summarize Rakuyou paired self-play opening data as Markdown."""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_games(paths):
    games = []
    for path in paths:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
        for game in data["games"]:
            games.append((path.stem, game))
    return games


def shin_color(game):
    return "black" if game["black"] == "shin_yonenaga" else "white"


def shin_score(game):
    if game["result"] == "draw":
        return 0.5
    winner = game["black"] if game["result"] == "black_win" else game["white"]
    return 1.0 if winner == "shin_yonenaga" else 0.0


def result_name(score):
    return {0.0: "負", 0.5: "分", 1.0: "勝"}[score]


def game_id(dataset, game):
    return f"{dataset}: pair {game['pair']} / game {game['game_in_pair']}"


def format_rate(scores):
    return f"{sum(scores) / len(scores):.1%}" if scores else "-"


def append_overview(lines, games):
    lines.extend(["## 対象データ", ""])
    by_dataset = defaultdict(list)
    for dataset, game in games:
        by_dataset[dataset].append(game)
    lines.extend([
        "| データ | 局数 | 新米長玉の成績 | スコア率 |",
        "|---|---:|---:|---:|",
    ])
    for dataset, dataset_games in sorted(by_dataset.items()):
        scores = [shin_score(game) for game in dataset_games]
        wins = scores.count(1.0)
        losses = scores.count(0.0)
        draws = scores.count(0.5)
        lines.append(
            f"| `{dataset}` | {len(scores)} | {wins}勝{losses}敗{draws}分 | "
            f"{format_rate(scores)} |"
        )
    scores = [shin_score(game) for _, game in games]
    lines.append(
        f"| 合計 | {len(scores)} | {scores.count(1.0)}勝{scores.count(0.0)}敗"
        f"{scores.count(0.5)}分 | {format_rate(scores)} |"
    )
    lines.append("")

    lines.extend([
        "## 先後別", "",
        "| 新米長玉の手番 | 局数 | 勝 | 敗 | 分 | スコア率 |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for color, label in (("black", "先手"), ("white", "後手")):
        scores = [shin_score(game) for _, game in games if shin_color(game) == color]
        lines.append(
            f"| {label} | {len(scores)} | {scores.count(1.0)} | "
            f"{scores.count(0.0)} | {scores.count(0.5)} | {format_rate(scores)} |"
        )
    lines.append("")


def append_opening_branches(lines, games, prefix_plies, minimum, limit):
    lines.extend([
        "## 頻出する序盤手順", "",
        "指し手はUSI形式。スコア率は、その手順が現れた対局における新米長玉の値。",
        "局数が少ない枝は強さの根拠にせず、深く読む候補の選別に使う。", "",
    ])
    for plies in prefix_plies:
        branches = defaultdict(list)
        for _, game in games:
            if len(game["moves"]) >= plies:
                branches[tuple(game["moves"][:plies])].append(shin_score(game))
        selected = [item for item in branches.items() if len(item[1]) >= minimum]
        selected.sort(key=lambda item: (-len(item[1]), item[0]))
        lines.extend([
            f"### {plies}手目まで", "",
            "| 局数 | スコア率 | 手順 |",
            "|---:|---:|---|",
        ])
        for moves, scores in selected[:limit]:
            lines.append(f"| {len(scores)} | {format_rate(scores)} | `{' '.join(moves)}` |")
        if not selected:
            lines.append("| - | - | 該当なし |")
        lines.append("")


def evaluation_drops(games, maximum_ply):
    drops = []
    for dataset, game in games:
        previous = None
        for record in game["records"]:
            if record["player"] != "shin_yonenaga" or record["ply"] > maximum_ply:
                continue
            analysis = record.get("analysis")
            if not analysis or analysis.get("score_type") != "cp":
                continue
            try:
                score = int(analysis["score"])
            except (TypeError, ValueError):
                continue
            if previous is not None:
                previous_ply, previous_score = previous
                drops.append({
                    "change": score - previous_score,
                    "before": previous_score,
                    "after": score,
                    "from_ply": previous_ply,
                    "to_ply": record["ply"],
                    "moves": game["moves"][previous_ply - 1:record["ply"]],
                    "dataset": dataset,
                    "game": game,
                })
            previous = (record["ply"], score)
    return sorted(drops, key=lambda item: item["change"])


def append_evaluation_drops(lines, games, maximum_ply, limit):
    lines.extend([
        "## 新米長玉側から見た序盤の評価低下候補", "",
        "新米長玉エンジンが指す直前の評価値を、同じエンジンによる2手後の評価値と比較する。",
        "間には新米長玉の着手と相手の応手が一つずつ含まれるため、どちらが原因かはこの表だけでは",
        "確定できない。深い再解析を行う局面候補として扱う。mate評価は除外する。", "",
        "| 低下 | 評価値 | 手数 | 指し手 | 結果 | 対局 |",
        "|---:|---:|---:|---|---:|---|",
    ])
    for drop in evaluation_drops(games, maximum_ply)[:limit]:
        game = drop["game"]
        lines.append(
            f"| {drop['change']:+d} | {drop['before']:+d} → {drop['after']:+d} | "
            f"{drop['from_ply']} → {drop['to_ply']} | `{' '.join(drop['moves'])}` | "
            f"{result_name(shin_score(game))} | {game_id(drop['dataset'], game)} |"
        )
    lines.append("")


def append_representative_games(lines, games):
    lines.extend([
        "## 短手数の参照対局", "",
        "内容の良し悪しを示す選定ではない。詳細確認を始めるための小さな候補集合。", "",
        "| 新米長玉の手番 | 結果 | 手数 | 対局 |",
        "|---|---:|---:|---|",
    ])
    for color, color_label in (("black", "先手"), ("white", "後手")):
        for target, result_label in ((1.0, "勝"), (0.0, "負")):
            candidates = [
                (len(game["moves"]), dataset, game)
                for dataset, game in games
                if shin_color(game) == color and shin_score(game) == target
            ]
            if candidates:
                plies, dataset, game = min(candidates, key=lambda item: item[0])
                lines.append(
                    f"| {color_label} | {result_label} | {plies} | {game_id(dataset, game)} |"
                )
    lines.append("")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="paired self-play JSON files")
    parser.add_argument("--output", type=Path, help="write Markdown to this file")
    parser.add_argument("--prefix-plies", default="4,6,8,10",
                        help="comma-separated opening prefix lengths")
    parser.add_argument("--min-frequency", type=int, default=3)
    parser.add_argument("--branch-limit", type=int, default=10)
    parser.add_argument("--analysis-plies", type=int, default=40)
    parser.add_argument("--drop-limit", type=int, default=20)
    return parser.parse_args()


def main():
    args = parse_args()
    games = load_games(args.inputs)
    prefix_plies = [int(value) for value in args.prefix_plies.split(",")]
    lines = ["# 新米長玉 自己対局序盤分析", ""]
    append_overview(lines, games)
    append_opening_branches(
        lines, games, prefix_plies, args.min_frequency, args.branch_limit
    )
    append_evaluation_drops(lines, games, args.analysis_plies, args.drop_limit)
    append_representative_games(lines, games)
    output = "\n".join(lines) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
