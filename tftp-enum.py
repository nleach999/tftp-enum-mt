import logging
import traceback
import argparse
import multiprocessing as mp
import sys, os
import hashlib
import list_handler, tftp
import urllib

logging.basicConfig(level=logging.CRITICAL)

parser = argparse.ArgumentParser(description = "Enumerate and download files from a TFTP service.")
parser.add_argument('-H', '--host', action='store', required=True, help="Hostname or IP where the service can be reached", dest='host')
parser.add_argument('-p', '--port', action='store', default=69, help="TFTP service port (default: 69)", dest='port')
parser.add_argument('-l', '--list', action='store', required=True, help="A list of file names", dest='list')
parser.add_argument('-c', '--chunk', action='store', default=1024, help="The number of names handled per thread (default: 1024)", dest='chunk', type=int)
parser.add_argument('-t', '--threads', action='store', default=3, help="The number of concurrent threads (default: 3)", dest='threads', type=int)
parser.add_argument('-o', '--outdir', action='store', default='.', help="Directory where downloaded files will be stored (default: .)", dest='outdir')
parser.add_argument('--timeout', action='store', default=60, type=int, help="Transfer timeout, in seconds (default: 60)", dest='timeout')


args = None

try:
    args = parser.parse_args(sys.argv[1:])
except SystemExit as ex:
    parser.print_help()
    exit(ex.code)
    


print(f"Enumerating {args.host} Port {args.port}")

filehash = None

with open(args.list, "rb") as list:
    digest = hashlib.file_digest(list, "md5")
    filehash = digest.hexdigest()

thelist = list_handler.ResumableList(args.list, args.chunk, args.host, filehash)

print(f"Resume information stored in [{thelist.resume_filename()}]")
thelist.print_stats()

if thelist.current_offset() >= thelist.file_end_pos():
    exit(0)


class ChunkThread:

    def __init__(self):
        self.__queue = mp.Queue()
        self.__receiver, self.__sender = mp.Pipe(False)
        self.__processed_bytes = thelist.current_offset()

    def FindFiles(self, chunk, src):
        for fname in chunk:
            try:
                if src.download(urllib.parse.quote(fname)):
                    chunk.add_found()
                else:
                    chunk.add_missed()

            except Exception as ex:
                self.__sender.send( (chunk,  
                  f"Exception: [{type(ex)}] File Name: [{fname}] Msg: [{str(ex)}] Stack Trace: [{traceback.format_exception(ex)}]"))
                return

        self.__queue.put(chunk)

    def FinishChunks(self, async_result):
        while not async_result.ready() or not self.__queue.empty():
            try:
                val = self.__queue.get(timeout=1)
                self.__processed_bytes = self.__processed_bytes + (val.end() - val.offset())
                print(f"Chunk complete: Found: {val.found()} Missed: {val.missed()} Approx. {self.__processed_bytes / thelist.file_end_pos():.2%} complete.")
                thelist.confirm_chunk(val)
            except:
                if self.__receiver.poll(1):
                    bad_chunk, exception  = self.__receiver.recv()
                    print(f"Error processing chunk covering file range {bad_chunk.offset()} to {bad_chunk.end()}")
                    print(f"Error: {exception}")
        
thread = ChunkThread()

def chunkgen():
    while not thelist.is_eof():
        yield thelist.get_chunk()

def ChunkFunc(chunk):
    thread.FindFiles(chunk, tftp.TftpDownload(args.host, args.outdir, args.port, args.timeout))

with mp.Pool(args.threads, maxtasksperchild=3) as p:
    thread.FinishChunks(p.map_async(ChunkFunc, chunkgen(), chunksize=1))
    p.close()
    p.join()

