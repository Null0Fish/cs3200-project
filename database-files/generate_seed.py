"""Generate 02_talent_scout_seed.sql -- the sample data for the talent_scout DB.

Run from the repo root (or anywhere; the output path is resolved relative to
this file):

    pip install faker
    python database-files/generate_seed.py

The generator is seeded with a fixed RNG seed, so re-running it reproduces the
same file byte-for-byte. The first rows of every table are the hand-written
demo rows the app's personas depend on (user_id 1 = Bethany the athlete,
2 = Kevin the recruiter, 3 = Johnathan the admin, 4 = Lori the analyst) -- those
are emitted verbatim and everything generated is appended after them, so the
auto-increment ids the app hard-codes never move.
"""

import random
from datetime import date, datetime, timedelta
from pathlib import Path

from faker import Faker

SEED = 3200
fake = Faker("en_US")
Faker.seed(SEED)
rng = random.Random(SEED)

OUT = Path(__file__).resolve().parent / "02_talent_scout_seed.sql"

# "Today" for the generated data. Announcements straddle this date so some are
# live in the app the moment the database comes up.
TODAY = date(2026, 8, 13)

# ---------------------------------------------------------------------------
# how much of everything
# ---------------------------------------------------------------------------
N_UNIVERSITY = 40
N_SPORT = 30
N_EVENT = 40
N_ATHLETE = 100
N_RECRUITER = 34
N_ANALYST = 8
N_ADMIN = 6
N_ANNOUNCEMENT = 40
N_ROSTER = 70
N_OPENING = 150
N_PERSONAL_RECORD = 350
N_CLIP = 180
N_COMMENT = 400
N_ROSTER_VIEW = 200
N_RECRUITER_VIEW = 200


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------
def q(value):
    """Render a Python value as a SQL literal."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime):
        return "'" + value.strftime("%Y-%m-%d %H:%M:%S") + "'"
    if isinstance(value, date):
        return "'" + value.isoformat() + "'"
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


def insert(table, columns, rows):
    """Build a multi-row INSERT statement, chunked so no statement is huge."""
    if not rows:
        return ""
    out = []
    for start in range(0, len(rows), 50):
        chunk = rows[start:start + 50]
        values = ",\n       ".join(
            "(" + ", ".join(q(v) for v in row) + ")" for row in chunk
        )
        out.append(
            f"INSERT INTO {table} ({', '.join(columns)})\nVALUES {values};\n"
        )
    return "\n".join(out)


def rand_date(start, end):
    return start + timedelta(days=rng.randint(0, (end - start).days))


def rand_datetime(start, end):
    d = rand_date(start, end)
    return datetime(d.year, d.month, d.day,
                    rng.randint(6, 23), rng.choice([0, 5, 10, 15, 20, 25, 30,
                                                    35, 40, 45, 50, 55]))


# ---------------------------------------------------------------------------
# reference data
# ---------------------------------------------------------------------------
UNIVERSITIES = [
    ("Boston College", "bc.edu"), ("Boston University", "bu.edu"),
    ("Clemson University", "clemson.edu"), ("Duke University", "duke.edu"),
    ("Emory University", "emory.edu"), ("Fordham University", "fordham.edu"),
    ("Georgetown University", "georgetown.edu"),
    ("Gonzaga University", "gonzaga.edu"),
    ("Indiana University", "indiana.edu"), ("Iowa State University", "iastate.edu"),
    ("Lehigh University", "lehigh.edu"), ("Marquette University", "marquette.edu"),
    ("Michigan State University", "msu.edu"),
    ("Ohio State University", "osu.edu"), ("Oregon State University", "oregonstate.edu"),
    ("Penn State University", "psu.edu"), ("Purdue University", "purdue.edu"),
    ("Rice University", "rice.edu"), ("Rutgers University", "rutgers.edu"),
    ("Stanford University", "stanford.edu"), ("Syracuse University", "syr.edu"),
    ("Texas A&M University", "tamu.edu"), ("Tulane University", "tulane.edu"),
    ("University of Alabama", "ua.edu"), ("University of Arizona", "arizona.edu"),
    ("University of California, Los Angeles", "ucla.edu"),
    ("University of Colorado Boulder", "colorado.edu"),
    ("University of Florida", "ufl.edu"), ("University of Georgia", "uga.edu"),
    ("University of Illinois", "illinois.edu"), ("University of Iowa", "uiowa.edu"),
    ("University of Kansas", "ku.edu"), ("University of Michigan", "umich.edu"),
    ("University of Minnesota", "umn.edu"), ("University of Oregon", "uoregon.edu"),
    ("University of Texas at Austin", "utexas.edu"),
    ("University of Virginia", "virginia.edu"),
    ("University of Washington", "washington.edu"),
    ("Vanderbilt University", "vanderbilt.edu"),
    ("Villanova University", "villanova.edu"),
    ("Wake Forest University", "wfu.edu"), ("Xavier University", "xavier.edu"),
]

# Sport name -> (positions an opening can ask for, height band in cm by gender).
SPORTS = {
    "Long Jump": (["Jumper", "Sprinter"], (165, 190), (155, 178)),
    "Football": (["Quarterback", "Wide Receiver", "Running Back", "Linebacker",
                  "Offensive Line", "Defensive Line", "Cornerback", "Safety",
                  "Tight End", "Kicker"], (175, 200), (165, 183)),
    "Basketball": (["Point Guard", "Shooting Guard", "Small Forward",
                    "Power Forward", "Center"], (183, 211), (170, 196)),
    "Baseball": (["Pitcher", "Catcher", "First Base", "Shortstop",
                  "Outfielder"], (175, 196), (165, 180)),
    "Softball": (["Pitcher", "Catcher", "Infielder", "Outfielder"],
                 (170, 190), (160, 180)),
    "Soccer": (["Goalkeeper", "Center Back", "Fullback", "Midfielder",
                "Winger", "Striker"], (170, 193), (158, 180)),
    "Volleyball": (["Outside Hitter", "Middle Blocker", "Setter", "Libero",
                    "Opposite"], (180, 205), (168, 193)),
    "Ice Hockey": (["Goaltender", "Defenseman", "Center", "Left Wing",
                    "Right Wing"], (175, 196), (163, 183)),
    "Field Hockey": (["Goalkeeper", "Defender", "Midfielder", "Forward"],
                     (170, 188), (157, 178)),
    "Lacrosse": (["Goalie", "Defense", "Midfield", "Attack"],
                 (175, 196), (160, 180)),
    "Swimming": (["Freestyle", "Backstroke", "Breaststroke", "Butterfly",
                  "Distance", "Sprint"], (178, 200), (165, 185)),
    "Diving": (["Springboard", "Platform"], (165, 183), (152, 170)),
    "Track and Field": (["Sprinter", "Distance", "Hurdler", "Thrower",
                         "Jumper", "Vaulter"], (170, 196), (158, 183)),
    "Cross Country": (["Distance"], (168, 188), (155, 175)),
    "Wrestling": (["Lightweight", "Middleweight", "Heavyweight"],
                  (163, 190), (152, 173)),
    "Tennis": (["Singles", "Doubles"], (175, 196), (160, 183)),
    "Golf": (["Golfer"], (172, 193), (160, 180)),
    "Rowing": (["Coxswain", "Port", "Starboard", "Sculler"],
               (183, 201), (170, 188)),
    "Gymnastics": (["All-Around", "Vault", "Bars", "Beam", "Floor"],
                   (157, 175), (147, 165)),
    "Water Polo": (["Goalkeeper", "Driver", "Center", "Utility"],
                   (180, 198), (168, 185)),
    "Rugby": (["Prop", "Hooker", "Lock", "Flanker", "Scrum-half", "Fly-half",
               "Center", "Wing", "Fullback"], (175, 198), (163, 183)),
    "Fencing": (["Foil", "Epee", "Sabre"], (170, 190), (158, 178)),
    "Sailing": (["Skipper", "Crew"], (170, 190), (157, 178)),
    "Skiing": (["Slalom", "Giant Slalom", "Downhill", "Nordic"],
               (170, 190), (157, 178)),
    "Beach Volleyball": (["Blocker", "Defender"], (180, 200), (168, 188)),
    "Bowling": (["Bowler"], (168, 190), (155, 178)),
    "Triathlon": (["Triathlete"], (170, 188), (157, 175)),
    "Equestrian": (["Hunt Seat", "Western", "Dressage"], (165, 183), (155, 175)),
    "Squash": (["Singles", "Doubles"], (172, 190), (158, 178)),
    "Shot Put": (["Thrower"], (183, 201), (168, 188)),
}

# Events an athlete can hold a personal record in. Timed events store a TIME
# in personal_record.time; measured/scored events store a DOUBLE in .score.
# (name, kind, low, high) where the range is seconds for timed events and the
# natural unit -- meters, points, strokes -- for scored ones.
EVENTS = [
    ("100m Dash", "time", 10.4, 13.8),
    ("200m Dash", "time", 21.2, 28.4),
    ("400m Dash", "time", 47.5, 64.0),
    ("800m Run", "time", 112.0, 150.0),
    ("1600m Run", "time", 250.0, 330.0),
    ("3200m Run", "time", 545.0, 720.0),
    ("5K Cross Country", "time", 900.0, 1260.0),
    ("110m Hurdles", "time", 13.9, 19.5),
    ("300m Hurdles", "time", 38.0, 52.0),
    ("4x100m Relay Split", "time", 10.6, 14.2),
    ("50m Freestyle", "time", 20.8, 29.5),
    ("100m Freestyle", "time", 46.5, 62.0),
    ("200m Freestyle", "time", 103.0, 140.0),
    ("500m Freestyle", "time", 280.0, 360.0),
    ("100m Backstroke", "time", 52.0, 70.0),
    ("100m Breaststroke", "time", 58.0, 78.0),
    ("100m Butterfly", "time", 50.0, 68.0),
    ("200m IM", "time", 116.0, 155.0),
    ("40 Yard Dash", "time", 4.35, 5.60),
    ("Pro Agility Shuttle", "time", 4.05, 5.20),
    ("Mile Time Trial", "time", 245.0, 400.0),
    ("2K Erg", "time", 360.0, 460.0),
    ("Long Jump Distance", "score", 4.90, 7.80),
    ("Triple Jump Distance", "score", 10.20, 15.60),
    ("High Jump Height", "score", 1.45, 2.15),
    ("Pole Vault Height", "score", 2.60, 5.20),
    ("Shot Put Distance", "score", 9.50, 20.10),
    ("Discus Distance", "score", 28.00, 62.00),
    ("Javelin Distance", "score", 30.00, 72.00),
    ("Hammer Throw Distance", "score", 30.00, 68.00),
    ("Vertical Jump", "score", 45.00, 105.00),
    ("Broad Jump", "score", 200.00, 340.00),
    ("Bench Press Max", "score", 45.00, 170.00),
    ("Squat Max", "score", 70.00, 250.00),
    ("Deadlift Max", "score", 90.00, 280.00),
    ("Beep Test Level", "score", 8.00, 14.50),
    ("Golf 18 Hole Score", "score", 66.00, 96.00),
    ("Free Throw Percentage", "score", 52.00, 96.00),
    ("Serve Speed", "score", 70.00, 190.00),
    ("Gymnastics All-Around", "score", 30.00, 58.00),
]

DIVISIONS = ["D1", "D1", "D1", "D2", "D2", "D3", "NAIA", "NJCAA", None]
STATUSES = (["open"] * 6) + (["committed"] * 3) + ["inactive"]

CLIP_CAPTIONS = [
    "Season highlight reel", "Full game film vs. {opp}", "State championship final",
    "New personal best this weekend", "First half highlights",
    "Sophomore year highlights", "Junior year highlights",
    "Senior night highlights", "Conference semifinal",
    "Offseason training session", "Combine testing day",
    "Regional qualifier run", "Back-to-back scores in the third",
    "Defensive highlights from the {opp} game", "Overtime winner",
    "Summer showcase highlights", "Coach asked me to post this one",
    "Two-minute skills tape", "Every touch vs. {opp}",
    "Invitational finals -- fastest heat", "Recruiting tape, updated",
    "Best plays from the tournament", "Warm-up and form check",
    "Full meet, all four events", "Clutch finish in the final seconds",
]

COMMENT_BODIES = [
    "Great burst off the line.", "Impressive footwork here.",
    "Would love to see more film from this season.",
    "Nice work -- your form has come a long way.",
    "Sending this to our position coach.",
    "That closing speed is real.", "Solid fundamentals throughout.",
    "Can you post the full game?", "What was your time on that last rep?",
    "Really strong second half.", "Good hands, keep it up.",
    "This is the tape that got my attention.",
    "Let's connect about our program.", "Your acceleration stands out.",
    "Great effort on defense.", "Are you attending any summer camps?",
    "Big improvement from your last clip.", "Love the motor on this one.",
    "Keep posting -- we're watching.", "That is a college-level rep.",
    "Strong finish through the line.", "Nice job staying composed under pressure.",
    "What are your current PRs?", "This is exactly the position fit we need.",
    "Well played. Following your season.",
]

ANNOUNCEMENT_SEEDS = [
    ("Scheduled maintenance this weekend",
     "Talent Scout will be read-only on Saturday from 2-6 AM ET while we "
     "upgrade the database. Clips and rosters stay viewable; new posts and "
     "edits will be rejected during that window."),
    ("New: filter rosters by division",
     "Athletes can now narrow roster search by division, gender, and sport at "
     "the same time. Find it at the top of the Browse Rosters page."),
    ("Recruiting dead period begins Monday",
     "Per NCAA rules, coaches may not initiate contact during the dead period. "
     "Messages sent through Talent Scout will queue and deliver afterward."),
    ("Verify your graduation year",
     "Openings match on graduation year. If yours is wrong, recruiters will "
     "not see you. Update it on your profile page."),
    ("Clip uploads now support larger files",
     "The upload limit is now 250 MB per clip. Longer full-game film no longer "
     "needs to be trimmed before posting."),
    ("Welcome to the fall recruiting season",
     "Over 400 new openings were posted this month. Check the roster board "
     "regularly -- most fill within three weeks."),
    ("Reminder: keep your personal records current",
     "Records older than a season are hidden from recruiter search results. "
     "Add a new entry after each meet to stay visible."),
    ("Analyst reports refreshed",
     "The analytics dashboards now include this season's data. Comparisons by "
     "sport, gender, and graduation year have been rebuilt."),
    ("Report inappropriate comments",
     "Every comment has a report action. Reported comments are reviewed by an "
     "administrator within 24 hours."),
    ("Profile photos coming next term",
     "We are testing profile photos with a small group of athletes. Expect a "
     "wider rollout after the winter season."),
    ("Combine results import",
     "Verified combine results from partner events are imported automatically. "
     "Look for the event name on your personal records list."),
    ("Two-factor authentication is available",
     "Recruiters handling multiple rosters should enable 2FA from account "
     "settings. It will become mandatory for recruiter accounts next year."),
    ("Roster archiving",
     "Rosters whose end date has passed are archived and no longer appear in "
     "search. Recruiters can still view them from their profile."),
    ("Spring showcase registration is open",
     "Registration for the regional spring showcase closes at the end of the "
     "month. Ask your coach for the team code."),
    ("Search is faster",
     "Athlete search now returns results roughly four times faster after an "
     "indexing change. No action needed on your part."),
    ("Holiday support hours",
     "Support responses will be slower over the holiday break. Urgent account "
     "issues still go to the administrator contact on your account page."),
    ("Deleted accounts and your data",
     "Deleting an account removes your clips, comments, and records "
     "immediately. Export anything you want to keep first."),
    ("New event types added",
     "Ten new events were added to the personal records list, including "
     "throwing and swimming events requested by users."),
    ("Recruiter view history",
     "Athletes can now see which programs have viewed their profile and when. "
     "Recruiters can turn this off per roster."),
    ("Survey: what should we build next?",
     "A short survey is open through the end of the month. Tell us which "
     "features matter most before we plan the next term of work."),
]

POSITION_NOTE_OPPONENTS = ["Lincoln", "Riverside", "Central", "Northgate",
                           "Westview", "St. Mark's", "Oakridge", "Fairmont"]


# ---------------------------------------------------------------------------
# the hand-written demo rows the app personas depend on -- emitted verbatim
# ---------------------------------------------------------------------------
DEMO = """-- The rows below are the original hand-written demo data. They are kept first
-- and unchanged because the app's persona buttons hard-code user_id 1
-- (Bethany, athlete), 2 (Kevin, recruiter), 3 (Johnathan, admin) and 4 (Lori,
-- analyst), and because api/assets/clips documents clip 1 as the clip with a
-- real video file attached. Everything generated is appended after these.

