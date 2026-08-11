DROP DATABASE IF EXISTS talent_scout;
CREATE DATABASE talent_scout;
USE talent_scout;

DROP TABLE IF EXISTS user;
CREATE TABLE user
(
    user_id    INT AUTO_INCREMENT,
    first_name VARCHAR(30) NOT NULL,
    last_name  VARCHAR(30) NOT NULL,
    email      VARCHAR(80) NOT NULL UNIQUE,
    phone      CHAR(10),
    PRIMARY KEY (user_id)
);

-- Analyst
DROP TABLE IF EXISTS analyst;
CREATE TABLE analyst
(
    user_id INT,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES user (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Administrator
DROP TABLE IF EXISTS administrator;
CREATE TABLE administrator
(
    user_id INT,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES user (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS announcement;
CREATE TABLE announcement
(
    announcement_id INT AUTO_INCREMENT,
    user_id         INT,
    title           TINYTEXT NOT NULL,
    body            MEDIUMTEXT,
    scheduled_start DATETIME NOT NULL,
    scheduled_end   DATETIME NOT NULL,
    PRIMARY KEY (announcement_id),
    FOREIGN KEY (user_id) REFERENCES administrator (user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- Recruiter
DROP TABLE IF EXISTS university;
CREATE TABLE university
(
    university_id INT AUTO_INCREMENT,
    website_url   VARCHAR(80),
    name          VARCHAR(50) NOT NULL UNIQUE,
    PRIMARY KEY (university_id)
);

DROP TABLE IF EXISTS recruiter;
CREATE TABLE recruiter
(
    user_id       INT,
    university_id INT,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES user (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (university_id) REFERENCES university (university_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

DROP TABLE IF EXISTS sport;
CREATE TABLE sport
(
    sport_id INT AUTO_INCREMENT,
    name     VARCHAR(80) NOT NULL UNIQUE,
    PRIMARY KEY (sport_id)
);

DROP TABLE IF EXISTS roster;
CREATE TABLE roster
(
    roster_id  INT AUTO_INCREMENT,
    user_id    INT,
    sport_id   INT,
    division   TINYTEXT,
    start_date DATE        NOT NULL,
    end_date   DATE        NOT NULL,
    gender     CHAR(1)     NOT NULL,
    team_name  VARCHAR(30) NOT NULL,
    PRIMARY KEY (roster_id),
    FOREIGN KEY (user_id) REFERENCES recruiter (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (sport_id) REFERENCES sport (sport_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

DROP TABLE IF EXISTS opening;
CREATE TABLE opening
(
    opening_number     INT,
    roster_id          INT,
    required_gpa       DECIMAL(3, 2),
    required_height_cm INT,
    position           VARCHAR(20),
    grad_year          YEAR,
    PRIMARY KEY (opening_number, roster_id),
    FOREIGN KEY (roster_id) REFERENCES roster (roster_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Athlete
DROP TABLE IF EXISTS athlete;
CREATE TABLE athlete
(
    user_id            INT,
    graduation_year    YEAR          NOT NULL,
    dob                DATE          NOT NULL,
    gender             CHAR(1)       NOT NULL,
    height_cm          INT           NOT NULL,
    weight_kg          INT           NOT NULL,
    gpa                DECIMAL(3, 2) NOT NULL,
    recruitment_status VARCHAR(10),
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES user (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS event;
CREATE TABLE event
(
    event_id INT AUTO_INCREMENT,
    name     VARCHAR(30) NOT NULL UNIQUE,
    PRIMARY KEY (event_id)
);

DROP TABLE IF EXISTS personal_record;
CREATE TABLE personal_record
(
    user_id  INT,
    date     DATE,
    event_id INT,
    time     TIME(2),
    score    DOUBLE,
    PRIMARY KEY (user_id, date, event_id),
    FOREIGN KEY (user_id) REFERENCES athlete (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES event (event_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

DROP TABLE IF EXISTS clip;
CREATE TABLE clip
(
    clip_id   INT AUTO_INCREMENT,
    user_id   INT,
    posted_at DATE     NOT NULL,
    caption   TINYTEXT NOT NULL,
    PRIMARY KEY (clip_id),
    FOREIGN KEY (user_id) REFERENCES athlete (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS comment;
CREATE TABLE comment
(
    comment_id INT AUTO_INCREMENT,
    clip_id    INT,
    user_id    INT,
    posted_at  DATE     NOT NULL,
    content    TINYTEXT NOT NULL,
    PRIMARY KEY (comment_id),
    FOREIGN KEY (clip_id) REFERENCES clip (clip_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user (user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- View
DROP TABLE IF EXISTS roster_view;
CREATE TABLE roster_view
(
    user_id   INT,
    roster_id INT,
    view_time DATETIME NOT NULL,
    PRIMARY KEY (user_id, roster_id),
    FOREIGN KEY (user_id) REFERENCES athlete (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (roster_id) REFERENCES roster (roster_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS recruiter_view;
CREATE TABLE recruiter_view
(
    athlete_id   INT,
    recruiter_id INT,
    view_time    DATETIME NOT NULL,
    PRIMARY KEY (athlete_id, recruiter_id),
    FOREIGN KEY (athlete_id) REFERENCES athlete (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (recruiter_id) REFERENCES recruiter (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


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

INSERT INTO clip (user_id, posted_at, caption)
VALUES (1, '2028-08-01', 'Super cool clip'),
       (1, '2028-08-02', 'Other cool clip');

INSERT INTO comment (clip_id, user_id, posted_at, content)
VALUES (1, 2, '2028-07-01', 'Good stuff'),
       (1, 2, '2028-07-01', 'SO good I commented again');

INSERT INTO roster_view (user_id, roster_id, view_time)
VALUES (1, 1, '2028-08-02 10:15:00'),
       (5, 2, '2028-08-03 10:15:00');

INSERT INTO recruiter_view (athlete_id, recruiter_id, view_time)
VALUES (1, 2, '2028-08-02 09:00:00'),
       (5, 6, '2028-08-03 09:00:00');
