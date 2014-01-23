#! /bin/bash
while read place
do
  sed -e "s|-place-|$place|g"  genDataHtml_Template.C > genDataHtml.C
  root -b genDataHtml.C
done < $1
exit 0

