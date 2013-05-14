#!/bin/bash

help()
{
cat <<EOF >&2
Usage: $0 [options] file

options: -l|--litecoin    get Litecoin addresses (default: Bitcoin)
	 -p|--private     include private keys
	 -c|--compressed  retrieve compressed addresses/keys
         -s|--start       start index (default: 1)
         -k|--count       number of addresses to generate (default: 10)
EOF
}

litecoin=""
compressed=""
getprivkey=0
start=1
count=10
OPTS=$(getopt -o phlcs:k: --long private,help,litecoin,compressed,start,count -- "$@")
eval set -- "$OPTS"
while true; do
  case "$1" in
    -l|--litecoin)    litecoin=" -l"; shift;;
    -c|--compressed)  compressed=" -c"; shift;;
    -p|--private)     getprivkey=1; shift;;
    -s|--start)       start=$2; shift 2;;
    -k|--count)       count=$2; shift 2;;
    -h|--help)        help; exit 1;;
    --)               shift; break;;
    *)                echo Internal error; exit 1;;
  esac
done

if [ $# != 1 ]
then
  help; exit 1
fi

if [ $getprivkey == 0 ]
then
  ./hex2wifaddr.py $litecoin $compressed $(for i in $(seq $start $(expr $start + $count - 1)); do (cat "$1" ; echo -n $i) | sha256sum | sed "s/ .*//"; done) | grep address | awk 'BEGIN {c='$start'} {print c++"\t"$2}'
else
  ./hex2wifaddr.py $litecoin $compressed $(for i in $(seq $start $(expr $start + $count - 1)); do (cat "$1" ; echo -n $i) | sha256sum | sed "s/ .*//"; done) | grep -v hexkey | awk 'BEGIN {c='$start'} {privkey=$2; getline; addr=$2; print c++"\t"addr"\t"privkey}'
fi
