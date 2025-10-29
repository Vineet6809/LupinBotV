import sqlite3
import os
from datetime import datetime , timedelta
from typing import Optional, List, Tuple

class Database:
    def __init__(self, db_name: str = "database.db"):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS streaks (
                user_id INTEGER,
                guild_id INTEGER,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_log_date TEXT,
                last_day_number INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS server_settings (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT DEFAULT '!',
                reminder_time TEXT DEFAULT '18:00',
                challenge_channel_id INTEGER,
                reminder_channel_id INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER,
                guild_id INTEGER,
                opt_out_mentions INTEGER DEFAULT 0,
                custom_reminder_time TEXT,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                user_id INTEGER,
                guild_id INTEGER,
                log_date TEXT,
                day_number INTEGER,
                PRIMARY KEY (user_id, guild_id, log_date)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS streak_freezes (
                user_id INTEGER,
                guild_id INTEGER,
                freeze_count INTEGER DEFAULT 1,
                last_freeze_date TEXT,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        
        # Users table for dashboard/user info caching
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                avatar_url TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Bot meta/state tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_meta (
                guild_id INTEGER PRIMARY KEY,
                last_seen_at TEXT,
                last_week_sent TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_channel_state (
                guild_id INTEGER,
                channel_id INTEGER,
                last_processed_id INTEGER,
                PRIMARY KEY (guild_id, channel_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_streak(self, user_id: int, guild_id: int) -> Optional[Tuple]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT current_streak, longest_streak, last_log_date, last_day_number
            FROM streaks WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def update_streak(self, user_id: int, guild_id: int, current_streak: int, 
                     longest_streak: int, last_day_number: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        cursor.execute("""
            INSERT INTO streaks (user_id, guild_id, current_streak, longest_streak, last_log_date, last_day_number)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, guild_id) DO UPDATE SET
                current_streak = excluded.current_streak,
                longest_streak = excluded.longest_streak,
                last_log_date = excluded.last_log_date,
                last_day_number = excluded.last_day_number
        """, (user_id, guild_id, current_streak, longest_streak, today, last_day_number))
        
        conn.commit()
        conn.close()
    
    def update_streak_with_date(self, user_id: int, guild_id: int, current_streak: int,
                                longest_streak: int, last_day_number: int, last_date_str: str):
        """Update streak while explicitly setting last_log_date to provided date (YYYY-MM-DD)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO streaks (user_id, guild_id, current_streak, longest_streak, last_log_date, last_day_number)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, guild_id) DO UPDATE SET
                current_streak = excluded.current_streak,
                longest_streak = excluded.longest_streak,
                last_log_date = excluded.last_log_date,
                last_day_number = excluded.last_day_number
        """, (user_id, guild_id, current_streak, longest_streak, last_date_str, last_day_number))
        conn.commit()
        conn.close()
    
    def reset_streak(self, user_id: int, guild_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        cursor.execute("""
            INSERT INTO streaks (user_id, guild_id, current_streak, longest_streak, last_log_date, last_day_number)
            VALUES (?, ?, 0, 0, ?, 0)
            ON CONFLICT(user_id, guild_id) DO UPDATE SET
                current_streak = 0,
                last_log_date = excluded.last_log_date,
                last_day_number = 0
        """, (user_id, guild_id, today))
        
        conn.commit()
        conn.close()
    
    def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[Tuple]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, current_streak, longest_streak, last_log_date
            FROM streaks WHERE guild_id = ?
            ORDER BY current_streak DESC, longest_streak DESC
            LIMIT ?
        """, (guild_id, limit))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def has_logged_today(self, user_id: int, guild_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.utcnow().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT 1 FROM daily_logs 
            WHERE user_id = ? AND guild_id = ? AND log_date = ?
        """, (user_id, guild_id, today))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def get_todays_day_number(self, user_id: int, guild_id: int) -> Optional[int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.utcnow().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT day_number FROM daily_logs 
            WHERE user_id = ? AND guild_id = ? AND log_date = ?
        """, (user_id, guild_id, today))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def log_daily_entry(self, user_id: int, guild_id: int, day_number: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.utcnow().strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT OR REPLACE INTO daily_logs (user_id, guild_id, log_date, day_number)
            VALUES (?, ?, ?, ?)
        """, (user_id, guild_id, today, day_number))
        conn.commit()
        conn.close()
    
    def log_specific_day(self, user_id: int, guild_id: int, date: str, day_number: int):
        """Log a specific day in the past for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO daily_logs (user_id, guild_id, log_date, day_number)
            VALUES (?, ?, ?, ?)
        ''', (user_id, guild_id, date, day_number))
        conn.commit()
        conn.close()
    
    def get_server_settings(self, guild_id: int) -> Optional[Tuple]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT prefix, reminder_time, challenge_channel_id, reminder_channel_id
            FROM server_settings WHERE guild_id = ?
        """, (guild_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def set_server_setting(self, guild_id: int, setting: str, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO server_settings (guild_id, {setting})
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET {setting} = excluded.{setting}
        """, (guild_id, value))
        
        conn.commit()
        conn.close()
    
    def get_user_setting(self, user_id: int, guild_id: int, setting: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT {setting} FROM user_settings 
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def set_user_setting(self, user_id: int, guild_id: int, setting: str, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO user_settings (user_id, guild_id, {setting})
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, guild_id) DO UPDATE SET {setting} = excluded.{setting}
        """, (user_id, guild_id, value))
        conn.commit()
        conn.close()
    
    def get_streak_history(self, user_id: int, guild_id: int, limit: int = 30) -> List[Tuple]:
        """Get streak history for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT log_date, day_number
            FROM daily_logs 
            WHERE user_id = ? AND guild_id = ?
            ORDER BY log_date DESC
            LIMIT ?
        """, (user_id, guild_id, limit))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_server_stats(self, guild_id: int) -> Tuple:
        """Get server-wide statistics."""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Get total users with streaks
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM streaks WHERE guild_id = ?
        """, (guild_id,))
        total_users = cursor.fetchone()[0] or 0
        
        # Get active today
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM daily_logs 
            WHERE guild_id = ? AND log_date = ?
        """, (guild_id, today))
        active_today = cursor.fetchone()[0] or 0
        
        # Get total days coded across all users
        cursor.execute("""
            SELECT SUM(current_streak) FROM streaks WHERE guild_id = ?
        """, (guild_id,))
        total_days = cursor.fetchone()[0] or 0
        
        # Get average streak
        cursor.execute("""
            SELECT AVG(current_streak) FROM streaks WHERE guild_id = ?
        """, (guild_id,))
        avg_streak = cursor.fetchone()[0] or 0
        
        conn.close()
        return (total_users, active_today, total_days, round(avg_streak, 1) if avg_streak else 0)

    def get_all_reminder_guilds(self) -> List[Tuple]:
        """Gets all guilds that have a reminder time and channel set."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT guild_id, reminder_time, reminder_channel_id
            FROM server_settings
            WHERE reminder_time IS NOT NULL AND reminder_channel_id IS NOT NULL
        """)
        results = cursor.fetchall()
        conn.close()
        return results

    def get_users_to_remind(self, guild_id: int, today_str: str) -> List[int]:
        """Gets users in a guild who have an active streak but haven't logged today."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.user_id
            FROM streaks s
            LEFT JOIN daily_logs d ON s.user_id = d.user_id AND s.guild_id = d.guild_id AND d.log_date = ?
            WHERE s.guild_id = ? AND s.current_streak > 0 AND d.log_date IS NULL
        """, (today_str, guild_id))
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_streak_freeze(self, user_id: int, guild_id: int) -> int:
        """Get user's freeze count (like Duolingo streak freeze)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT freeze_count FROM streak_freezes WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 1
    
    def use_streak_freeze(self, user_id: int, guild_id: int) -> bool:
        """Use a streak freeze. Returns True if successful."""
        freeze_count = self.get_streak_freeze(user_id, guild_id)
        if freeze_count > 0:
            conn = self.get_connection()
            cursor = conn.cursor()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT INTO streak_freezes (user_id, guild_id, freeze_count, last_freeze_date)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET
                    freeze_count = freeze_count - 1,
                    last_freeze_date = ?
            """, (user_id, guild_id, freeze_count - 1, today, today))
            conn.commit()
            conn.close()
            return True
        return False
    
    def add_streak_freeze(self, user_id: int, guild_id: int, amount: int = 1):
        """Add freezes to user's account."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # First check if exists
        cursor.execute("""
            SELECT freeze_count FROM streak_freezes WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        result = cursor.fetchone()
        
        if result:
            new_count = result[0] + amount
            cursor.execute("""
                UPDATE streak_freezes SET freeze_count = ? WHERE user_id = ? AND guild_id = ?
            """, (new_count, user_id, guild_id))
        else:
            cursor.execute("""
                INSERT INTO streak_freezes (user_id, guild_id, freeze_count)
                VALUES (?, ?, ?)
            """, (user_id, guild_id, amount))
        
        conn.commit()
        conn.close()

    def clear_user_logs(self, user_id: int, guild_id: int):
        """Delete all of a user's daily logs."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM daily_logs 
            WHERE user_id = ? AND guild_id = ?
        ''', (user_id, guild_id))
        conn.commit()
        conn.close()

    # Users table helpers
    def upsert_user(self, user_id: int, username: Optional[str], display_name: Optional[str], avatar_url: Optional[str]):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (user_id, username, display_name, avatar_url, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                display_name = excluded.display_name,
                avatar_url = excluded.avatar_url,
                last_updated = CURRENT_TIMESTAMP
            """,
            (user_id, username, display_name, avatar_url)
        )
        conn.commit()
        conn.close()

    # Bot meta helpers
    def get_last_seen(self, guild_id: int) -> Optional[str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT last_seen_at FROM bot_meta WHERE guild_id = ?", (guild_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def set_last_seen(self, guild_id: int, dt_str: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO bot_meta (guild_id, last_seen_at)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET last_seen_at = excluded.last_seen_at
            """,
            (guild_id, dt_str)
        )
        conn.commit()
        conn.close()

    def get_last_week_sent(self, guild_id: int) -> Optional[str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT last_week_sent FROM bot_meta WHERE guild_id = ?", (guild_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def set_last_week_sent(self, guild_id: int, week_key: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO bot_meta (guild_id, last_week_sent)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET last_week_sent = excluded.last_week_sent
            """,
            (guild_id, week_key)
        )
        conn.commit()
        conn.close()

    # Channel state helpers
    def get_last_processed(self, guild_id: int, channel_id: int) -> Optional[int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT last_processed_id FROM bot_channel_state WHERE guild_id = ? AND channel_id = ?", (guild_id, channel_id))
        row = cursor.fetchone()
        conn.close()
        return int(row[0]) if row and row[0] is not None else None

    def set_last_processed(self, guild_id: int, channel_id: int, last_processed_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO bot_channel_state (guild_id, channel_id, last_processed_id)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, channel_id) DO UPDATE SET last_processed_id = excluded.last_processed_id
            """,
            (guild_id, channel_id, last_processed_id)
        )
        conn.commit()
        conn.close()
