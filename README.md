# TalentScout

**Team Purplicious — CS 3200, Summer B 2026**

TalentScout is a bidirectional recruiting platform for high school athletes and college
recruiters. Too many promising athletes go unnoticed because they don't know how to market
themselves, don't live where scouts travel, and can't afford a $2,000 recruiting service.
TalentScout replaces that with data: athletes publish their metrics, personal records, and
highlight clips, and recruiters publish the rosters and openings they actually need to fill.
Both sides can see who has been looking at them.

Key features:

- **Athlete profiles** with GPA, height/weight, graduation year, recruitment status, personal
  record history, and highlight clips.
- **A recruiter clip feed** with athlete metrics one tap away, plus filtered athlete search on
  GPA, height, graduation year, and status.
- **Roster openings** so athletes can see which programs match their numbers, and recruiters
  can see which athletes are looking at their rosters.
- **View tracking** in both directions — the coaches who viewed an athlete, and the athletes
  who viewed a roster.
- **Aggregate, de-identified analytics** for researchers studying high school athletics.

## Personas

| Persona | Who they are | What they do in the app |
|---|---|---|
| **Bethany** — High School Athlete | Sophomore hurdler in a region scouts rarely visit | Maintains her profile and PRs, uploads clips, checks which programs match her numbers and which coaches viewed her |
| **Kevin** — College Recruiter | Football recruiter whose travel budget was cut | Posts rosters and openings, scrolls the clip feed, queries athletes by metric, sees who viewed his rosters |
| **Jonathan** — Administrator | Moderates content and supports accounts | Reads an unfiltered feed, deletes clips, comments, rosters, and accounts, posts platform announcements |
| **Lori** — Data Analyst | Master's researcher studying young-adult athletics | Pulls aggregate metrics, filters by gender/sport/class year, exports de-identified rows |

The design document — personas, user stories, ER diagrams, and the SQL behind each user
story — is in [docs/TalentScout.md](docs/TalentScout.md).

## Architecture

Three Docker containers, defined in `docker-compose.yaml`:

| Container | Stack | Port | Source |
|---|---|---|---|
| `web-app` | Streamlit | 8501 | `./app` |
| `web-api` | Flask REST API | 4000 | `./api` |
| `mysql_db` | MySQL 9 | 3200 (host) → 3306 | `./database-files` |

Streamlit pages never touch MySQL directly. They call the Flask API at
`http://web-api:4000`, and only the API opens database connections
(`api/backend/db_connection/__init__.py` hands out one connection per request).

## Repository Layout

```
app/                    Streamlit front end
  src/Home.py           Persona picker (the mock "login" screen)
  src/pages/            One file per screen, numbered by persona
  src/modules/nav.py    Role-based sidebar navigation
  src/modules/api.py    Shared API request/flash-message helpers
  src/modules/clips.py  Playing a clip's video, and where its file lives
  src/modules/moderation.py  Admin-only page guard and two-click delete
api/                    Flask REST API
  backend/rest_entry.py create_app(): config, DB hook, blueprint registration
  backend/<domain>/     One blueprint per domain (see below)
  backend/db_connection/ Per-request MySQL connection
  assets/clips/         Clip video files, served from /assets/clips
database-files/         01_..._ddl.sql schema + 02_..._seed.sql data, run on first DB start
docs/                   Design document and course setup guides
datasets/, ml-src/      Empty placeholders from the course template
```

### Running it

Full instructions are in [docs/RepoSetup.md](docs/RepoSetup.md). The short version:

```bash
cp api/.env.template api/.env    # then fill in SECRET_KEY and MYSQL_ROOT_PASSWORD
docker compose up -d
```

Then open <http://localhost:8501>. If you change anything in `database-files/`, the volume has
to be dropped for MySQL to re-run the SQL:

```bash
docker compose down db -v && docker compose up db -d
```

### A note on "login"

`Home.py` shows one button per persona. Clicking a button sets `role`, `first_name`, and
`user_id` in `st.session_state` and jumps to that persona's home page; `nav.py` then builds a
sidebar containing only that role's pages. There are no passwords and no real authentication —
this is the course template's RBAC pattern, described in [docs/RBAC.md](docs/RBAC.md), and it
is deliberate: the project is about the data model, not about auth.

## The REST API

Every TalentScout route is mounted under `/talent_scout`. Routes are grouped into six
blueprints by the tables they own, so each blueprint is the single place to look for a given
part of the schema.

**`athletes`** — `api/backend/athletes/athlete_routes.py` (athlete, personal_record, event)

