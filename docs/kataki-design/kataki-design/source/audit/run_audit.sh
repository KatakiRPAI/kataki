set -e
cd "$(dirname "$0")"
python3 sky2.py >/dev/null && python3 scene3.py >/dev/null && cp out/Sky2-*.dc.html root/project/
B=$(ls root/project | grep -E '^(Sky2|Scene|Main)' | tr '\n' ' ')
node preview2.js audit $B
python3 audit.py $(echo $B | sed 's/\.dc\.html//g')
