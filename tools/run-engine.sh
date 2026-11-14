#!/bin/sh
# Keep engine data paths independent of the GUI's working directory.
cd -- "$(dirname -- "$0")/../bin" || exit 1
exec ./release "$@"
