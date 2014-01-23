#! /bin/bash    
CONT=1                                                                                                                                                                               
while [ $CONT -lt 10 ]
do
wget http://test-carrillo.web.cern.ch/test-carrillo/rpc/hvscan/hvscan2012II/p$CONT/rollYeff.txt 
mv rollYeff.txt rollYeff_$CONT.txt
CONT=$[$CONT+1]
done
exit 0

