import os
import pandas as pd
from huggingface_hub import snapshot_download
from tqdm import tqdm

from tubecensus.sampler import sample_one, sample_many
from tubecensus.fetcher import YTStore, pad_ts, ts_to_epoch
from tubecensus.parser import parse_wb

class TubeCensus:
    """
    data_dir: str
        The path to the local data store.
    """
    def __init__(self, data_dir=os.getenv('TUBECENSUS_DIR',os.path.join(os.path.expanduser("~"), ".tubecensus"))):
        snapshot_download(repo_id="ceggleston/tubecensus", repo_type="dataset", local_dir=data_dir)
        self.data_dir = data_dir

        self.census = {vers:os.path.join(data_dir, f"census/census_{vers}.txt") for vers in ["usernames", "ids", "customs", "handles"]}
        self.snapshots = {vers:YTStore(os.path.join(data_dir, f"snapshots/{vers}.rocksdb")) for vers in ["usernames", "ids", "customs", "handles"]}
        self.cache = {os.path.basename(f).split(".")[0]:f for f in os.listdir(os.path.join(data_dir, "cache")) if f.endswith(".csv")}

        #self.cache_df = pd.concat([pd.read_csv(os.path.join(data_dir, "cache", v), dtype={'session':str,'username':str,'id':str,'custom':str,'handle':str,'subs':"UInt32",'ts':"UInt64",'url':str}) for k,v in self.cache.items()], ignore_index=True)

    """ 
    sample(): samples channel identifiers from one of the four collected formats.
        n: int
            The number of channels sampled.
        by: str
            The channel URL format to be sampled over. One of "ids", "usernames", "customs", or "handles".
    """
    def sample(self, n, by="ids"):
        return pd.DataFrame(sample_many(self.census[by],n),columns=[by])

    def sample_until(self, n, condition=lambda x: True, by="ids"):
        sampled = []
        while len(sampled) < n:
            line = sample_one(self.census[by])
            if line and condition(line):
                sampled.append(line)
        return pd.DataFrame(sampled, columns=[by])

    def has_timestamp(self, channel, from_ts, to_ts, by="ids"):
        captures = self.snapshots[by].get(channel)
        if not captures:
            return False
        from_epoch = ts_to_epoch(pad_ts(from_ts))
        to_epoch = ts_to_epoch(pad_ts(to_ts, end=True))
        return any(from_epoch <= ts_to_epoch(pad_ts(cap[0])) <= to_epoch for cap in captures)
    
    """
    fetch(): fetches the subscriber counts for a list of channels or DataFrame, between from_ts and to_ts (inclusive), or the closest snapshot to a given timestamp.
        channels: list<str> or pd.DataFrame
        by: str
            The channel URL format to be sampled over. One of "ids", "usernames", "customs", or "handles".
        from_ts/to_ts: [str, str]
            A tuple of two timestamps (from_ts, to_ts) to filter snapshots.
        closest: str
            The timestamp for which to find the closest snapshot.
    """ 
    def fetch(self, channels, by="ids", from_ts=None, to_ts=None, closest=None):
        pbar = tqdm(total=len(channels))
        if isinstance(channels, list):
            df = pd.DataFrame(channels, columns=[by])
        else:
            df = channels.copy()
        db = self.snapshots[df.columns[0]]
        datas=[]
        for channel in df[df.columns[0]]:
            captures = db.get(channel)
            if closest:
                closest_captures = sorted(captures, key=lambda x: abs(ts_to_epoch(pad_ts(x[0])) - ts_to_epoch(pad_ts(closest,mid=True))))
                for c in closest_captures:
                    md=parse_wb(self.wb_url(*c),c[0])
                    if md:
                        datas.append(md)
                        break
            elif from_ts and to_ts:
                from_epoch = ts_to_epoch(pad_ts(from_ts))
                to_epoch = ts_to_epoch(pad_ts(to_ts, end=True))
                filtered_captures = [cap for cap in captures if from_epoch <= ts_to_epoch(pad_ts(cap[0])) <= to_epoch]
                for c in filtered_captures:
                    md=parse_wb(self.wb_url(*c),c[0])
                    if md:
                        datas.append(md)
                        break
            else:
                raise Exception("Must specify either from_ts and to_ts or closest.")
            pbar.update(1)
        return pd.DataFrame(datas)

    def wb_url(self, ts, suffix):
        return f"http://web.archive.org/web/{ts}/youtube.com/{suffix}"

    def close(self):
        for db in self.snapshots.values():
            db.close()