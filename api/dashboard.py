"""Vercel Serverless API for LupinBot Dashboard"""
from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return
    
    def do_GET(self):
        """Handle GET requests."""
        # Enable CORS
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        path = self.path.strip('/')
        
        # Parse path: /api/server_stats/12345 or /api/leaderboard/12345
        parts = path.split('/')
        
        try:
            if path.startswith('api/connected_guilds'):
                # Return empty list - to be populated by bot
                response = {
                    'success': True,
                    'data': []
                }
            
            elif path.startswith('api/server_stats/'):
                guild_id = parts[-1]
                # Connect to your database or return placeholder
                response = {
                    'success': True,
                    'data': {
                        'total_users': 0,
                        'active_today': 0,
                        'total_days': 0,
                        'avg_streak': 0,
                        'activity_rate': 0
                    }
                }
            
            elif path.startswith('api/leaderboard/'):
                guild_id = parts[-1]
                response = {
                    'success': True,
                    'data': []
                }
            
            else:
                response = {
                    'success': False,
                    'error': 'Invalid API endpoint'
                }
        
        except Exception as e:
            response = {
                'success': False,
                'error': str(e)
            }
        
        self.wfile.write(json.dumps(response).encode())
        return
