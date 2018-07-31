#!/usr/bin/env bash
#file=`echo "$1"| sed s/\.ui/_win.ui/g`
#file2=`echo "$2"| sed s/\.ui/_win.ui/g`
#file3=`echo "$3"| sed s/\.ui/_win.ui/g`
#echo $file
#cp $1 $file
#echo $2 $file2
#cp $2 $file2
#cp $3 $file3
for arg in $@
do
    pyfile=`echo "$arg"| sed s/\.ui/\.py/g`
    pyuic5 $arg -o $pyfile
done
