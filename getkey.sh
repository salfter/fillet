#!/bin/bash

help()
{
cat <<EOF >&2
Usage: $0 [options] file num

options: -p|--private  retrieve private key (default: address)
         -q|--qr       display QR code
EOF
}

getprivkey=0
showqrcode=0
OPTS=$(getopt -o pqh --long private,qr,help -- "$@")
eval set -- "$OPTS"
while true; do
  case "$1" in
    -p|--private) getprivkey=1; shift;;
    -q|--qr)      showqrcode=1; shift;;
    -h|--help)    help; exit 1;;
    --)           shift; break;;
    *)            echo Internal error; exit 1;;
  esac
done

if [ $# != 2 ]
then
  help; exit 1
fi

hexkey=$(python fillet.py --file "$1" --keynumber "$2" --size 1 | sed "s/.*: //")

if [ $getprivkey == 1 ]
then
  out=$(python hex2wifaddr.py $hexkey | grep privkey | sed "s/.* //")
else
  out=$(python hex2wifaddr.py $hexkey | grep address | sed "s/.* //")
fi

if [ $showqrcode == 1 ]
then
  qrencode -l H -o - $out | display &
fi

echo $out
