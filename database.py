import sqlite3
import os
from datetime import datetime,timedelta
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
        value = value.timedelta(hours=5, minutes=30) if isinstance(value, datetime) else value
        cursor.execute(f"""
            INSERT INTO server_settings (guild_id, {setting})
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET {setting} = excluded.{setting}
        """, (guild_id, value)
        
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
