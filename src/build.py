name: Build data store

on:
  push:
    paths:
      - 'raw/**'
      - 'src/**'
  workflow_dispatch:

permissions:
  contents: write

# Uploading several batches in a row starts several runs at once. They all
# rebuild the whole store from raw/ and then all try to push data/ to main, so
# whichever arrives second is rejected as non-fast-forward and the run goes red.
# Only the LAST run matters -- build.py reads every file under raw/ from
# scratch, so a superseded run has nothing unique to contribute. Cancel it.
concurrency:
  group: build-data-store
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install pdftotext (for PDF stewards reports)
        run: sudo apt-get update && sudo apt-get install -y poppler-utils
      - name: Rebuild derived data
        run: python3 src/build.py
      - name: Commit if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add data
          if git diff --cached --quiet; then
            echo "data/ unchanged - nothing to commit"
            exit 0
          fi
          git commit -m "auto-rebuild data [skip ci]"
          # Even with the concurrency guard, a push can land between our
          # checkout and our push. Rebase onto whatever is on main and retry
          # rather than failing the whole run and leaving data/ stale.
          for attempt in 1 2 3 4 5; do
            if git push; then
              echo "pushed on attempt $attempt"
              exit 0
            fi
            echo "push rejected (attempt $attempt) - rebasing onto origin/main"
            git pull --rebase --autostash origin main || true
            sleep $((attempt * 5))
          done
          echo "::error::could not push data/ after 5 attempts"
          exit 1
