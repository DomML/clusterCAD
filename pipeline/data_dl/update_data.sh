echo -ne "Remove AS \r"
rm -rf ../data/antismash/raw/*
echo -ne "Copie  AS \r"
rsync -rp antismash/* ../data/antismash/raw/
echo -ne "Copie GBK \r"
cp -r ./mibig_gbk_4.0 ../data/mibig/raw
echo -ne "Copie MBG \r"
cp -r ./mibig_json_4.0 ../data/mibig/raw
echo -ne "          \r"