#!/usr/bin/python

#Mirko Sacripanti - mirko@nextware.it - +39.3355899896
import datetime
import getopt
import os
import fnmatch
import platform
import subprocess
import shutil
import sys

#import time
VERSION = "2003.27.5.17"
SCRIPTNAME = os.path.basename(__file__)
WINDOWS = platform.system() == 'Windows'
DATETIMESUFFIX = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

_Source = ""
_Dest = ""
_Block = ""
_Perm = False
_Verbose = False
_Bandwidth = 0
_Hour = 0
_Day = 0
_Week = 0
_Month = 0
_Year = 0

_FileLock = None
_FileLockName = ""
_FileLog = ""
_FileLogRsync = ""
_FileLogRsyncOut = ""
_FileStatus = ""
_Status = []

def main(argv):
    global _Source
    global _Dest
    global _Block
    global _Perm
    global _Verbose
    global _Bandwidth
    global _Hour
    global _Day
    global _Week
    global _Month
    global _Year

    global _FileLog
    global _FileLogRsync
    global _FileLogRsyncOut
    global _FileStatus
    global _Status

    print(SCRIPTNAME + ' ' + VERSION + ' ' + platform.system())

    try:
        opts, args = getopt.getopt(argv, "s:d:b:pv", ["source=", "dest=", "block=", "perm", "verbose", "bandwidth=", "hour=", "day=", "week=", "month=", "year="])
    except getopt.GetoptError:
        Help()
        sys.exit()

    for opt, arg in opts:
        if opt in ("-s", "--source"):
            _Source = arg
        elif opt in ("-d", "--dest"):
            _Dest = arg
        elif opt in ("-b", "--block"):
            _Block = arg
        elif opt in ("-p", "--perm"):
            _Perm = True
        elif opt in ("-v", "--verbose"):
            _Verbose = True
        elif opt in ("--bandwidth"):
            _Bandwidth = int(arg)
        elif opt in ("--hour"):
            _Hour = int(arg)
        elif opt in ("--day"):
            _Day = int(arg)
        elif opt in ("--week"):
            _Week = int(arg)
        elif opt in ("--month"):
            _Month = int(arg)
        elif opt in ("--year"):
            _Year = int(arg)

    if _Source == "" or _Dest == "" or _Block == "":
        Help()
        sys.exit()

    _FileStatus = os.path.realpath(__file__) + ".ultimo." + _Block
    _FileLog = os.path.join(_Dest, "Log", _Block + "." + DATETIMESUFFIX + ".log")
    _FileLogRsync = os.path.join(_Dest, "Log", _Block + "." + DATETIMESUFFIX + ".log.rsync")
    _FileLogRsyncOut = os.path.join(_Dest, "Log", _Block + "." + DATETIMESUFFIX + ".log.out.rsync")

    if not os.path.exists(_Dest):
        Log(_Dest + " non esiste", noFile=True, saveStatus=True)
        sys.exit()

    if not os.path.exists(os.path.join(_Dest, "Log")):
        try:
            os.makedirs(os.path.join(_Dest, "Log"))
        except:
            Log("Errore creazione cartella Log: " + PrintException("Log", [os.path.join(_Dest, "Log")]), noFile=True, saveStatus=True)
            sys.exit()

    PrintDiskSpace()

    if not OnlyOneInstanceBegin():
        Log("Backup gia' attivo")
        sys.exit()

    if os.path.isdir(_Source):
        Log(_Source + " pronta per il backup")
    else:
        Log(_Source + " vuota", saveStatus=True)
        sys.exit()

    if not os.path.exists(os.path.join(_Dest, "Corrente")):
        try:
            os.makedirs(os.path.join(_Dest, "Corrente"))
        except:
            Log("Errore creazione cartella Corrente: " + PrintException("Corrente", [os.path.join(_Dest, "Corrente")]), saveStatus=True)
            sys.exit()

    Log("File di log: " + _FileLog)
    Log("File di log rsync: " + _FileLogRsync)
    Log("File di log rsync out: " + _FileLogRsyncOut)

    SaveStatus("Inizio")

    Excluded = os.path.realpath(__file__) + ".escludi." + _Block
    if not os.path.exists(Excluded):
        f = open(Excluded, "w")
        f.close()

    print("-----------------------------------------")
    print("Parametri:")
    print("Source: " + _Source)
    print("Dest: " + _Dest)
    print("Block: " + _Block)
    print("Perm: " + str(_Perm))
    print("Verbose: " + str(_Verbose))
    print("Bandwidth: " + str(_Bandwidth))
    print("Hour: " + str(_Hour))
    print("Day: " + str(_Day))
    print("Week: " + str(_Week))
    print("Month: " + str(_Month))
    print("Year: " + str(_Year))
    print("-----------------------------------------")

    RsyncParam = ['nice', '-n 19']

    if not WINDOWS:
        RsyncParam.append('ionice')
        RsyncParam.append('-c3')

    RsyncParam.append('rsync')
    RsyncParam.append('-ah')

    if _Verbose:
        RsyncParam.append('-vP')

    RsyncParam.append('--stats')
    RsyncParam.append('--delete')
    RsyncParam.append('--delete-excluded')
    RsyncParam.append("--exclude-from='" + GetPath(Excluded) + "'")

    if not _Perm:
        RsyncParam.append('--chmod=777')
        RsyncParam.append('--no-A')
        RsyncParam.append('--no-X')
        RsyncParam.append('--no-o')
        RsyncParam.append('--no-g')

    if _Bandwidth > 0:
        RsyncParam.append('--bwlimit=' + str(_Bandwidth))

    RsyncParam.append("--log-file='" + GetPath(_FileLogRsync) + "'")

    Dest00 = ""
    if _Hour > 0:
        Dest00 = fnmatch.filter(os.listdir(_Dest), 'Ora.00*')
    elif _Day > 0:
        Dest00 = fnmatch.filter(os.listdir(_Dest), 'Giorno.00*')
    elif _Week > 0:
        Dest00 = fnmatch.filter(os.listdir(_Dest), 'Sett.00*')
    elif _Month > 0:
        Dest00 = fnmatch.filter(os.listdir(_Dest), 'Mese.00*')
    elif _Year > 0:
        Dest00 = fnmatch.filter(os.listdir(_Dest), 'Anno.00*')
    if Dest00 is not None and len(Dest00) > 0:
        Dest00.sort()
        Dest00 = Dest00[0]
        RsyncParam.append("--link-dest='" + GetPath(os.path.join(_Dest, Dest00)) + "'")
        if _Verbose:
            print("Precedente: " + Dest00)

    RsyncParam.append("'" + GetPath(_Source) + "'")
    RsyncParam.append("'" + GetPath(os.path.join(_Dest, "Corrente")) + "'")

    RsyncComplete = False
    RsyncIn = " ".join(RsyncParam)
    RsyncOut = ""

    if _Verbose:
        print("Comando: " + os.linesep + RsyncIn)

    try:
        """RsyncOut = subprocess.check_output(RsyncIn, shell=True, stderr=subprocess.STDOUT).decode(sys.getfilesystemencoding())""" #Diff 2-3
        RsyncOut = subprocess.check_output(RsyncIn, shell=True, stderr=subprocess.STDOUT).decode("utf8") #Diff 2-3
    except subprocess.CalledProcessError as e:
        RsyncComplete = e.returncode == 0 or e.returncode == 23 or e.returncode == 24
        if not RsyncComplete:
            _Status.append("Rsync return code: " + e.returncode)
            Log("Errore Rsync: " + PrintException("", [e.returncode, RsyncOut, RsyncIn]))
    else:
        RsyncComplete = True

    print("Esecuzione: " + os.linesep + RsyncOut)
    f = open(_FileLogRsyncOut, "w")
    f.write(RsyncOut)
    f.write(os.linesep)
    f.close()

    if RsyncComplete:
        SaveStatus("Rsync")
        if UpdatePeriods():
            SaveStatus("Fine")
        else:
            SaveStatus("Errore periodi")
    else:
        Log("Sincronizzazione non riuscita")
        SaveStatus("Errore Rsync")

    PrintDiskSpace()

    OnlyOneInstanceEnd()

