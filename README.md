# BackupSnap
Very useful wrapper around --link-dest rsync parameter

## Parameters:

-s \<value\> / --source=\<value\>

    Source directory.
    
-d \<value\> / --dest=\<value\>

    Destination directory.

--logdir=\<value\>

    Log files directory. If this parameter is omitted, the destination directory (plus "Log") will be used.

-b \<value\> / --block=\<value\>

    Name of the block file to use. It permits to execute multiple backups using the same folders.

-p / --perm

    Enable the backup of the permissions.

-v / --verbose

    Make the backup verbose.

--bandwidth=\<number\>

    Limit the maximum bandwith available for the backup (in KB/s).
    
--hour=\<number\>

    How many hourly backups to maintain.
    
--day=\<number\>

    How many daily backups to maintain.
    
--week=\<number\>

    How many weekly backups to maintain.
    
--month=\<number\>

    How many monthly backups to maintain.
    
--year=\<number\>

    How many yearly backups to maintain.
