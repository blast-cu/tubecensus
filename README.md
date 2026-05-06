# TubeCensus

A Python library for sampling YouTube channels and retrieving their historical Wayback Machine metadata.

## Setup
* Requirements: ~20GB of storage. 
    * Defaults to `~/.tubecensus`, but can be overriden by `TubeCensus(data_dir=...)`, or the `TUBECENSUS_DIR` environment variable.
* `pip install tubecensus`
* Example:
```
from tubecensus import TubeCensus
tc = TubeCensus()                                        # client configuration goes here
sample = tc.sample(10, by='usernames')                   # sample 10 channels by their username field
subs = tc.fetch(sample, from_ts='2019', to_ts='2021')    # retrieve the subs of those 10 when present from 2019-2021.
```
## Features

### sample(n, by={"usernames","ids","customs", "handles"})
- Sample YouTube channels from the URLs collected from the Wayback machine indices.
- Current version includes unique URLs up to 2023. These are featured in the four YouTube channel formats:
    1. Username (`/profile?user=`, `/user/`): 34.8M channels
    2. ID (`/channel/UC`): 106M channels 
    3. Custom Page (`/c/`): 5.9M channels
    4. Handle (`/@`): 25.4M channels
- See our paper for more discussion.

### sample_until(n, by, condition)
- Construct a conditional sample by repeatedly drawing channels and keeping them if the condition function is met.
- Can be used along with YouTube API / Innertube to construct samples conditioned on API metadata (e.g. country, join date, channel topic), or alternatively our metadata (subscribers at given timestamp).

### fetch(channels, by, from_ts, to_ts, closest)
- Retrieve the subscriber counts for a given timestamp using the Wayback Machine.
- Requires to either specify a timestamp range using `(from_ts, to_ts)` or `closest`.
- Returns outputs as a Pandas DataFrame, and includes additional channel identifier metadata extracted from the page (username / id fields).

## Citation
```
@article{tubecensus, 
    title={TubeCensus: A Transparent, Replicable, and Large-Scale Census of YouTube Channels and their Subscriber Counts Over Time}, 
    volume={20}, 
    number={1}, 
    journal={Proceedings of the International AAAI Conference on Web and Social Media}, 
    author={Eggleston, Chloe and Handler, Abram and Pacheco, Maria Leonor}, 
    year={2026}, 
    month={May}, 
}
```

## TO-DOs
- Early channel IDs via CDN URLs
    - Before the standardization of the YouTube channel ID (c. 2012), they were occasionally used in the URLs of custom channel page content (such as profile pictures and custom CSS). They can be used to map additional usernames to channel IDs. 
- Scrape channel hubs / related channels
    - Subscriber counts for additional channels are sometimes accessible in the related channels tab. When paired with identifiers extracted from profile pictures or subscriber button HTML attributes, they can add upwards of ~10 subscriber counts in a given page scrape.
- Caching
    - We redistribute the data collected in our paper as a part of [our dataset](https://zenodo.org/uploads/18267682), which is downloaded with this library. We plan to integrate these into the library such that URLs in the cache are not re-scraped.
