import os

class Config:
    #Flask settings
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = 5000
    FLASK_DEBUG = True
    
    #Paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    FRONTEND_DIR = os.path.join(BASE_DIR,'./Frontend')
    TEMPLATE_FOLDER = os.path.join(FRONTEND_DIR,'templates')
    STATIC_FOLDER = os.path.join(FRONTEND_DIR, 'static')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    
    #Models settings
    VIDEO_PATH