def Help():
    print(SCRIPTNAME + ' -s/--source=<source> -d/--dest=<destination> -b/--block=<block name> [-p/--perm] [-v/--verbose] i --bandwidth=<bandwidth> --hour=<hour> --day=<day> --month=<month> --year=<year>')
    print("Deploy: wget http://nextware.it/BackupSnap[2|3].py.gz -OBackupSnap.py.gz && gunzip BackupSnap.py.gz -f && chmod u+x BackupSnap.py && ./BackupSnap.py")

def GetPath(path):
    if path == "":
        return ""
    else:
        if WINDOWS:
            """return subprocess.check_output(["cygpath", "-u", "-a", path]).decode(sys.getfilesystemencoding()).strip("\n")""" #Diff 2-3
            return subprocess.check_output(["cygpath", "-u", "-a", path]).decode("utf8").strip("\n") #Diff 2-3

        else:
            return path

def DateTimeLog():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def Log(text, noFile=False, saveStatus=False):
    TestoLog = "---> " + DateTimeLog() + " " + text
    """print(TestoLog.decode(sys.getfilesystemencoding()))""" #Diff 2-3
    print(TestoLog) #Diff 2-3

    if not noFile:
        f = open(_FileLog, "a+")
        f.write(TestoLog)
        f.write(os.linesep)
        f.close()

