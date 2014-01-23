#! /bin/bash
while read place
do
  ./genhtml.sh results/dataHtml${place}.txt
done < $1
exit 0

