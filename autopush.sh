#!/bin/bash

cd terra

git add fuetterung.txt
git add haeutungen.txt
git add saeuberungen.txt
git add schlangendaten.txt

git commit -m "automatic commit - Update data"

git push