INSERT INTO user (first_name, last_name, email, phone)
VALUES ('Bethany', 'Smith', 'bsmith@email.com', null),
       ('Kevin', 'Fox', 'kfox@email.com', null),
       ('Jonathan', 'Brown', 'jbrown@email.com', '1234567899'),
       ('Lori', 'Kyle', 'lkyle@email.com', null),
       ('Other', 'Athlete', 'other.athlete@email.com', null),
       ('Other', 'Recruiter', 'other.recruiter@email.com', null),
       ('Other', 'Admin', 'other.admin@email.com', null),
       ('Other', 'Analyst', 'other.analyst@email.com', null),
       ('New', 'User', 'new.user@email.com', null);

INSERT INTO analyst (user_id)
VALUES (4),
       (8);

INSERT INTO administrator (user_id)
VALUES (3),
       (7);

INSERT INTO announcement (user_id, title, body, scheduled_start, scheduled_end)
VALUES (3, 'Hello', 'Enjoy the app or smth.', '2028-08-01 00:00:00', '2028-08-02 01:00:00'),
       (3, 'Test', 'Can you see this?', '2029-08-01 00:00:00', '2029-08-02 01:00:00');

INSERT INTO university (website_url, name)
VALUES ('https://northeastern.edu', 'Northeastern'),
       ('https://school.edu', 'School');

