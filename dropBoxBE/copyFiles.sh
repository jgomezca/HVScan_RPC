# How to copy the old dropBox files

ssh webcondvm

# Files since the 25th of August
DAYS=$(python -c 'import datetime; print (datetime.datetime.now() - datetime.datetime(2012, 8, 25)).days')
echo $DAYS

# find /DropBox_backend/ -type f -mtime -$DAYS -exec ls -l '{}' \;

find /DropBox_backend/ -type f -mtime -$DAYS -exec cp --preserve=all '{}' /afs/cern.ch/cms/DB/conddb/test/dropbox/replay/files/ \;

chmod -R ugo-w /afs/cern.ch/cms/DB/conddb/test/dropbox/replay/files
chmod -R o-rwx /afs/cern.ch/cms/DB/conddb/test/dropbox/replay/files
chmod g+rx /afs/cern.ch/cms/DB/conddb/test/dropbox/replay/files

# TODO: Negative ACLs?

