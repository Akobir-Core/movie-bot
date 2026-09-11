import sqlite3
import threading
from datetime import datetime, timezone

class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init()

    def _init(self):
        with self.lock, self.conn:
            self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT NOT NULL,
                joined_at TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                search_count INTEGER DEFAULT 0,
                views_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS movies(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                genre TEXT DEFAULT '',
                year TEXT DEFAULT '',
                country TEXT DEFAULT '',
                quality TEXT DEFAULT '',
                rating REAL DEFAULT 0,
                poster_file_id TEXT,
                video_file_id TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS channels(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                username TEXT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS favorites(
                user_id INTEGER NOT NULL,
                movie_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(user_id,movie_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(movie_id) REFERENCES movies(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS movie_views(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                movie_id INTEGER NOT NULL,
                viewed_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS searches(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_movies_code ON movies(code);
            CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title);
            CREATE INDEX IF NOT EXISTS idx_movies_genre ON movies(genre);
            CREATE INDEX IF NOT EXISTS idx_views_movie ON movie_views(movie_id);
            """)

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat()

    def upsert_user(self, user):
        now = self.now()
        with self.lock, self.conn:
            self.conn.execute("""
            INSERT INTO users(id,username,full_name,joined_at,last_seen)
            VALUES(?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
            username=excluded.username, full_name=excluded.full_name, last_seen=excluded.last_seen
            """, (user.id, user.username, user.full_name, now, now))

    def get_user(self, user_id):
        return self.conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    def all_user_ids(self):
        return [r["id"] for r in self.conn.execute("SELECT id FROM users").fetchall()]

    def add_movie(self, data):
        with self.lock, self.conn:
            cur = self.conn.execute("""
            INSERT INTO movies(code,title,description,genre,year,country,quality,rating,poster_file_id,video_file_id,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """, (
                data["code"], data["title"], data["description"], data["genre"],
                data["year"], data["country"], data["quality"], data.get("rating", 0),
                data.get("poster_file_id"), data["video_file_id"], self.now()
            ))
            return cur.lastrowid

    def get_movie(self, code):
        return self.conn.execute("SELECT * FROM movies WHERE code=?", (code.strip(),)).fetchone()

    def delete_movie(self, code):
        with self.lock, self.conn:
            cur = self.conn.execute("DELETE FROM movies WHERE code=?", (code.strip(),))
            return cur.rowcount > 0

    def update_movie(self, movie_id, data):
        fields = ["title","description","genre","year","country","quality","rating"]
        values = [data.get(x, "") for x in fields]
        values.append(movie_id)
        with self.lock, self.conn:
            self.conn.execute(f"UPDATE movies SET {','.join(x+'=?' for x in fields)} WHERE id=?", values)

    def search_movies(self, query, limit=20):
        q = f"%{query.strip()}%"
        return self.conn.execute("""
        SELECT * FROM movies
        WHERE title LIKE ? OR code LIKE ? OR genre LIKE ?
        ORDER BY views DESC, id DESC LIMIT ?
        """, (q,q,q,limit)).fetchall()

    def genre_movies(self, genre, limit=20):
        return self.conn.execute("""
        SELECT * FROM movies WHERE LOWER(genre) LIKE LOWER(?)
        ORDER BY views DESC,id DESC LIMIT ?
        """, (f"%{genre}%",limit)).fetchall()

    def top_movies(self, limit=10):
        return self.conn.execute("SELECT * FROM movies ORDER BY views DESC,id DESC LIMIT ?", (limit,)).fetchall()

    def new_movies(self, limit=10):
        return self.conn.execute("SELECT * FROM movies ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    def all_movies(self, limit=100):
        return self.conn.execute("SELECT * FROM movies ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    def register_view(self, user_id, movie_id):
        with self.lock, self.conn:
            now = self.now()
            self.conn.execute("INSERT INTO movie_views(user_id,movie_id,viewed_at) VALUES(?,?,?)",
                              (user_id,movie_id,now))
            self.conn.execute("UPDATE movies SET views=views+1 WHERE id=?", (movie_id,))
            self.conn.execute("UPDATE users SET views_count=views_count+1,last_seen=? WHERE id=?",
                              (now,user_id))

    def register_search(self, user_id, query):
        with self.lock, self.conn:
            self.conn.execute("INSERT INTO searches(user_id,query,created_at) VALUES(?,?,?)",
                              (user_id,query,self.now()))
            self.conn.execute("UPDATE users SET search_count=search_count+1,last_seen=? WHERE id=?",
                              (self.now(),user_id))

    def toggle_favorite(self, user_id, movie_id):
        with self.lock, self.conn:
            row = self.conn.execute(
                "SELECT 1 FROM favorites WHERE user_id=? AND movie_id=?", (user_id,movie_id)
            ).fetchone()
            if row:
                self.conn.execute("DELETE FROM favorites WHERE user_id=? AND movie_id=?", (user_id,movie_id))
                return False
            self.conn.execute("INSERT INTO favorites(user_id,movie_id,created_at) VALUES(?,?,?)",
                              (user_id,movie_id,self.now()))
            return True

    def is_favorite(self,user_id,movie_id):
        return self.conn.execute("SELECT 1 FROM favorites WHERE user_id=? AND movie_id=?",
                                 (user_id,movie_id)).fetchone() is not None

    def favorites(self,user_id):
        return self.conn.execute("""
        SELECT m.* FROM movies m JOIN favorites f ON f.movie_id=m.id
        WHERE f.user_id=? ORDER BY f.created_at DESC
        """,(user_id,)).fetchall()

    def add_channel(self, channel_id, username, title):
        with self.lock, self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO channels(channel_id,username,title,created_at) VALUES(?,?,?,?)",
                (str(channel_id),username,title,self.now())
            )

    def channels(self):
        return self.conn.execute("SELECT * FROM channels ORDER BY id").fetchall()

    def delete_channel(self, channel_id):
        with self.lock, self.conn:
            cur=self.conn.execute("DELETE FROM channels WHERE channel_id=?", (str(channel_id),))
            return cur.rowcount > 0

    def stats(self):
        q=lambda sql: self.conn.execute(sql).fetchone()[0]
        return {
            "users":q("SELECT COUNT(*) FROM users"),
            "movies":q("SELECT COUNT(*) FROM movies"),
            "views":q("SELECT COALESCE(SUM(views),0) FROM movies"),
            "searches":q("SELECT COUNT(*) FROM searches"),
            "channels":q("SELECT COUNT(*) FROM channels"),
            "active":q("SELECT COUNT(*) FROM users WHERE last_seen >= datetime('now','-7 days')")
        }

    def close(self):
        self.conn.close()
