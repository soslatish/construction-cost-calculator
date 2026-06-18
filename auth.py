from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, ROLE_VIEWER, ROLE_MANAGER

auth_bp = Blueprint('auth', __name__)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('Доступ запрещён.', 'error')
            return redirect(url_for('calc.index'))
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('calc.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        if not username or not email or not password:
            flash('Заполните все поля.', 'error')
            return render_template('auth/register.html')

        if password != password2:
            flash('Пароли не совпадают.', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Пароль должен быть не менее 6 символов.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Этот email уже зарегистрирован.', 'error')
            return render_template('auth/register.html')

        user = User(username=username, email=email, role=ROLE_VIEWER)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Регистрация успешна! Вы вошли как наблюдатель.', 'success')
        return redirect(url_for('calc.index'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('calc.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Неверное имя пользователя или пароль.', 'error')
            return render_template('auth/login.html')

        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('calc.index'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('calc.index'))


@auth_bp.route('/admin/users')
@admin_required
def user_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('auth/users.html', users=users)


@auth_bp.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def add_manager():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('Заполните все поля.', 'error')
            return render_template('auth/add_manager.html')

        if len(password) < 6:
            flash('Пароль должен быть не менее 6 символов.', 'error')
            return render_template('auth/add_manager.html')

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует.', 'error')
            return render_template('auth/add_manager.html')

        if User.query.filter_by(email=email).first():
            flash('Этот email уже зарегистрирован.', 'error')
            return render_template('auth/add_manager.html')

        user = User(username=username, email=email, role=ROLE_MANAGER)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash(f'Менеджер «{username}» добавлен.', 'success')
        return redirect(url_for('auth.user_list'))

    return render_template('auth/add_manager.html')


@auth_bp.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Нельзя изменить роль администратора.', 'error')
        return redirect(url_for('auth.user_list'))

    user.role = ROLE_MANAGER if user.role == ROLE_VIEWER else ROLE_VIEWER
    db.session.commit()
    role_name = 'менеджер' if user.role == ROLE_MANAGER else 'наблюдатель'
    flash(f'Роль пользователя «{user.username}» изменена на «{role_name}».', 'success')
    return redirect(url_for('auth.user_list'))


@auth_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Нельзя удалить администратора.', 'error')
        return redirect(url_for('auth.user_list'))

    db.session.delete(user)
    db.session.commit()
    flash(f'Пользователь «{user.username}» удалён.', 'success')
    return redirect(url_for('auth.user_list'))
