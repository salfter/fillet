#!/bin/bash

help()
{
cat <<EOF >&2
Usage: $0 [options] file num

options: -p|--private     retrieve private key (default: address)
	 -c|--compressed  retrieve compressed key/address
         -q|--qr          display QR code
EOF
}

getprivkey=0
showqrcode=0
compressed=""
litecoin=""
OPTS=$(getopt -o pqhlc --long private,qr,help,litecoin,compressed -- "$@")
eval set -- "$OPTS"
while true; do
  case "$1" in
    -l|--litecoin)    litecoin=" -l"; shift;;
    -c|--compressed)  compressed=" -c"; shift;;
    -p|--private)     getprivkey=1; shift;;
    -q|--qr)          showqrcode=1; shift;;
    -h|--help)        help; exit 1;;
    --)               shift; break;;
    *)                echo Internal error; exit 1;;
  esac
done

decoder="hex2wifaddr.py $litecoin $compressed"

if [ $# != 2 ]
then
  help; exit 1
fi

hexkey=$((cat wedding.jpg; echo -n 1) | sha256sum | sed "s/ .*//")

if [ $getprivkey == 1 ]
then
  out=$(python $decoder $hexkey | grep privkey | sed "s/.* //")
else
  out=$(python $decoder $hexkey | grep address | sed "s/.* //")
fi

if [ $showqrcode == 1 ]
then
  qrencode -l H -o - $out | display - &
fi

echo $out
