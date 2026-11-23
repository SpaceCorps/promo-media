# SpaceCorps 2027 promo media

Finished promo videos and picture posts of [SpaceCorps 2027](https://play.spacecorps.tech/), and the feeds the
publishing service reads.

- Releases `v<version>` hold the videos, release `cards` the picture posts.
- `schedule.json`: every post of the history series with its day and hour (Europe/Stockholm).
- `feeds/*.xml`: one RSS feed per channel. `.github/workflows/feeds.yml` adds each post at its hour (`scripts/feeds.py`).
