class TubeCensus:
    def __init__(self, cache_dir=None):
        raise NotImplementedError

    def sample(self, n, source="ids"):
        raise NotImplementedError

    def fetch(self, channels, source="ids", closest=None):
        raise NotImplementedError