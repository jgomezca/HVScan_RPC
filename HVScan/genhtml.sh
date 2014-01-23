#!/bin/bash
cat indexhead.html > $1.html
j=1
export lines=`cat $1 | wc -l`
if [[ $lines -eq "0" ]]
then
 echo No lines in $1 file
 exit 0
fi
until [[ $j -eq $lines+1 ]] 
    do 
    #echo $j
    export roll=`awk 'NR=='$j' {print $1}' $1`
    export wp=`awk 'NR=='$j' {print $2}' $1`
    export slope50=`awk 'NR=='$j' {print $3}' $1`
    export emax=`awk 'NR=='$j' {print $4}' $1`
    export hv50=`awk 'NR=='$j' {print $5}' $1`
    export chi2=`awk 'NR=='$j' {print $6}' $1`
    export clswp=`awk 'NR=='$j' {print $7}' $1`
    export effwp=`awk 'NR=='$j' {print $8}' $1`
    export wpDef=`awk 'NR=='$j' {print $9}' $1`
    export effWpDef=`awk 'NR=='$j' {print $10}' $1`
    export clsWpDef=`awk 'NR=='$j' {print $11}' $1`
    export hv50error=`awk 'NR=='$j' {print $12}' $1`


    cp indexLocal.html results/$roll/index.html
    sed -e "s|-roll-|$roll|g" -e "s|-wp-|$wp|g" -e "s|-slope50-|$slope50|g" -e "s|-emax-|$emax|g" -e "s|-hv50-|$hv50|g" -e "s|-chi2-|$chi2|g" -e "s|-clswp-|$clswp|g"  -e "s|-effwp-|$effwp|g" -e "s|-wpDef-|$wpDef|g" -e "s|-effWpDef-|$effWpDef|g" -e "s|-clsWpDef-|$clsWpDef|g" -e "s|-hv50error-|$hv50error|g"  indexline.html >> $1.html
    #echo $roll
    #echo $wp
    #echo $slope50
    #echo $emax
    #echo $hv50
    #echo $chi2
    #echo $clswp
    #echo $effwp
    #echo $wpDef
    #echo $effWpDef
    #echo $clsWpDef
    #echo $hv50error
   
    let "j=$j+1"
    done
cat indextail.html >> $1.html
exit 0
