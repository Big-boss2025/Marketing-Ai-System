import os
import sys
from datetime import datetime, timedelta

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models.base import db
from routes.user import user_bp
from routes.admin import admin_bp
from routes.ai_assistant import ai_assistant_bp
from routes.payment import payment_bp
from routes.social_media import social_media_bp
from routes.performance import performance_bp
from routes.referral import referral_bp
from routes.credit_schedule import credit_schedule_bp
from routes.reports import reports_bp
from routes.webhooks import webhooks_bp
from routes.oauth import oauth_bp
from routes.support import support_bp
from routes.marketing_strategies import marketing_strategies_bp
from routes.video_generation import video_generation_bp
from routes.prompt_analyzer import prompt_analyzer_bp

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Basic Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'marketing-automation-system-secret-key-2024')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-marketing-automation-2024')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Database Configuration
    database_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{database_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # CORS Configuration - Allow all origins for development
    CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # JWT Configuration
    jwt = JWTManager(app)
    
    # Initialize Database
    db.init_app(app)
    
    # Register Blueprints
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(ai_assistant_bp, url_prefix='/api/ai-assistant')
    app.register_blueprint(payment_bp, url_prefix='/api/payment')
    app.register_blueprint(social_media_bp, url_prefix='/api/social-media')
    app.register_blueprint(performance_bp, url_prefix='/api/performance')
    app.register_blueprint(referral_bp, url_prefix='/api/referral')
    app.register_blueprint(credit_schedule_bp, url_prefix='/api/credit-schedule')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(webhooks_bp, url_prefix='/api/webhooks')
    app.register_blueprint(oauth_bp, url_prefix='/api/oauth')
    app.register_blueprint(support_bp, url_prefix='/api/support')
    app.register_blueprint(marketing_strategies_bp, url_prefix='/api/marketing-strategies')
    app.register_blueprint(video_generation_bp, url_prefix='/api/video-generation')
    app.register_blueprint(prompt_analyzer_bp, url_prefix='/api/prompt-analyzer')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Marketing Automation System is running',
            'version': '1.0.0'
        })
    
    # Serve frontend files
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return jsonify({
                    'message': 'Marketing Automation System API',
                    'status': 'running',
                    'endpoints': {
                        'health': '/api/health',
                        'users': '/api/users',
                        'admin': '/api/admin'
                    }
                })
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

