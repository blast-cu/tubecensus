import msgpack
from rocksdict import Rdict, Options, AccessType
from datetime import datetime, timezone

WAYBACK_PREFIX = "http://web.archive.org/web/"

def epoch_to_ts(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y%m%d%H%M%S")

def ts_to_epoch(ts):
    return int(datetime.strptime(ts, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp())

def pad_ts(ts,end=False,mid=False):
    if end:
        if len(ts) == 4:
            return ts + "1231235959"
        elif len(ts) == 6:
            return ts + "31235959"
        elif len(ts) == 8:
            return ts + "235959"
        elif len(ts) == 10:
            return ts + "5959"
        elif len(ts) == 12:
            return ts + "59"
    elif mid:
        if len(ts) == 4:
            return ts + "0702120000"
        elif len(ts) == 6:
            return ts + "02120000"
        elif len(ts) == 8:
            return ts + "120000"
        elif len(ts) == 10: 
            return ts + "0000"
        elif len(ts) == 12:
            return ts + "00"
    else:
        if len(ts) == 4:
            return ts + "0101000000"
        elif len(ts) == 6:
            return ts + "01000000"
        elif len(ts) == 8:
            return ts + "000000"
        elif len(ts) == 10:
            return ts + "0000"
        elif len(ts) == 12:
            return ts + "00"
    return ts

class YTStore:
    def __init__(self, db_path):
        self.db_path = db_path
        opts = Options(raw_mode=True)
        opts.create_if_missing(False)
        self.db = Rdict(
            self.db_path,
            options=opts,
            access_type=AccessType.read_only(),
        )

    def _raw_bytes(self, key):
        raw = self.db.get(key.encode("utf-8"))
        if raw is None:
            return None
        return msgpack.unpackb(raw, raw=False)

    def get(self, key: str):
        packed = self._raw_bytes(key)
        if packed is None:
            return None
        return [(epoch_to_ts(ts), suffix) for ts, suffix in packed]

    def get_wb(self, key: str):
        packed = self._raw_bytes(key)
        if packed is None:
            return None
        return [
            f"{WAYBACK_PREFIX}{epoch_to_ts(ts)}/{suffix}"
            for ts, suffix in packed
        ]

    def close(self):
        self.db.close()