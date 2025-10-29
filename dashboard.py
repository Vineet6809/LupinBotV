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

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

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
    """Get leaderboard data using database-backed user info only (no Discord API calls here)."""
    try:
        leaderboard = db.get_leaderboard(guild_id, limit=10)
        data = []
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Ensure users table exists (also created in database.init_db)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                avatar_url TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        for user_id, current_streak, longest_streak, last_log_date in leaderboard:
            user_id_int = int(user_id)
            user_info = {
                'user_id': str(user_id_int),
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'last_log_date': last_log_date,
                'username': f'User {user_id_int}',
                'display_name': f'User {user_id_int}',
                'avatar': None
            }
            
            cursor.execute("SELECT username, display_name, avatar_url FROM users WHERE user_id = ?", (user_id_int,))
            user_row = cursor.fetchone()
            if user_row:
                username, display_name, avatar_url = user_row
                user_info['username'] = username or user_info['username']
                user_info['display_name'] = display_name or user_info['display_name']
                user_info['avatar'] = avatar_url
            
            data.append(user_info)
        
        conn.close()
        
        return jsonify({'success': True, 'data': data})
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
        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, day_number
            FROM daily_logs
            WHERE guild_id = ? AND log_date = ?
            ORDER BY user_id DESC
            LIMIT 50
        """, (guild_id, today))
        
        activity = []
        for user_id, day_number in cursor.fetchall():
            activity.append({'user_id': str(user_id), 'day_number': day_number})
        
        conn.close()
        
        return jsonify({'success': True, 'data': activity})
    except Exception as e:
        logger.error(f'Error getting recent activity: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/connected_guilds')
def connected_guilds():
    """Get list of all connected guilds (guilds that have data)."""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT guild_id
            FROM streaks
            ORDER BY guild_id
        """)
        
        guilds = []
        for row in cursor.fetchall():
            guild_id_str = str(row[0])
            guilds.append({'guild_id': guild_id_str, 'name': f'Guild {guild_id_str}'})
        
        conn.close()
        
        return jsonify({'success': True, 'data': guilds})
    except Exception as e:
        logger.error(f'Error getting connected guilds: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

def set_bot_instance(bot_instance):
    """Set the Discord bot instance for fetching user data (not used in Flask endpoints)."""
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
