"""Web Dashboard for LupinBot"""
from flask import Flask, render_template, jsonify, request
from database import Database
import logging
from datetime import datetime

logger = logging.getLogger('LupinBot.dashboard')
app = Flask(__name__)
db = Database()
bot = None  # Bot instance will be set from main.py

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/server_stats/<int:guild_id>')
def server_stats(guild_id):
    """Get server statistics."""
    try:
        stats = db.get_server_stats(guild_id)
        total_users, active_today, total_days, avg_streak = stats
        
        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'active_today': active_today,
                'total_days': total_days,
                'avg_streak': avg_streak,
                'activity_rate': round((active_today / total_users * 100), 1) if total_users > 0 else 0
            }
        })
    except Exception as e:
        logger.error(f'Error getting server stats: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leaderboard/<int:guild_id>')
def leaderboard_api(guild_id):
    """Get leaderboard data with Discord user information from daily-code channel."""
    try:
        leaderboard = db.get_leaderboard(guild_id, limit=10)
        
        data = []
        # Cache for user lookups to avoid repeated API calls
        user_cache = {}
        
        # Try to get user info from daily-code channel if bot is available
        if bot and hasattr(bot, 'is_ready') and bot.is_ready():
            try:
                # Find the daily-code channel
                for guild in bot.guilds:
                    if guild.id == guild_id:
                        # Look for channel named 'daily-code' or similar
                        for channel in guild.text_channels:
                            if 'daily-code' in channel.name.lower() or 'code' in channel.name.lower():
                                logger.info(f'Found daily-code channel: {channel.name}')
                                # Get recent members who posted in this channel
                                try:
                                    import asyncio
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    # Fetch channel history for user info
                                    async def get_users():
                                        async for message in channel.history(limit=100):
                                            if message.author and message.author.id not in user_cache:
                                                user_cache[message.author.id] = {
                                                    'username': message.author.name,
                                                    'display_name': message.author.display_name or message.author.name,
                                                    'avatar': str(message.author.display_avatar.url) if message.author.display_avatar else None
                                                }
                                    loop.run_until_complete(get_users())
                                    loop.close()
                                except Exception as e:
                                    logger.debug(f"Could not fetch channel history: {e}")
                                break
            except Exception as e:
                logger.debug(f"Error accessing guild: {e}")
        
        # Get user info from database
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Create users table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                avatar_url TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Build leaderboard data
        for user_id, current_streak, longest_streak, last_log_date in leaderboard:
            user_id_int = int(user_id)
            user_info = {
                'user_id': str(user_id),
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'last_log_date': last_log_date,
                'username': f'User {user_id}',
                'display_name': f'User {user_id}',
                'avatar': None
            }
            
            # Try to get user info from database first
            cursor.execute("SELECT username, display_name, avatar_url FROM users WHERE user_id = ?", (user_id_int,))
            user_row = cursor.fetchone()
            
            if user_row:
                username, display_name, avatar_url = user_row
                user_info['username'] = username or f'User {user_id}'
                user_info['display_name'] = display_name or username or f'User {user_id}'
                user_info['avatar'] = avatar_url
                logger.info(f"Found user {user_id} in database: {username}")
            else:
                # Use cached user info if available
                if user_id_int in user_cache:
                    cached = user_cache[user_id_int]
                    user_info['username'] = cached['username']
                    user_info['display_name'] = cached['display_name']
                    user_info['avatar'] = cached['avatar']
                elif bot and hasattr(bot, 'is_ready') and bot.is_ready():
                    # Try direct user lookup
                    try:
                        logger.info(f"Bot is ready, fetching user {user_id}")
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        user = loop.run_until_complete(bot.fetch_user(user_id_int))
                        if user:
                            user_info['username'] = user.name
                            user_info['display_name'] = user.display_name or user.name
                            user_info['avatar'] = str(user.display_avatar.url) if user.display_avatar else None
                            logger.info(f"Fetched user {user_id}: {user.name}")
                        loop.close()
                    except Exception as e:
                        logger.error(f"Could not fetch user {user_id}: {e}")
                else:
                    logger.info(f"Bot not ready or not available. Bot: {bot}, Ready: {bot.is_ready() if bot else 'No bot'}")
            
            data.append(user_info)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f'Error getting leaderboard: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user_stats/<int:user_id>/<int:guild_id>')
def user_stats(user_id, guild_id):
    """Get user statistics."""
    try:
        streak_data = db.get_streak(user_id, guild_id)
        history = db.get_streak_history(user_id, guild_id, limit=30)
        
        if not streak_data:
            return jsonify({'success': False, 'error': 'No stats found for this user'}), 404
        
        current_streak, longest_streak, last_log_date, last_day_number = streak_data
        
        return jsonify({
            'success': True,
            'data': {
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'last_log_date': last_log_date,
                'last_day_number': last_day_number,
                'history': [
                    {'log_date': log_date, 'day_number': day_number}
                    for log_date, day_number in history
                ]
            }
        })
    except Exception as e:
        logger.error(f'Error getting user stats: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recent_activity/<int:guild_id>')
def recent_activity(guild_id):
    """Get recent activity."""
    try:
        # Get current time
        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get today's activity
        cursor.execute("""
            SELECT user_id, day_number
            FROM daily_logs
            WHERE guild_id = ? AND log_date = ?
            ORDER BY user_id DESC
            LIMIT 50
        """, (guild_id, today))
        
        activity = []
        for user_id, day_number in cursor.fetchall():
            activity.append({
                'user_id': str(user_id),
                'day_number': day_number
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': activity
        })
    except Exception as e:
        logger.error(f'Error getting recent activity: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/connected_guilds')
def connected_guilds():
    """Get list of all connected guilds (guilds that have data)."""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get all unique guild IDs from streaks table
        cursor.execute("""
            SELECT DISTINCT guild_id
            FROM streaks
            ORDER BY guild_id
        """)
        
        guilds = []
        for row in cursor.fetchall():
            # Convert guild_id to string to avoid JavaScript number precision loss
            guild_id_str = str(row[0])
            guilds.append({
                'guild_id': guild_id_str,
                'name': f'Guild {guild_id_str}'
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': guilds
        })
    except Exception as e:
        logger.error(f'Error getting connected guilds: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

def set_bot_instance(bot_instance):
    """Set the Discord bot instance for fetching user data."""
    global bot
    bot = bot_instance
    logger.info('Bot instance set for dashboard')

def run_dashboard(host='localhost', port=5000, debug=False):
    """Run the dashboard server."""
    logger.info(f'Starting LupinBot Dashboard on http://{host}:{port}')
    logger.info('Make sure your Discord bot is running to access the data!')
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    run_dashboard(port=port, debug=True)

