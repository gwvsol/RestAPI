#!/bin/bash
remoteHost="api.hldns.ru:5000"
#remoteHost="https://api.hldns.ru"
url="api/v1.0"
user="api"
passwd="1245"
# Формируем JSON
id="1"
name="k1"
upSystem="16:38"
miner="eth"
upMiner="16:39"
Hash="Mh/s"
hashrate="105"
tgpu="67"
fgpu="90"
NGPU="6"
PGPU="138"

INFO=$(\
printf "{\n"
printf "\t\"method\": \"stats\",\n"
printf "\t\"jsonrpc\": \"2.0\",\n"
printf "\t\"id\": \"$id\",\n"
printf "\t\"name\": \"$name\",\n"
printf "\t\"sysuptime\": \"$upSystem\",\n"
printf "\t\"miner\": \"$miner\",\n"
printf "\t\"uptimeminer\": \"$upMiner\",\n"
printf "\t\"totalhashrate\": \"${hashrate}$Hash\",\n"
printf "\t\"maxtemp\": \"${tgpu}C\",\n"
printf "\t\"maxfan\": \"${fgpu}\",\n"
printf "\t\"totalgpu\": \"$NGPU\",\n"
printf "\t\"totalpower\": \"${PGPU}W\"\n"
printf "}\n")

echo $INFO
# Отправляем JSON на REST API сервер
#curl -s -u $user:$passwd -j --ssl -H "Content-Type: application/json" -X POST -d "$INFO" $remoteHost/$url
curl -v -u $user:$passwd -j -H "Content-Type: application/json" -X POST -d "$INFO" $remoteHost/$url
