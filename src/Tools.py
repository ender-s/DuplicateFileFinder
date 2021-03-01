class Tools(object):
    _SIZES = [1024, 1048576, 1073741824, 1099511627776]
    _SIZENAMES = ["bytes", "KiB", "MiB", "GiB", "TiB"]

    def humanReadableSize(self, size):
        HRSize = float(size)
        for i in range(len(self._SIZES)):
            if size >= self._SIZES[i]:
                HRSize /= 1024.0
            else:
                break
    
        return f"{round(HRSize, 2)} {self._SIZENAMES[i]}"

    