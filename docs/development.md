# Apple Silicon Mac での開発手順

技巧は SSE 4.2 前提のため、Apple Silicon では x86_64 (Rosetta) でビルドします。
初回のみ OpenMP ランタイムのビルドが必要です（cmake が必要です: `brew install cmake`）。

```sh
cd Rakuyou
make libomp-x86_64   # 初回のみ
make release
```

実行ファイルは `bin/release` です。将棋所等で使う場合は、
[Releases](https://github.com/gikou-official/Gikou/releases) の Windows 版 zip から
`params.bin` 等のデータファイルを `bin/` にコピーしてください（`gikou.exe` は不要）。