| Method | Route | Purpose |
|---|---|---|
| GET | `/athlete` | Athlete search; filters `min_gpa`, `min_height_cm`, `grad_year`, `gender`, `status` |
| POST | `/athlete` | Create an athlete profile for an existing user |
| GET | `/athlete/<id>` | Full profile with clips and personal records nested |
| PUT | `/athlete/<id>` | Update metrics, academics, or recruitment status |
| DELETE | `/athlete/<id>` | Delete the account (cascades through the user row) |
| GET | `/personal_record` | All personal records; filters `athlete_id`, `event_id` |
| GET | `/athlete/<id>/personal_record` | One athlete's record history, oldest first |
| POST | `/athlete/<id>/personal_record` | Log a new personal record |
| GET | `/event` | Event catalog for dropdowns |

**`clips`** — `api/backend/clips/clip_routes.py` (clip, comment)

| Method | Route | Purpose |
|---|---|---|
| GET | `/clip` | The feed; filter `athlete_id` |
| POST | `/clip` | Upload a clip, with the video as multipart field `video` |
| GET | `/clip/<id>` | One clip with the poster's metrics and its comments |
| PUT | `/clip/<id>` | Edit a caption |
| PUT | `/clip/<id>/video` | Attach or replace the clip's video file |
| DELETE | `/clip/<id>` | Remove a clip and its video (comments cascade) |
| GET | `/clip/<id>/comment` | Just the comment thread |
| GET | `/comment` | Every comment on the platform; filters `clip_id`, `user_id` |
| POST | `/comment` | Comment on a clip |
| PUT | `/comment/<id>` | Edit a comment body |
| DELETE | `/comment/<id>` | Remove a comment |

Clip videos are the one thing that doesn't live in MySQL — the bytes go on disk
and the row only carries the file's name in `clip_url`. See
[Clip videos](#clip-videos) below.

**`recruiting`** — `api/backend/recruiting/recruiting_routes.py` (recruiter, university, sport,
roster, opening)

| Method | Route | Purpose |
|---|---|---|
| GET | `/recruiter` | All recruiters with their university; filter `university_id` |
| GET | `/recruiter/<id>` | One recruiter with university and rosters nested |
| DELETE | `/recruiter/<id>` | Delete a recruiter account |
| GET | `/university` | Universities with recruiter counts |
| GET | `/sports` | Sport catalog for dropdowns |
| GET | `/roster` | All rosters with the posting recruiter and their university; filters `recruiter_id`, `sport_id`, `division`, `gender` |
| POST | `/roster` | Post a roster |
| GET | `/roster/<id>` | One roster with its openings nested |
| DELETE | `/roster/<id>` | Take a roster down |
| GET | `/opening` | Openings; filters `roster_id`, `position`, `grad_year`, `sport_id`, `recruiter_id`, and `athlete_id` (only openings that athlete qualifies for) |
| POST | `/opening` | Add an opening to a roster |
| DELETE | `/roster/<id>/opening/<n>` | Remove one opening |

**`engagement`** — `api/backend/engagement/engagement_routes.py` (recruiter_view, roster_view)

| Method | Route | Purpose |
|---|---|---|
| GET | `/recruiter_view` | All profile views; filters `recruiter_id`, `athlete_id` |
| GET | `/recruiter_view/<athlete_id>` | Coaches who viewed this athlete, with contact info |
| POST | `/recruiter_view/<athlete_id>` | Record a profile view |
| GET | `/roster_view` | All roster views; filters `recruiter_id`, `roster_id`, `athlete_id` |
| GET | `/roster_view/<roster_id>` | Athletes who viewed this roster, with their metrics |
| POST | `/roster_view/<roster_id>` | Record a roster view |

**`admin`** — `api/backend/admin/admin_routes.py` (announcement, user moderation)

| Method | Route | Purpose |
|---|---|---|
| GET | `/announcement` | All announcements; `active=true` for the current window only |
| GET | `/announcement/<id>` | One announcement with its author |
| POST | `/announcement` | Post an announcement |
| PUT | `/announcement/<id>` | Reword or reschedule |
| DELETE | `/announcement/<id>` | Pull an announcement down |
| GET | `/user` | Every account with its derived role; filter `role` |
| GET | `/user/<id>` | One account with its role and clip/comment/roster counts |
| DELETE | `/user/<id>` | Delete any account regardless of role |

**`analytics`** — `api/backend/analytics/analytics_routes.py` (read-only, de-identified)

| Method | Route | Purpose |
|---|---|---|
| GET | `/analytics/athlete_summary` | Counts and averages; `group_by` = `gender`, `graduation_year`, `recruitment_status`, or `sport` |
| GET | `/analytics/athlete` | One de-identified row per athlete, ready to export |
| GET | `/analytics/personal_record` | Average performance per event per date |
| GET | `/analytics/event` | Per-event record counts, best and average times |
| GET | `/analytics/platform_summary` | Platform-wide totals in a single row |

The course template's demo blueprint (`api/backend/simple/simple_routes.py`) is still mounted
at the root and is the quickest way to confirm the API container is alive without involving
MySQL: `/`, `/data`, `/niceMessage`, `/message`, `/playlist`.

### Clip videos

`clip.clip_url` holds the name of a clip's video file, stored **with a leading slash**, and
`api/backend/assets/asset_routes.py` serves those files:

| Method | Route | Purpose |
|---|---|---|
| GET | `/assets/clips/<filename>` | One clip's video file, from `api/assets/clips` |

This is the only route not mounted under `/talent_scout` — these are files, not resources in
the data model — and the only URL the *browser* requests directly, so it uses the API's
published host port (`http://localhost:4000`) rather than the `web-api` Docker hostname the
Streamlit pages call. Set `CLIP_ASSET_BASE_URL` on the app container to override that.

A clip whose `clip_url` is set plays in a `st.video` player pointing at
`http://localhost:4000/assets/clips/<filename>`; a clip whose `clip_url` is NULL has no video
attached and renders without a player, which every page showing clips has to handle.

Athletes upload the file itself through the app — **Upload a Clip** sends it alongside the
caption as multipart field `video`, and **My Clips** can attach or replace one later. The API
writes it into `api/assets/clips` named after the clip's id (clip 12 uploaded as `race.mp4`
becomes `/12.mp4`) and stores that name in `clip_url`; the uploaded name never reaches the
file system. Files can also be dropped into `api/assets/clips` by hand and pointed at from
`clip_url`, which is how the seeded `/super_cool_clip.mp4` works. Deleting a clip removes an
uploaded file with it, but leaves hand-placed ones alone. See
[api/assets/clips/README.md](api/assets/clips/README.md) and
`api/backend/clips/clip_storage.py`.