INSERT INTO recruiter (user_id, university_id)
VALUES (2, 1),
       (6, 2);

INSERT INTO sport (name)
VALUES ('Long Jump'),
       ('Football');

INSERT INTO roster (user_id, sport_id, division, start_date, end_date, gender, team_name)
VALUES (2, 1, 'D1', '2028-08-01', '2029-08-01', 'F', 'Fast Runners'),
       (6, 2, 'D2', '2028-08-01', '2029-08-01', 'M', 'Other Team');

INSERT INTO opening (opening_number, roster_id, required_gpa, required_height_cm, position, grad_year)
VALUES (1, 1, 3.00, 140, 'Sprinter', 2029),
       (2, 1, 4.00, 180, 'Slow runner', 2029);

INSERT INTO athlete (user_id, graduation_year, dob, gender, height_cm, weight_kg, gpa, recruitment_status)
VALUES (1, 2029, '2011-04-16', 'F', 140, 65, 3.95, 'open'),
       (5, 2028, '2010-01-01', 'M', 150, 70, 2.50, 'open');

INSERT INTO event (name)
VALUES ('100m Dash'),
       ('200m Dash');

INSERT INTO personal_record (user_id, date, event_id, time, score)
VALUES (1, '2028-08-02', 1, '00:00:30.50', NULL),
       (1, '2028-08-01', 2, '00:00:28.50', NULL);

