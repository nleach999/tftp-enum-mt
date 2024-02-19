import tftpy
from pathlib import Path

class TftpDownload:    

    def __init__(self, host, outdir, port=69, timeout=tftpy.SOCK_TIMEOUT):
        self.__client = tftpy.TftpClient(host, port)
        self.__outdir = outdir
        self.__host = host
        self.__port = port
        self.__timeout = timeout


    def download(self, filename):
        try:
            self.__client.download(filename, Path(self.__outdir) / Path(filename).name, timeout=self.__timeout)
            return True
        except tftpy.TftpTimeout as toex:
            raise toex
        except (tftpy.TftpException, Exception):
            return False
        