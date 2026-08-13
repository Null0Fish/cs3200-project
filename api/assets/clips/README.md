# `clips` Directory

Highlight-clip video files. Anything dropped in here is served by the API at

```
http://localhost:4000/assets/clips/<filename>
```

(see `api/backend/assets/asset_routes.py`), and the frontend plays that URL for
every clip whose `clip.clip_url` is not NULL.

Files arrive here two ways. An athlete uploading a clip through the app sends
the video with the request, and the API writes it here named after the clip's
id — clip 12 uploaded as `race.mp4` becomes `12.mp4`, with `clip_url` set to
`/12.mp4`. A file can also be dropped in by hand and pointed at from `clip_url`,
which is what the seed data does.

`clip_url` is stored **with a leading slash** — a clip row holding
`/super_cool_clip.mp4` is played from
`http://localhost:4000/assets/clips/super_cool_clip.mp4`, which resolves to
`api/assets/clips/super_cool_clip.mp4` on disk.

The seed data in `database-files/talent_scout.sql` gives clip 1 a `clip_url` of
`/super_cool_clip.mp4`, so dropping a file with that name here is enough to see
a real video in the app. Clip 2 is seeded with a NULL `clip_url` and renders
without a player.

Video files are deliberately not committed to the repository.
