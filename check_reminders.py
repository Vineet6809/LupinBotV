#!/usr/bin/env python3
"""
Test script to verify reminder configuration and database queries.
Run this to check if your reminder setup will work.
"""

import sqlite3
from datetime import datetime

def check_reminder_config():
    """Check the current reminder configuration in the database."""
    print("=" * 60)
    print("REMINDER CONFIGURATION CHECKER")
    print("=" * 60)
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Check server settings
    print("\n1. Checking server_settings table...")
    cursor.execute("""
        SELECT guild_id, reminder_time, reminder_channel_id 
        FROM server_settings
    """)
    
    all_settings = cursor.fetchall()
    if not all_settings:
        print("   ❌ No server settings found in database")
        conn.close()
        return
    
    print(f"   ✅ Found {len(all_settings)} server(s) with settings")
    
    for guild_id, reminder_time, reminder_channel_id in all_settings:
        print(f"\n   Guild ID: {guild_id}")
        print(f"   - Reminder Time (UTC): {reminder_time if reminder_time else '❌ NOT SET'}")
        print(f"   - Reminder Channel ID: {reminder_channel_id if reminder_channel_id else '❌ NOT SET'}")
        
        # Check if this guild would be included in reminders
        cursor.execute("""
            SELECT guild_id, reminder_time, reminder_channel_id
            FROM server_settings
            WHERE guild_id = ? AND reminder_time IS NOT NULL AND reminder_channel_id IS NOT NULL
        """, (guild_id,))
        
        result = cursor.fetchone()
        if result:
            print(f"   ✅ STATUS: This guild WILL receive reminders")
        else:
            print(f"   ❌ STATUS: This guild WILL NOT receive reminders")
            if not reminder_time:
                print(f"      → Missing: Reminder Time - Use /setreminder")
            if not reminder_channel_id:
                print(f"      → Missing: Reminder Channel - Use /setreminderchannel")
    
    # Check active streaks
    print("\n2. Checking active streaks...")
    cursor.execute("""
        SELECT COUNT(*) FROM streaks WHERE current_streak > 0
    """)
    active_count = cursor.fetchone()[0]
    print(f"   ✅ {active_count} user(s) have active streaks")
    
    # Check who would be reminded today
    print("\n3. Checking users who need reminders today...")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    for guild_id, _, _ in all_settings:
        cursor.execute("""
            SELECT s.user_id
            FROM streaks s
            LEFT JOIN daily_logs d ON s.user_id = d.user_id AND s.guild_id = d.guild_id AND d.log_date = ?
            WHERE s.guild_id = ? AND s.current_streak > 0 AND d.log_date IS NULL
        """, (today, guild_id))
        
        users_to_remind = cursor.fetchall()
        print(f"   Guild {guild_id}: {len(users_to_remind)} user(s) would be reminded")
        
        if users_to_remind:
            print(f"      User IDs: {', '.join([str(u[0]) for u in users_to_remind[:5]])}")
            if len(users_to_remind) > 5:
                print(f"      ... and {len(users_to_remind) - 5} more")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    # Final check
    cursor.execute("""
        SELECT COUNT(*) FROM server_settings
        WHERE reminder_time IS NOT NULL AND reminder_channel_id IS NOT NULL
    """)
    configured_count = cursor.fetchone()[0]
    
    if configured_count > 0:
        print(f"✅ {configured_count} server(s) properly configured for reminders")
        print("\nReminders WILL be sent when the scheduled time arrives!")
    else:
        print("❌ NO servers properly configured for reminders")
        print("\nTO FIX:")
        print("1. Run: /setreminder time:\"HH:MM AM/PM\"")
        print("2. Run: /setreminderchannel channel:#your-channel")
        print("3. Run: /checkreminder (to verify)")
    
    print("=" * 60)
    conn.close()

if __name__ == "__main__":
    try:
        check_reminder_config()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure database.db exists in the current directory.")