`clip_url` is a column on `clip`, so a database created before it was added has to be
re-seeded — `docker compose down db -v && docker compose up db -d` — or every clip request
fails with `Unknown column 'c.clip_url'`.

### Conventions used by every route

- Handlers open `get_db().cursor(dictionary=True)`, wrap the work in `try/except/finally`, and
  always close the cursor. Writes call `get_db().commit()`.
- Filters are appended to a `WHERE 1=1` base clause with `%s` placeholders, so parameters are
  never string-formatted into SQL. Where a *column* has to be interpolated (the analytics
  `group_by`), it comes from a whitelist dict.
- `TIME` columns are `CAST(... AS CHAR)` because mysql-connector returns them as timedeltas,
  which Flask cannot serialize.
- Missing rows return 404 with `{"error": ...}`, bad input returns 400, database failures are
  logged and return 500.

## Database

`database-files/01_talent_scout_ddl.sql` creates the `talent_scout` schema and
`database-files/02_talent_scout_seed.sql` fills it. MySQL runs every `.sql` file in that
folder in alphabetical order the first time the container starts, which is why the files are
numbered — the DDL has to run before the data.

The seed file is generated by `database-files/generate_seed.py` (Python Faker, fixed RNG
seed, so it reproduces byte-for-byte). Edit the generator and re-run it rather than editing
the SQL by hand:

```bash
pip install faker
python database-files/generate_seed.py
```

Because the init scripts only run on an empty data directory, picking up a changed seed file
means dropping the volume: `docker compose down -v && docker compose up -d`.

`user` is a supertype with `athlete`, `recruiter`, `administrator`, and `analyst` subtype
tables keyed on `user_id`, which is why deleting an account means deleting the `user` row and
letting `ON DELETE CASCADE` do the rest.

## Documentation

| Document | Description |
|---|---|
| [docs/TalentScout.md](docs/TalentScout.md) | Phase 1/2 design document: personas, user stories, wireframes, ER diagrams, SQL |
| [docs/README.md](docs/README.md) | Index of the course template documentation |
| [docs/PreReq.md](docs/PreReq.md) | Python environment and tooling setup |
| [docs/RepoSetup.md](docs/RepoSetup.md) | Forking, `.env`, running the containers |
| [docs/ImportantTips.md](docs/ImportantTips.md) | Hot reloading, container recovery, MySQL gotchas |
| [docs/RBAC.md](docs/RBAC.md) | How the role-based sidebar works |
| [docs/Theming.md](docs/Theming.md) | Colors and fonts via `app/src/.streamlit/config.toml` |
