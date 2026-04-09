name: Tu dong phan tich co phieu

on:
  schedule:
    - cron: '0 2 * * 1-5'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Lay code tu Github
        uses: actions/checkout@v3

      - name: Cai dat Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Cai dat thu vien
        run: |
          pip install yfinance matplotlib pandas

      - name: Chay file phan tich
        run: python analysis.py

      - name: Luu bieu do vao kho
        uses: actions/upload-artifact@v4
        with:
          name: bieu-do-ket-qua
          path: ket_qua.png
