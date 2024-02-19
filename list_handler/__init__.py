from pathlib import Path
import json, os

class ResumableList:

    def __init__(self, filename, chunksize, hostname, filehash):
        self.__resume_file = Path(f".{hostname}.{filehash}")
        self.__list_file = Path(filename)
        self.__chunksize = chunksize
        self.__chunk_index = { "confirmed" : [], "unconfirmed" : [] }

        self.__fh = open(self.__list_file, "rt")
        self.__fh.seek(0, 2)
        self.__eof = self.__fh.tell()


        if os.path.exists(self.__resume_file):
            with open(self.__resume_file, "rt") as res:
                self.__chunk_index = json.load(res)
            self.__offset = self.__recalc_offset()
            self.__write_resume()
        else:
            self.__offset = 0
            self.__write_resume("xt")

        self.__fh.seek(self.__offset)


    def __del__(self):
        self.__fh.close()

    def __write_resume(self, mode="wt"):
        with open(self.__resume_file, mode) as res:
            res.write(json.dumps(self.__chunk_index))

    def __recalc_offset(self):
        offset = 0

        if len(self.__chunk_index['unconfirmed']) > 0:
            offset = min(self.__chunk_index['unconfirmed'])
        elif len(self.__chunk_index['confirmed']) > 0:
            offset = max(self.__chunk_index['confirmed'])
        
        remove_confirmed = [x for x in self.__chunk_index['confirmed'] if x > offset]

        for i in remove_confirmed:
            self.__chunk_index['confirmed'].remove(i)

        self.__chunk_index['unconfirmed'] = []

        return offset
    
    def is_eof(self):
        return self.__fh.tell() >= self.__eof

    def file_end_pos(self):
        return self.__eof

    def resume_filename(self):
        return self.__resume_file
    
    def list_filename(self):
        return self.__list_file
    
    def current_offset(self):
        return self.__fh.tell()

    def print_stats(self):
        print(f"Offset for [{self.__list_file}]: {self.__fh.tell() } out of max {self.__eof} ({self.__fh.tell() / self.__eof:0.2%} complete)")

    class Chunk:
        def __init__(self, offset, end, items):
            self.__offset = offset
            self.__items = items
            self.__pos = 0
            self.__end = end
            self.__found = 0
            self.__missed = 0
            self.__error = 0


        def add_found(self):
            self.__found = self.__found + 1
        
        def found(self):
            return self.__found

        def add_missed(self):
            self.__missed = self.__missed + 1
        
        def missed(self):
            return self.__missed

        def add_error(self):
            self.__error = self.__error + 1
        
        def error(self):
            return self.__error

        def __iter__(self):
            return iter(self.__items)
        
        def offset(self):
            return self.__offset
        
        def end(self):
            return self.__end


    def get_chunk(self):

        pos = self.__fh.tell()

        read = []

        for x in range(0, self.__chunksize):
            line = self.__fh.readline()
            if not line is None and len(line.rstrip()) > 0:
                read.append(line.rstrip())


        self.__chunk_index["unconfirmed"].append(pos)
        self.__write_resume()

        return ResumableList.Chunk(pos, self.__fh.tell(), read)

    def confirm_chunk(self, chunk):
        if chunk.offset() in self.__chunk_index["unconfirmed"]:
            self.__chunk_index["unconfirmed"].remove(chunk.offset())
            self.__chunk_index["confirmed"].append(chunk.end())
            self.__write_resume()
