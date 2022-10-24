# BackupSnap
Very useful wrapper around --link-dest rsync parameter

## Parameters:

-s / --source

    Source directory.
    
-d / --dest

    Destination directory.

--logdir

    Log files directory. If this parameter is omitted, the destination directory (plus "Log") will be used.

-b / --block

    Name of the block file to use. It permits to execute multiple backups using the same folders.

-p / --perm

    Enable the backup of the permissions.

-v / --verbose

    Make the backup verbose.

--bandwidth

    Limit the maximum bandwith available for the backup (in KB/s).
    
--hour

    How many hourly backups to maintain.
    
--day

    How many daily backups to maintain.
    
--week

    How many weekly backups to maintain.
    
--month

    How many monthly backups to maintain.
    
--year

    How many yearly backups to maintain.
