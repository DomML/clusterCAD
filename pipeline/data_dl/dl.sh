#!/bin/bash
mkdir mibig
mkdir antismash

if [ ! -f mibig_json_4.0.tar.gz ]; then
    wget https://dl.secondarymetabolites.org/mibig/mibig_json_4.0.tar.gz
    tar -xzf mibig_json_4.0.tar.gz | pv > /dev/null
fi

if [ ! -f mibig_gbk_4.0.tar.gz ]; then
    wget https://dl.secondarymetabolites.org/mibig/mibig_gbk_4.0.tar.gz
    tar -xzf mibig_gbk_4.0.tar.gz | pv > /dev/null
fi

for j in mibig_json_4.0/*json; do
    v=$(cat $j | jq '.version')
    b=$(basename $j | cut -d"." -f1)
    s=$(cat $j | jq '.status')
    
    echo -ne $b $s    "\r"

    if [ $s != "\"active\"" ]; then
        continue
    fi
    
    if [ ! -f mibig/$b/$b.json ]; then
        wget -q -P mibig https://mibig.secondarymetabolites.org/repository/$b.$v/$b.zip
        unzip -q mibig/$b.zip -d mibig/$b
        rm mibig/$b.zip
    fi
    
    if [ ! -f antismash/$b/$b.json ]; then
        wget -q -P antismash https://mibig.secondarymetabolites.org/repository/$b.$v/generated/$b.zip
        unzip -q antismash/$b.zip -d antismash/$b
        rm antismash/$b.zip
    fi
done
echo ""