def SaveStatus(text):
    f = open(_FileStatus, "w")
    f.write(DateTimeLog() + " " + _Dest + " " + _Block + " " + DATETIMESUFFIX + " " + text + os.linesep)
    for S in _Status:
        f.write(DateTimeLog() + " " + S + os.linesep)
    f.close()

def OnlyOneInstanceBegin():
    global _FileLock
    global _FileLockName

    _FileLockName = os.path.realpath(__file__) + ".lock." + _Block

    Log("Verifica esecuzione singola: " + _FileLockName)

    if WINDOWS:
        try:
            if os.path.exists(_FileLockName):
                os.unlink(_FileLockName)
            _FileLock = os.open(_FileLockName, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except:
            Log("Errore esecuzione singola: " + PrintException("LockFile", [_FileLockName]))
            return False

    else:
        _FileLock = open(_FileLockName, 'w')
        try:
            import fcntl
            fcntl.lockf(_FileLock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except:
            Log("Errore esecuzione singola: " + PrintException("LockFile", [_FileLockName]))
            return False

    return True

def OnlyOneInstanceEnd():
    global _FileLock
    global _FileLockName

    if WINDOWS:
        os.close(_FileLock)
    else:
        _FileLock.close()

    os.unlink(_FileLockName)

def PrintDiskSpace():
    """DF = subprocess.check_output(["df","-h",GetPath(_Dest)]).decode(sys.getfilesystemencoding())""" #Diff 2-3
    DF = subprocess.check_output(["df","-h",GetPath(_Dest)]).decode("utf8") #Diff 2-3
    Log("DiskSpace:" + os.linesep + DF)

def PrintException(method, params):
    R = 'Exception "' + method + '" ('
    for P in params:
        R += str(P) + ", "

    R += ")"

    for E in sys.exc_info():
        R += " - " + str(E)

    return R

def ShiftDirs(dirType):
    DirList = fnmatch.filter(os.listdir(_Dest), dirType + ".??.????????-??????")
    if DirList is not None and len(DirList) >= 1:
        DirList.sort()
        for I in range(len(DirList) - 1, -1, -1):
            Source = os.path.join(_Dest, DirList[I])
            Dest = os.path.join(_Dest, dirType + "." + str(I + 1).zfill(2) + "." + DirList[I][len(dirType + ".??."):])
            try:
                Log("Aggiornamento periodi (ShiftDirs): " + dirType + " " + Source + " " + Dest)
                os.rename(Source, Dest)
            except:
                Log("Errore aggiornamento periodi: " + PrintException("ShiftDirs", [dirType, I, Source, Dest]))
                return False

    DirList = fnmatch.filter(os.listdir(_Dest), "Corrente")
    if DirList is not None and len(DirList) == 1:
        Source = os.path.join(_Dest, "Corrente")
        Dest = os.path.join(_Dest, dirType + ".00." + DATETIMESUFFIX)
        try:
            Log("Aggiornamento periodi (ShiftDirs): " + dirType + " " + Source + " " + Dest)
            os.rename(Source, Dest)
        except:
            Log("Errore aggiornamento periodi: " + PrintException("ShiftDirs 00", [dirType, Source, Dest]))
            return False

    return True

def DoRaiseLevel(dirTypeStart, dirTypeEnd, dirName):
    global _Status

    if not ShiftDirs(dirTypeEnd):
        return False

    Source = os.path.join(_Dest, dirName)
    Dest = os.path.join(_Dest, dirTypeEnd + ".00." + dirName[len(dirTypeStart + ".??."):])
    try:
        Log("Aggiornamento periodi (DoRaiseLevel): " + dirTypeStart + " " + dirTypeEnd + " " + dirName + " " + Source + " " + Dest)
        os.rename(Source, Dest)
    except:
        Ex = PrintException("DoRaiseLevel", [dirTypeStart, dirTypeEnd, dirName, Source, Dest])
        Log("Errore aggiornamento periodi: " + Ex)
        _Status.append("Errore DoRaiseLevel (" + dirTypeStart + " " + dirTypeEnd + "): " + Source + " " + Dest + " " + Ex)
        return False
    else:
        _Status.append("DoRaiseLevel (" + dirTypeStart + " " + dirTypeEnd + "): " + Source + " " + Dest)

    return True

def DoDeleteLast(length, limit, dirName):
    if length > limit:
        try:
            Log("Aggiornamento periodi (DoDeleteLast): " + str(length) + " " + str(limit) + " " + dirName)
            shutil.rmtree(os.path.join(_Dest, dirName))
        except:
            Ex = PrintException("DoDeleteLast", [length, limit, os.path.join(_Dest, dirName)])
            Log("Errore aggiornamento periodi: " + Ex)
            _Status.append("Errore DoDeleteLast (" + str(length) + " " + str(limit) + "): " + dirName + " " + Ex)
            return False
        else:
            _Status.append("DoDeleteLast (" + str(length) + " " + str(limit) + "): " + dirName)

    return True

def GetLimitDirNumber(dirType):
    Limit = 0
    if dirType == "Ora":
        Limit = _Hour
    elif dirType == "Giorno":
        Limit = _Day
    elif dirType == "Sett":
        Limit = _Week
    elif dirType == "Mese":
        Limit = _Month
    elif dirType == "Anno":
        Limit = _Year

    return Limit

def RaiseLevel(dirTypeStart, dirTypeEnd):
    if len(dirTypeEnd) > 0:
        DirListStart = fnmatch.filter(os.listdir(_Dest), dirTypeStart + ".??.????????-??????")
        if DirListStart is not None and len(DirListStart) >= 1:
            DirListStart.sort()
            LastDirStart = DirListStart[-1]

            DirListEnd = fnmatch.filter(os.listdir(_Dest), dirTypeEnd + ".??.????????-??????")
            if DirListEnd is not None and len(DirListEnd) >= 1:
                DirListEnd.sort()
                FirstDirEnd = DirListEnd[0]

                Diff = DiffFistLastDir(dirTypeStart, LastDirStart, dirTypeEnd, FirstDirEnd)

                if (dirTypeEnd == "Giorno" and Diff >= 1) or (dirTypeEnd == "Sett" and Diff >= 7) or (dirTypeEnd == "Mese" and Diff >= 31) or (dirTypeEnd == "Anno" and Diff >= 365):
                    if not DoRaiseLevel(dirTypeStart, dirTypeEnd, LastDirStart):
                        return False
            else:
                if len(DirListStart) > GetLimitDirNumber(dirTypeStart):
                    if not DoRaiseLevel(dirTypeStart, dirTypeEnd, LastDirStart):
                        return False

    DirList = fnmatch.filter(os.listdir(_Dest), dirTypeStart + ".??.????????-??????")
    if DirList is not None and len(DirList) >= 1:
        DirList.sort()
        LastDir = DirList[-1]

        if not DoDeleteLast(len(DirList), GetLimitDirNumber(dirTypeStart), LastDir):
            return False

    return True

def DiffFistLastDir(dirTypeFirst, first,dirTypeLast, last):
    PresentDate = datetime.datetime.strptime(first[len(dirTypeFirst + ".??."):], "%Y%m%d-%H%M%S")
    PastDate = datetime.datetime.strptime(last[len(dirTypeLast + ".??."):], "%Y%m%d-%H%M%S")
    R = (PresentDate - PastDate).days
    Log("Aggiornamento periodi (DiffFistLastDir): " + dirTypeFirst + " " + first + " " + dirTypeLast + " " + last + " " + str(R))
    return R

def UpdatePeriods():
    Log("Aggiornamento periodi...")

    ShiftExecuted = False

    if _Hour > 0:
        if not ShiftExecuted:
            if not ShiftDirs("Ora"):
                return False
        ShiftExecuted = True

        if _Day > 0:
            if not RaiseLevel("Ora", "Giorno"):
                return False
        elif _Week > 0:
            if not RaiseLevel("Ora", "Sett"):
                return False
        elif _Month > 0:
            if not RaiseLevel("Ora", "Mese"):
                return False
        elif _Year > 0:
            if not RaiseLevel("Ora", "Anno"):
                return False
        else:
            if not RaiseLevel("Ora", ""):
                return False


    if _Day > 0:
        if not ShiftExecuted:
            if not ShiftDirs("Giorno"):
                return False
        ShiftExecuted = True

        if _Week > 0:
            if not RaiseLevel("Giorno", "Sett"):
                return False
        elif _Month > 0:
            if not RaiseLevel("Giorno", "Mese"):
                return False
        elif _Year > 0:
            if not RaiseLevel("Giorno", "Anno"):
                return False
        else:
            if not RaiseLevel("Giorno", ""):
                return False

    if _Week > 0:
        if not ShiftExecuted:
            if not ShiftDirs("Sett"):
                return False
        ShiftExecuted = True

        if _Month > 0:
            if not RaiseLevel("Sett", "Mese"):
                return False
        elif _Year > 0:
            if not RaiseLevel("Sett", "Anno"):
                return False
        else:
            if not RaiseLevel("Sett", ""):
                return False

    if _Month > 0:
        if not ShiftExecuted:
            if not ShiftDirs("Mese"):
                return False
        ShiftExecuted = True

        if _Year > 0:
            if not RaiseLevel("Mese", "Anno"):
                return False
        else:
            if not RaiseLevel("Mese", ""):
                return False

    if _Year > 0:
        if not RaiseLevel("Anno", ""): return False

    Log("Fine aggiornamento")
    return True

if __name__ == "__main__":
    main(sys.argv[1:])