-- The second clip is seeded with a NULL clip_url on purpose: the app has to
-- cope with clip rows that have no video file attached.
INSERT INTO clip (user_id, posted_at, caption, clip_url)
VALUES (1, '2028-08-01', 'Super cool clip', '/super_cool_clip.mp4'),
       (1, '2028-08-02', 'Other cool clip', NULL);

INSERT INTO comment (clip_id, user_id, posted_at, content)
VALUES (1, 2, '2028-07-01', 'Good stuff'),
       (1, 2, '2028-07-01', 'SO good I commented again');

INSERT INTO roster_view (user_id, roster_id, view_time)
VALUES (1, 1, '2028-08-02 10:15:00'),
       (5, 2, '2028-08-03 10:15:00');

INSERT INTO recruiter_view (athlete_id, recruiter_id, view_time)
VALUES (1, 2, '2028-08-02 09:00:00'),
       (5, 6, '2028-08-03 09:00:00');
"""

# Ids already used by the demo rows above.
DEMO_USER_IDS = list(range(1, 10))
DEMO_ATHLETES = [1, 5]
DEMO_RECRUITERS = [2, 6]
DEMO_ANALYSTS = [4, 8]
DEMO_ADMINS = [3, 7]
DEMO_UNIVERSITIES = [1, 2]
DEMO_SPORTS = {1: "Long Jump", 2: "Football"}
DEMO_EVENTS = {1: "100m Dash", 2: "200m Dash"}
DEMO_ROSTERS = [1, 2]
DEMO_CLIPS = [1, 2]
DEMO_PR_KEYS = {(1, date(2028, 8, 2), 1), (1, date(2028, 8, 1), 2)}
DEMO_ROSTER_VIEWS = {(1, 1), (5, 2)}
DEMO_RECRUITER_VIEWS = {(1, 2), (5, 6)}


# ---------------------------------------------------------------------------
# generation
# ---------------------------------------------------------------------------
sections = []

# --- university -------------------------------------------------------------
university_rows = []
university_ids = list(DEMO_UNIVERSITIES)
next_university_id = 3
for name, domain in UNIVERSITIES[:N_UNIVERSITY - len(DEMO_UNIVERSITIES)]:
    university_rows.append((f"https://www.{domain}", name[:50]))
    university_ids.append(next_university_id)
    next_university_id += 1
sections.append(("university", ["website_url", "name"], university_rows))

# --- sport ------------------------------------------------------------------
sport_rows = []
sport_by_id = dict(DEMO_SPORTS)
next_sport_id = 3
for name in list(SPORTS)[:N_SPORT]:
    if name in DEMO_SPORTS.values():
        continue
    sport_rows.append((name,))
    sport_by_id[next_sport_id] = name
    next_sport_id += 1
sections.append(("sport", ["name"], sport_rows))
sport_ids = list(sport_by_id)

# --- event ------------------------------------------------------------------
event_rows = []
event_by_id = {}
for eid, name in DEMO_EVENTS.items():
    event_by_id[eid] = next(e for e in EVENTS if e[0] == name)
next_event_id = 3
for spec in EVENTS[:N_EVENT]:
    if spec[0] in DEMO_EVENTS.values():
        continue
    event_rows.append((spec[0],))
    event_by_id[next_event_id] = spec
    next_event_id += 1
sections.append(("event", ["name"], event_rows))
event_ids = list(event_by_id)

# --- user + role subtypes ---------------------------------------------------
# One user row per person; the role tables below claim those ids. Every
# generated user lands in exactly one role table, so the mandatory
# participation of the athlete/recruiter/analyst/administrator subtypes holds.
user_rows = []
next_user_id = 10
used_emails = {"bsmith@email.com", "kfox@email.com", "jbrown@email.com",
               "lkyle@email.com", "other.athlete@email.com",
               "other.recruiter@email.com", "other.admin@email.com",
               "other.analyst@email.com", "new.user@email.com"}


def new_user(domain_pool):
    """Append a user row and return its id, first name and last name."""
    global next_user_id
    first = fake.first_name()
    last = fake.last_name()
    base = f"{first}.{last}".lower().replace("'", "").replace(" ", "")
    domain = rng.choice(domain_pool)
    email = f"{base}@{domain}"
    n = 2
    while email in used_emails or len(email) > 80:
        email = f"{base}{n}@{domain}"
        n += 1
    used_emails.add(email)
    # Roughly two thirds of people list a phone number.
    phone = "".join(str(rng.randint(0, 9)) for _ in range(10)) \
        if rng.random() < 0.66 else None
    uid = next_user_id
    next_user_id += 1
    user_rows.append((first, last, email, phone))
    return uid, first, last


PERSONAL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com"]

athlete_ids = list(DEMO_ATHLETES)
athlete_rows = []
athlete_meta = {}  # user_id -> dict(sport, gender, grad_year)

for _ in range(N_ATHLETE - len(DEMO_ATHLETES)):
    uid, _, _ = new_user(PERSONAL_DOMAINS)
    sport = rng.choice(list(SPORTS))
    positions, male_h, female_h = SPORTS[sport]
    gender = rng.choice("MF")
    lo, hi = male_h if gender == "M" else female_h
    height = rng.randint(lo, hi)
    # Weight tracks height with sport-flavored spread; football and wrestling
    # skew heavy, distance running light.
    bmi = rng.uniform(20.5, 27.5)
    if sport in ("Football", "Wrestling", "Rugby", "Shot Put"):
        bmi += rng.uniform(1.5, 5.0)
    if sport in ("Cross Country", "Track and Field", "Triathlon", "Gymnastics"):
        bmi -= rng.uniform(1.0, 3.0)
    weight = round(bmi * (height / 100) ** 2)
    grad_year = rng.choices([2026, 2027, 2028, 2029, 2030],
                            weights=[1, 3, 4, 4, 2])[0]
    # Most high schoolers turn 18 during their graduation year.
    birth_year = grad_year - rng.choice([17, 18, 18, 18, 19])
    dob = rand_date(date(birth_year, 1, 1), date(birth_year, 12, 31))
    gpa = round(min(4.0, max(1.9, rng.gauss(3.35, 0.45))), 2)
    status = rng.choice(STATUSES)
    # A senior who has already committed is the common case for 2026 grads.
    if grad_year == 2026 and rng.random() < 0.5:
        status = "committed"
    athlete_ids.append(uid)
    athlete_meta[uid] = {"sport": sport, "gender": gender,
                         "grad_year": grad_year}
    athlete_rows.append((uid, grad_year, dob, gender, height, weight, gpa,
                         status))

athlete_meta[1] = {"sport": "Long Jump", "gender": "F", "grad_year": 2029}
athlete_meta[5] = {"sport": "Football", "gender": "M", "grad_year": 2028}

recruiter_ids = list(DEMO_RECRUITERS)
recruiter_rows = []
recruiter_university = {2: 1, 6: 2}
for _ in range(N_RECRUITER - len(DEMO_RECRUITERS)):
    uid, _, _ = new_user(["athletics.edu"])
    uni = rng.choice(university_ids)
    recruiter_ids.append(uid)
    recruiter_university[uid] = uni
    recruiter_rows.append((uid, uni))

# Recruiter emails read better on their school's domain than a generic one.
analyst_ids = list(DEMO_ANALYSTS)
analyst_rows = []
for _ in range(N_ANALYST - len(DEMO_ANALYSTS)):
    uid, _, _ = new_user(["talentscout.io"])
    analyst_ids.append(uid)
    analyst_rows.append((uid,))

admin_ids = list(DEMO_ADMINS)
admin_rows = []
for _ in range(N_ADMIN - len(DEMO_ADMINS)):
    uid, _, _ = new_user(["talentscout.io"])
    admin_ids.append(uid)
    admin_rows.append((uid,))

sections.append(("user", ["first_name", "last_name", "email", "phone"],
                 user_rows))
sections.append(("athlete", ["user_id", "graduation_year", "dob", "gender",
                             "height_cm", "weight_kg", "gpa",
                             "recruitment_status"], athlete_rows))
sections.append(("recruiter", ["user_id", "university_id"], recruiter_rows))
sections.append(("analyst", ["user_id"], analyst_rows))
sections.append(("administrator", ["user_id"], admin_rows))

# --- announcement -----------------------------------------------------------
# Windows straddle TODAY so the home page has live announcements as well as
# expired and upcoming ones.
announcement_rows = []
for i in range(N_ANNOUNCEMENT - 2):
    title, body = ANNOUNCEMENT_SEEDS[i % len(ANNOUNCEMENT_SEEDS)]
    start_day = rand_date(TODAY - timedelta(days=300), TODAY + timedelta(days=90))
    start = datetime(start_day.year, start_day.month, start_day.day,
                     rng.choice([0, 6, 8, 9, 12]), 0)
    end = start + timedelta(days=rng.choice([3, 7, 7, 14, 21, 30]))
    announcement_rows.append((rng.choice(admin_ids), title, body, start, end))
sections.append(("announcement", ["user_id", "title", "body",
                                  "scheduled_start", "scheduled_end"],
                 announcement_rows))

# --- roster -----------------------------------------------------------------
# Every recruiter owns at least one roster (mandatory participation on the
# recruiter side), then the remainder are handed out at random.
TEAM_SUFFIX = {
    "M": ["Men's", "Men's"],
    "F": ["Women's"],
}
roster_rows = []
roster_meta = dict()  # roster_id -> dict(sport, gender, recruiter, start, end)
next_roster_id = 3
generated_recruiters = [r for r in recruiter_ids if r not in DEMO_RECRUITERS]
owners = list(generated_recruiters)
while len(owners) < N_ROSTER - len(DEMO_ROSTERS):
    owners.append(rng.choice(recruiter_ids))
rng.shuffle(owners)

for owner in owners[:N_ROSTER - len(DEMO_ROSTERS)]:
    sid = rng.choice(sport_ids)
    sport = sport_by_id[sid]
    gender = rng.choice("MF")
    season_start_year = rng.choice([2026, 2026, 2027])
    start = date(season_start_year, rng.choice([8, 9, 10]), rng.randint(1, 28))
    end = date(season_start_year + 1, rng.choice([3, 4, 5, 6]),
               rng.randint(1, 28))
    label = "Men's" if gender == "M" else "Women's"
    team_name = f"{label} {sport}"[:30]
    roster_rows.append((owner, sid, rng.choice(DIVISIONS), start, end, gender,
                        team_name))
    roster_meta[next_roster_id] = {"sport": sport, "gender": gender,
                                   "recruiter": owner, "start": start,
                                   "end": end}
    next_roster_id += 1

roster_meta[1] = {"sport": "Long Jump", "gender": "F", "recruiter": 2,
                  "start": date(2028, 8, 1), "end": date(2029, 8, 1)}
roster_meta[2] = {"sport": "Football", "gender": "M", "recruiter": 6,
                  "start": date(2028, 8, 1), "end": date(2029, 8, 1)}
roster_ids = list(roster_meta)
sections.append(("roster", ["user_id", "sport_id", "division", "start_date",
                            "end_date", "gender", "team_name"], roster_rows))

# --- opening ----------------------------------------------------------------
# A weak entity: opening_number is only unique within its roster, so each
# roster numbers its own openings from 1. Every generated roster gets at least
# one opening.
opening_rows = []
generated_rosters = [r for r in roster_ids if r not in DEMO_ROSTERS]
opening_counts = {rid: 1 for rid in generated_rosters}
remaining = (N_OPENING - 2) - len(generated_rosters)
for _ in range(max(0, remaining)):
    opening_counts[rng.choice(generated_rosters)] += 1

for rid in generated_rosters:
    meta = roster_meta[rid]
    positions = SPORTS[meta["sport"]][0]
    male_h, female_h = SPORTS[meta["sport"]][1], SPORTS[meta["sport"]][2]
    lo, hi = male_h if meta["gender"] == "M" else female_h
    chosen = rng.sample(positions, min(len(positions), opening_counts[rid]))
    while len(chosen) < opening_counts[rid]:
        chosen.append(rng.choice(positions))
    for number, position in enumerate(chosen, start=1):
        # Requirements sit a little below the roster's typical build so real
        # athletes actually clear them.
        required_height = rng.randint(lo - 8, hi - 10) if hi - 10 > lo - 8 \
            else lo - 8
        opening_rows.append((number, rid,
                             round(rng.uniform(2.0, 3.6), 2),
                             required_height,
                             position[:20],
                             meta["start"].year + rng.choice([0, 1])))
sections.append(("opening", ["opening_number", "roster_id", "required_gpa",
                             "required_height_cm", "position", "grad_year"],
                 opening_rows))

# --- personal_record --------------------------------------------------------
# Weak entity keyed by (athlete, date, event). Athletes log records against
# events that suit their sport where one exists, otherwise anything.
SPORT_EVENT_HINTS = {
    "Swimming": ["Freestyle", "Backstroke", "Breaststroke", "Butterfly", "IM"],
    "Diving": ["Vertical Jump", "Gymnastics All-Around"],
    "Cross Country": ["5K", "Mile", "1600m", "3200m"],
    "Track and Field": ["Dash", "Hurdles", "Relay", "Jump", "Vault", "Run",
                        "Throw", "Discus", "Javelin", "Shot Put"],
    "Long Jump": ["Long Jump", "Triple Jump", "Dash", "Broad Jump"],
    "Shot Put": ["Shot Put", "Discus", "Bench Press", "Squat"],
    "Football": ["40 Yard", "Shuttle", "Vertical", "Broad", "Bench", "Squat",
                 "Deadlift"],
    "Basketball": ["Vertical", "Shuttle", "Free Throw", "Beep"],
    "Golf": ["Golf 18"],
    "Tennis": ["Serve Speed", "Shuttle"],
    "Rowing": ["2K Erg", "Deadlift", "Squat"],
    "Gymnastics": ["Gymnastics All-Around", "Vertical"],
}


def pick_event(sport):
    hints = SPORT_EVENT_HINTS.get(sport)
    if hints:
        matches = [eid for eid, spec in event_by_id.items()
                   if any(h in spec[0] for h in hints)]
        if matches and rng.random() < 0.85:
            return rng.choice(matches)
    return rng.choice(event_ids)


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"


pr_rows = []
pr_keys = set(DEMO_PR_KEYS)
attempts = 0
while len(pr_rows) < N_PERSONAL_RECORD - 2 and attempts < N_PERSONAL_RECORD * 40:
    attempts += 1
    uid = rng.choice([a for a in athlete_ids if a in athlete_meta])
    eid = pick_event(athlete_meta[uid]["sport"])
    when = rand_date(TODAY - timedelta(days=730), TODAY)
    key = (uid, when, eid)
    if key in pr_keys:
        continue
    pr_keys.add(key)
    name, kind, low, high = event_by_id[eid]
    if kind == "time":
        pr_rows.append((uid, when, eid, format_time(round(rng.uniform(low, high), 2)),
                        None))
    else:
        pr_rows.append((uid, when, eid, None, round(rng.uniform(low, high), 2)))
sections.append(("personal_record", ["user_id", "date", "event_id", "time",
                                     "score"], pr_rows))

# --- clip -------------------------------------------------------------------
# clip_url stays NULL for generated clips: the matching video files are not
# committed to the repo (see api/assets/clips/README.md), and a URL with no
# file behind it would render a broken player.
clip_rows = []
clip_meta = {1: {"user": 1, "posted": date(2028, 8, 1)},
             2: {"user": 1, "posted": date(2028, 8, 2)}}
next_clip_id = 3
clip_posters = [rng.choice(athlete_ids) for _ in range(N_CLIP - 2)]
for uid in clip_posters:
    posted = rand_date(TODAY - timedelta(days=540), TODAY)
    caption = rng.choice(CLIP_CAPTIONS).format(
        opp=rng.choice(POSITION_NOTE_OPPONENTS))
    clip_rows.append((uid, posted, caption, None))
    clip_meta[next_clip_id] = {"user": uid, "posted": posted}
    next_clip_id += 1
sections.append(("clip", ["user_id", "posted_at", "caption", "clip_url"],
                 clip_rows))
clip_ids = list(clip_meta)

# --- comment ----------------------------------------------------------------
# Comments come mostly from recruiters, some from other athletes, and never
# land before the clip they are on was posted.
commenters = recruiter_ids * 3 + athlete_ids + analyst_ids
comment_rows = []
for _ in range(N_COMMENT - 2):
    cid = rng.choice(clip_ids)
    posted_clip = clip_meta[cid]["posted"]
    author = rng.choice(commenters)
    latest = min(TODAY, posted_clip + timedelta(days=120))
    when = posted_clip if latest <= posted_clip else rand_date(posted_clip, latest)
    comment_rows.append((cid, author, when, rng.choice(COMMENT_BODIES)))
sections.append(("comment", ["clip_id", "user_id", "posted_at", "content"],
                 comment_rows))

# --- roster_view (bridge: athlete <-> roster) -------------------------------
roster_view_rows = []
seen = set(DEMO_ROSTER_VIEWS)
attempts = 0
while len(roster_view_rows) < N_ROSTER_VIEW - 2 and attempts < N_ROSTER_VIEW * 40:
    attempts += 1
    uid = rng.choice(athlete_ids)
    rid = rng.choice(roster_ids)
    if (uid, rid) in seen:
        continue
    # Athletes mostly browse rosters that match their own sport and gender.
    meta = roster_meta[rid]
    if uid in athlete_meta and rng.random() < 0.6:
        if meta["gender"] != athlete_meta[uid]["gender"]:
            continue
    seen.add((uid, rid))
    roster_view_rows.append((uid, rid,
                             rand_datetime(TODAY - timedelta(days=365), TODAY)))
sections.append(("roster_view", ["user_id", "roster_id", "view_time"],
                 roster_view_rows))

# --- recruiter_view (bridge: athlete <-> recruiter) -------------------------
recruiter_view_rows = []
seen = set(DEMO_RECRUITER_VIEWS)
attempts = 0
while len(recruiter_view_rows) < N_RECRUITER_VIEW - 2 \
        and attempts < N_RECRUITER_VIEW * 40:
    attempts += 1
    aid = rng.choice(athlete_ids)
    rid = rng.choice(recruiter_ids)
    if (aid, rid) in seen:
        continue
    seen.add((aid, rid))
    recruiter_view_rows.append((aid, rid,
                                rand_datetime(TODAY - timedelta(days=365),
                                              TODAY)))
sections.append(("recruiter_view", ["athlete_id", "recruiter_id", "view_time"],
                 recruiter_view_rows))


# ---------------------------------------------------------------------------
# write it out, parents before children
# ---------------------------------------------------------------------------
ORDER = ["user", "analyst", "administrator", "announcement", "university",
         "recruiter", "sport", "roster", "opening", "athlete", "event",
         "personal_record", "clip", "comment", "roster_view", "recruiter_view"]
by_table = {name: (cols, rows) for name, cols, rows in sections}

parts = [
    "-- talent_scout sample data.\n"
    "--\n"
    "-- GENERATED FILE -- do not edit by hand. Regenerate with:\n"
    "--     pip install faker && python database-files/generate_seed.py\n"
    "--\n"
    "-- Runs after 01_talent_scout_ddl.sql (MySQL executes the files mounted\n"
    "-- into /docker-entrypoint-initdb.d in alphabetical order).\n"
    "\n"
    "USE talent_scout;\n",
    DEMO,
    "-- ------------------------------------------------------------------\n"
    "-- Generated data (Python Faker, seed %d)\n"
    "-- ------------------------------------------------------------------\n"
    % SEED,
]
for table in ORDER:
    cols, rows = by_table[table]
    if rows:
        parts.append(f"-- {table}: {len(rows)} generated rows\n"
                     + insert(table, cols, rows))

OUT.write_text("\n".join(parts))

totals = {
    "university": len(university_rows) + 2, "sport": len(sport_rows) + 2,
    "event": len(event_rows) + 2, "user": len(user_rows) + 9,
    "athlete": len(athlete_rows) + 2, "recruiter": len(recruiter_rows) + 2,
    "analyst": len(analyst_rows) + 2, "administrator": len(admin_rows) + 2,
    "announcement": len(announcement_rows) + 2, "roster": len(roster_rows) + 2,
    "opening": len(opening_rows) + 2, "personal_record": len(pr_rows) + 2,
    "clip": len(clip_rows) + 2, "comment": len(comment_rows) + 2,
    "roster_view": len(roster_view_rows) + 2,
    "recruiter_view": len(recruiter_view_rows) + 2,
}
print(f"wrote {OUT}")
for table, count in totals.items():
    print(f"  {table:<16} {count:>5} rows")
