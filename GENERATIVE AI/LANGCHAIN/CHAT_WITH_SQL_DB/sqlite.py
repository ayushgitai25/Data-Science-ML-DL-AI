import sqlite3

# ✅ Connect to SQLite (creates db file if not exists)
connection = sqlite3.connect("sqllite.db")
cursor = connection.cursor()

# ---------------- DROP OLD TABLES ----------------
cursor.executescript("""
DROP TABLE IF EXISTS RATING;
DROP TABLE IF EXISTS MOVIE_ACTOR;
DROP TABLE IF EXISTS ACTOR;
DROP TABLE IF EXISTS MOVIE;
DROP TABLE IF EXISTS DIRECTOR;
""")

# ---------------- CREATE TABLES ----------------
cursor.executescript("""
CREATE TABLE DIRECTOR (
    director_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    country       TEXT
);

CREATE TABLE MOVIE (
    movie_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    year          INT,
    genre         TEXT,
    director_id   INT,
    budget        REAL,
    box_office    REAL,
    FOREIGN KEY (director_id) REFERENCES DIRECTOR(director_id)
);

CREATE TABLE ACTOR (
    actor_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    birth_year    INT,
    nationality   TEXT
);

CREATE TABLE MOVIE_ACTOR (
    movie_id   INT,
    actor_id   INT,
    role       TEXT,
    PRIMARY KEY (movie_id, actor_id),
    FOREIGN KEY (movie_id) REFERENCES MOVIE(movie_id),
    FOREIGN KEY (actor_id) REFERENCES ACTOR(actor_id)
);

CREATE TABLE RATING (
    rating_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id     INT,
    user_name    TEXT,
    score        REAL,
    review       TEXT,
    FOREIGN KEY (movie_id) REFERENCES MOVIE(movie_id)
);
""")

# ---------------- INSERT DATA ----------------

# Directors
directors = [
    ('Christopher Nolan', 'UK'),
    ('Steven Spielberg', 'USA'),
    ('S.S. Rajamouli', 'India'),
    ('Hayao Miyazaki', 'Japan')
]
cursor.executemany("INSERT INTO DIRECTOR (name, country) VALUES (?, ?)", directors)

# Movies
movies = [
    ('Inception', 2010, 'Sci-Fi', 1, 160000000, 829000000),
    ('Jurassic Park', 1993, 'Adventure', 2, 63000000, 1043000000),
    ('RRR', 2022, 'Action', 3, 72000000, 155000000),
    ('Spirited Away', 2001, 'Animation', 4, 19000000, 395000000),
    ('Interstellar', 2014, 'Sci-Fi', 1, 165000000, 677000000)
]
cursor.executemany("INSERT INTO MOVIE (title, year, genre, director_id, budget, box_office) VALUES (?, ?, ?, ?, ?, ?)", movies)

# Actors
actors = [
    ('Leonardo DiCaprio', 1974, 'USA'),
    ('Sam Neill', 1947, 'New Zealand'),
    ('N. T. Rama Rao Jr.', 1983, 'India'),
    ('Emma Watson', 1990, 'UK'),
    ('Matthew McConaughey', 1969, 'USA')
]
cursor.executemany("INSERT INTO ACTOR (name, birth_year, nationality) VALUES (?, ?, ?)", actors)

# Movie ↔ Actor links
movie_actor = [
    (1, 1, 'Dom Cobb'),
    (2, 2, 'Dr. Alan Grant'),
    (3, 3, 'Komaram Bheem'),
    (4, 4, 'Chihiro (voice)'),
    (5, 5, 'Cooper'),
    (5, 1, 'Supporting role')
]
cursor.executemany("INSERT INTO MOVIE_ACTOR (movie_id, actor_id, role) VALUES (?, ?, ?)", movie_actor)

# Ratings
ratings = [
    (1, 'Alice', 9.0, 'Mind-bending and brilliant!'),
    (2, 'Bob', 8.5, 'Classic adventure film.'),
    (3, 'Ravi', 9.2, 'Epic storytelling and action.'),
    (4, 'Kenji', 9.5, 'A magical masterpiece.'),
    (5, 'Maria', 8.8, 'Visually stunning and emotional.')
]
cursor.executemany("INSERT INTO RATING (movie_id, user_name, score, review) VALUES (?, ?, ?, ?)", ratings)

# ✅ Commit all changes
connection.commit()

# ---------------- FETCH & DISPLAY ----------------
print("🎬 Directors:")
for row in cursor.execute("SELECT * FROM DIRECTOR"):
    print(row)

print("\n🎥 Movies:")
for row in cursor.execute("SELECT * FROM MOVIE"):
    print(row)

print("\n⭐ Actors:")
for row in cursor.execute("SELECT * FROM ACTOR"):
    print(row)

print("\n🎭 Movie-Actor Links:")
for row in cursor.execute("SELECT * FROM MOVIE_ACTOR"):
    print(row)

print("\n📊 Ratings:")
for row in cursor.execute("SELECT * FROM RATING"):
    print(row)

# ✅ Close connection
connection.close()
