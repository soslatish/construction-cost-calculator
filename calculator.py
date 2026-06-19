from functools import wraps
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from models import db, Calculation, CalculationItem

calc_bp = Blueprint('calc', __name__)


def editor_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.can_edit:
            flash('У вас нет прав для этого действия.', 'error')
            return redirect(url_for('calc.index'))
        return f(*args, **kwargs)
    return decorated


@calc_bp.route('/')
def index():
    return render_template('calculator/index.html')


@calc_bp.route('/save', methods=['POST'])
@editor_required
def save():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Нет данных'}), 400

    params = data.get('params', {})
    items = data.get('items', [])

    calc = Calculation(
        user_id=current_user.id,
        name=params.get('name', 'Без названия'),
        object_type=params.get('object_type', ''),
        total_area=float(params.get('total_area', 0)),
        floors=int(params.get('floors', 1)),
        foundation_type=params.get('foundation_type', ''),
        roof_type=params.get('roof_type', ''),
        notes=params.get('notes', ''),
        total_cost=float(data.get('total_cost', 0)),
    )
    db.session.add(calc)
    db.session.flush()

    for item in items:
        calc_item = CalculationItem(
            calculation_id=calc.id,
            category=item.get('category', ''),
            name=item.get('name', ''),
            unit=item.get('unit', ''),
            quantity=float(item.get('quantity', 0)),
            unit_price=float(item.get('unit_price', 0)),
            total_price=float(item.get('total_price', 0)),
        )
        db.session.add(calc_item)

    db.session.commit()
    return jsonify({'success': True, 'id': calc.id})


@calc_bp.route('/history')
@login_required
def history():
    if current_user.is_admin:
        calculations = Calculation.query.order_by(Calculation.created_at.desc()).all()
    else:
        calculations = Calculation.query.filter_by(user_id=current_user.id)\
            .order_by(Calculation.created_at.desc()).all()
    return render_template('calculator/history.html', calculations=calculations)


@calc_bp.route('/report/<int:calc_id>')
@login_required
def report(calc_id):
    calc = Calculation.query.get_or_404(calc_id)
    if not current_user.is_admin and calc.user_id != current_user.id:
        flash('Доступ запрещён.', 'error')
        return redirect(url_for('calc.history'))

    categories = {}
    for item in calc.items:
        categories.setdefault(item.category, []).append(item)

    category_totals = {}
    for cat, cat_items in categories.items():
        category_totals[cat] = sum(i.total_price for i in cat_items)

    category_names = {
        'materials': 'Материалы',
        'works': 'Работы',
        'equipment': 'Оборудование',
        'delivery': 'Доставка',
        'overhead': 'Накладные расходы',
    }

    return render_template('calculator/report.html',
                           calc=calc,
                           categories=categories,
                           category_totals=category_totals,
                           category_names=category_names)


@calc_bp.route('/report/<int:calc_id>/pdf')
@login_required
def report_pdf(calc_id):
    calc = Calculation.query.get_or_404(calc_id)
    if not current_user.is_admin and calc.user_id != current_user.id:
        flash('Доступ запрещён.', 'error')
        return redirect(url_for('calc.history'))

    categories = {}
    for item in calc.items:
        categories.setdefault(item.category, []).append(item)

    category_totals = {}
    for cat, cat_items in categories.items():
        category_totals[cat] = sum(i.total_price for i in cat_items)

    category_names = {
        'materials': 'Материалы',
        'works': 'Работы',
        'equipment': 'Оборудование',
        'delivery': 'Доставка',
        'overhead': 'Накладные расходы',
    }

    html = render_template('calculator/report_pdf.html',
                           calc=calc,
                           categories=categories,
                           category_totals=category_totals,
                           category_names=category_names)

    try:
        from xhtml2pdf import pisa
        from io import BytesIO
        result_buf = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=result_buf, encoding='utf-8')
        if pisa_status.err:
            flash('Ошибка генерации PDF.', 'error')
            return redirect(url_for('calc.report', calc_id=calc_id))
        pdf = result_buf.getvalue()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=smeta_{calc.id}.pdf'
        return response
    except ImportError:
        flash('Модуль xhtml2pdf не установлен. Экспорт PDF недоступен.', 'warning')
        return redirect(url_for('calc.report', calc_id=calc_id))


@calc_bp.route('/delete/<int:calc_id>', methods=['POST'])
@editor_required
def delete(calc_id):
    calc = Calculation.query.get_or_404(calc_id)
    if calc.user_id != current_user.id and not current_user.is_admin:
        flash('Доступ запрещён.', 'error')
        return redirect(url_for('calc.history'))

    db.session.delete(calc)
    db.session.commit()
    flash('Расчёт удалён.', 'success')
    return redirect(url_for('calc.history'))


@calc_bp.route('/load/<int:calc_id>')
@login_required
def load(calc_id):
    calc = Calculation.query.get_or_404(calc_id)
    if not current_user.is_admin and calc.user_id != current_user.id:
        return jsonify({'error': 'Доступ запрещён'}), 403

    items = []
    for item in calc.items:
        items.append({
            'category': item.category,
            'name': item.name,
            'unit': item.unit,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total_price': item.total_price,
        })

    return jsonify({
        'params': {
            'name': calc.name,
            'object_type': calc.object_type,
            'total_area': calc.total_area,
            'floors': calc.floors,
            'foundation_type': calc.foundation_type,
            'roof_type': calc.roof_type,
            'notes': calc.notes,
        },
        'items': items,
        'total_cost': calc.total_cost,
    })
