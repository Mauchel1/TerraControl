#!/bin/bash

#git area

cd terra

git add fuetterung.txt
git add haeutungen.txt
git add saeuberungen.txt
git add schlangendaten.txt

git commit -m "automatic commit - Update data"

git push

#website area

rsync fuetterung.txt mauchel1@hadar.uberspace.de:/var/www/virtual/mauchel1/html/terra/fuetterung.txt
rsync haeutungen.txt mauchel1@hadar.uberspace.de:/var/www/virtual/mauchel1/html/terra/haeutungen.txt
rsync saeuberungen.txt mauchel1@hadar.uberspace.de:/var/www/virtual/mauchel1/html/terra/saeuberungen.txt
rsync schlangendaten.txt mauchel1@hadar.uberspace.de:/var/www/virtual/mauchel1/html/terra/schlangendaten.txt
