import os
from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User, ROLE_ADMIN

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Войдите в систему для доступа к этой странице.'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from auth import auth_bp
    from calculator import calc_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(calc_bp)

    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role=ROLE_ADMIN).first():
            admin = User(
                username='admin',
                email='admin@sunline-stroy.ru',
                role=ROLE_ADMIN,
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
