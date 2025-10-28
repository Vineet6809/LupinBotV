import aiosqlite
import os
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger('LupinBot.database')

class AsyncDatabase:
    def __init__(self, db_name: str = "database.db"):
        self.db_name = db_name
        self._connection = None
    
    async def get_connection(self):
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_name)
            await self._connection.execute("PRAGMA foreign_keys = ON")
            # Enable row factory for dict-like access
            self._connection.row_factory = aiosqlite.Row
        return self._connection
    
    async def init_db(self):
        """Initialize the database with all required tables."""
        conn = await self.get_connection()
        
        await conn.execute("""
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
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS server_settings (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT DEFAULT '!',
                reminder_time TEXT DEFAULT '18:00',
                challenge_channel_id INTEGER,
                reminder_channel_id INTEGER
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER,
                guild_id INTEGER,
                opt_out_mentions INTEGER DEFAULT 0,
                custom_reminder_time TEXT,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                user_id INTEGER,
                guild_id INTEGER,
                log_date TEXT,
                day_number INTEGER,
                PRIMARY KEY (user_id, guild_id, log_date)
            )
        """)
        
        await conn.commit()
        logger.info("Database initialized successfully")
    
    async def close(self):
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def get_streak(self, user_id: int, guild_id: int) -> Optional[Tuple]:
        """Get a user's streak data."""
        try:
            conn = await self.get_connection()
            async with conn.execute("""
                SELECT current_streak, longest_streak, last_log_date, last_day_number
                FROM streaks WHERE user_id = ? AND guild_id = ?
            """, (user_id, guild_id)) as cursor:
                result = await cursor.fetchone()
                if result:
                    return tuple(result)
                return None
        except Exception as e:
            logger.error(f"Error getting streak: {e}")
            return None
    
    async def update_streak(self, user_id: int, guild_id: int, current_streak: int, 
                           longest_streak: int, last_day_number: int):
        """Update or insert a user's streak."""
        try:
            conn = await self.get_connection()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            await conn.execute("""
                INSERT INTO streaks (user_id, guild_id, current_streak, longest_streak, last_log_date, last_day_number)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET
                    current_streak = excluded.current_streak,
                    longest_streak = excluded.longest_streak,
                    last_log_date = excluded.last_log_date,
                    last_day_number = excluded.last_day_number
            """, (user_id, guild_id, current_streak, longest_streak, today, last_day_number))
            
            await conn.commit()
        except Exception as e:
            logger.error(f"Error updating streak: {e}")
    
    async def reset_streak(self, user_id: int, guild_id: int):
        """Reset a user's streak to 0."""
        try:
            conn = await self.get_connection()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            await conn.execute("""
                INSERT INTO streaks (user_id, guild_id, current_streak, longest_streak, last_log_date, last_day_number)
                VALUES (?, ?, 0, 0, ?, 0)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET
                    current_streak = 0,
                    last_log_date = excluded.last_log_date,
                    last_day_number = 0
            """, (user_id, guild_id, today))
            
            await conn.commit()
        except Exception as e:
            logger.error(f"Error resetting streak: {e}")
    
    async def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[Tuple]:
        """Get the leaderboard for a guild."""
        try:
            conn = await self.get_connection()
            async with conn.execute("""
                SELECT user_id, current_streak, longest_streak, last_log_date
                FROM streaks WHERE guild_id = ?
                ORDER BY current_streak DESC, longest_streak DESC
                LIMIT ?
            """, (guild_id, limit)) as cursor:
                results = await cursor.fetchall()
                return [tuple(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    async def has_logged_today(self, user_id: int, guild_id: int) -> bool:
        """Check if a user has logged today."""
        try:
            conn = await self.get_connection()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            async with conn.execute("""
                SELECT 1 FROM daily_logs 
                WHERE user_id = ? AND guild_id = ? AND log_date = ?
            """, (user_id, guild_id, today)) as cursor:
                result = await cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Error checking today's log: {e}")
            return False
    
    async def get_todays_day_number(self, user_id: int, guild_id: int) -> Optional[int]:
        """Get today's day number for a user."""
        try:
            conn = await self.get_connection()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            async with conn.execute("""
                SELECT day_number FROM daily_logs 
                WHERE user_id = ? AND guild_id = ? AND log_date = ?
            """, (user_id, guild_id, today)) as cursor:
                result = await cursor.fetchone()
                if result:
                    return result[0]
                return None
        except Exception as e:
            logger.error(f"Error getting today's day number: {e}")
            return None
    
    async def log_daily_entry(self, user_id: int, guild_id: int, day_number: int):
        """Log a daily entry for a user."""
        try:
            conn = await self.get_connection()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            await conn.execute("""
                INSERT OR REPLACE INTO daily_logs (user_id, guild_id, log_date, day_number)
                VALUES (?, ?, ?, ?)
            """, (user_id, guild_id, today, day_number))
            await conn.commit()
        except Exception as e:
            logger.error(f"Error logging daily entry: {e}")
    
    async def get_server_settings(self, guild_id: int) -> Optional[Tuple]:
        """Get server settings for a guild."""
        try:
            conn = await self.get_connection()
            async with conn.execute("""
                SELECT prefix, reminder_time, challenge_channel_id, reminder_channel_id
                FROM server_settings WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    return tuple(result)
                return None
        except Exception as e:
            logger.error(f"Error getting server settings: {e}")
            return None
    
    async def set_server_setting(self, guild_id: int, setting: str, value):
        """Set a server setting."""
        try:
            conn = await self.get_connection()
            if isinstance(value, datetime):
                value = value - timedelta(hours=5, minutes=30)
            
            await conn.execute(f"""
                INSERT INTO server_settings (guild_id, {setting})
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET {setting} = excluded.{setting}
            """, (guild_id, value))
            await conn.commit()
        except Exception as e:
            logger.error(f"Error setting server setting: {e}")
    
    async def get_user_setting(self, user_id: int, guild_id: int, setting: str):
        """Get a user setting."""
        try:
            conn = await self.get_connection()
            async with conn.execute(f"""
                SELECT {setting} FROM user_settings 
                WHERE user_id = ? AND guild_id = ?
            """, (user_id, guild_id)) as cursor:
                result = await cursor.fetchone()
                if result:
                    return result[0]
                return None
        except Exception as e:
            logger.error(f"Error getting user setting: {e}")
            return None
    
    async def set_user_setting(self, user_id: int, guild_id: int, setting: str, value):
        """Set a user setting."""
        try:
            conn = await self.get_connection()
            await conn.execute(f"""
                INSERT INTO user_settings (user_id, guild_id, {setting})
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET {setting} = excluded.{setting}
            """, (user_id, guild_id, value))
            await conn.commit()
        except Exception as e:
            logger.error(f"Error setting user setting: {e}")
    
    async def get_streak_history(self, user_id: int, guild_id: int, limit: int = 30) -> List[Tuple]:
        """Get streak history for a user."""
        try:
            conn = await self.get_connection()
            async with conn.execute("""
                SELECT log_date, day_number
                FROM daily_logs 
                WHERE user_id = ? AND guild_id = ?
                ORDER BY log_date DESC
                LIMIT ?
            """, (user_id, guild_id, limit)) as cursor:
                results = await cursor.fetchall()
                return [tuple(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting streak history: {e}")
            return []
    
    async def get_server_stats(self, guild_id: int) -> Tuple:
        """Get server-wide statistics."""
        try:
            conn = await self.get_connection()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            # Get total users with streaks
            async with conn.execute("""
                SELECT COUNT(DISTINCT user_id) FROM streaks WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                total_users = (await cursor.fetchone())[0] or 0
            
            # Get active today
            async with conn.execute("""
                SELECT COUNT(DISTINCT user_id) FROM daily_logs 
                WHERE guild_id = ? AND log_date = ?
            """, (guild_id, today)) as cursor:
                active_today = (await cursor.fetchone())[0] or 0
            
            # Get total days coded across all users
            async with conn.execute("""
                SELECT SUM(current_streak) FROM streaks WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                total_days = (await cursor.fetchone())[0] or 0
            
            # Get average streak
            async with conn.execute("""
                SELECT AVG(current_streak) FROM streaks WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                avg_streak = (await cursor.fetchone())[0] or 0
            
            return (total_users, active_today, total_days, round(avg_streak, 1) if avg_streak else 0)
        except Exception as e:
            logger.error(f"Error getting server stats: {e}")
            return (0, 0, 0, 0)
