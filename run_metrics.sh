#!/bin/sh

set -e

MODEL_NAME="${1:-"gpt-oss:20b"}"
INPUT_FILES="-i ./uploads/20251001-evaluator01-oskar.xlsx -i ./uploads/20251001-evaluator02-andrei-olar-2.xlsx -i ./uploads/20251001-evaluator03-andrei-olar.xlsx -i ./uploads/20251001-evaluator04-LauraD.xlsx"
TARGET_ATTRS="-t re1 -t re2 -t re3 -t ri1 -t ri2 -t c1 -t r1 -t r2"
for metric in mae rmse lin-ccc icc; do
  echo "running $metric on $MODEL_NAME"
  uv run metrics ${INPUT_FILES} ${TARGET_ATTRS} -k paper_no -o "./uploads/$(date +%Y%m%d)-${MODEL_NAME}.xlsx" $metric "./uploads/20251001-evaluator05-LLM-${MODEL_NAME}.xlsx"
done

echo done
