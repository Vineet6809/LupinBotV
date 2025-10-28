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
        value = value - timedelta(hours=5, minutes=30) if isinstance(value, datetime) else value

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
