# `clips` Directory

Highlight-clip video files. Anything dropped in here is served by the API at

```
http://localhost:4000/assets/clips/<filename>
```

(see `api/backend/assets/asset_routes.py`), and the frontend builds a `<video>`
element pointing at that URL for every clip whose `clip.clip_url` is not NULL.

`clip_url` is stored **with a leading slash** — a clip row holding
`/super_cool_clip.mp4` is played from
`http://localhost:4000/assets/clips/super_cool_clip.mp4`, which resolves to
`api/assets/clips/super_cool_clip.mp4` on disk.

The seed data in `database-files/talent_scout.sql` gives clip 1 a `clip_url` of
`/super_cool_clip.mp4`, so dropping a file with that name here is enough to see
a real video in the app. Clip 2 is seeded with a NULL `clip_url` and renders
without a player.

Video files are deliberately not committed to the repository.
