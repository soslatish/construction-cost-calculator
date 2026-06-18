const CATEGORIES = ['materials', 'works', 'equipment', 'delivery', 'overhead'];
const UNITS = ['шт', 'м²', 'м³', 'м.п.', 'кг', 'т', 'л', 'компл.', 'усл.', 'час', 'смена', 'рейс'];

function formatNumber(num) {
    return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(num);
}

function parseInputNumber(val) {
    return parseFloat(val) || 0;
}

function addRow(category, data) {
    const tbody = document.querySelector(`#table-${category} tbody`);
    const rowNum = tbody.rows.length + 1;

    const tr = document.createElement('tr');
    tr.dataset.category = category;

    const unitOptions = UNITS.map(u =>
        `<option value="${u}" ${data && data.unit === u ? 'selected' : ''}>${u}</option>`
    ).join('');

    tr.innerHTML = `
        <td class="text-center row-num">${rowNum}</td>
        <td><input type="text" class="form-control form-control-sm item-name" value="${data ? data.name : ''}" placeholder="Наименование"></td>
        <td>
            <select class="form-select form-select-sm item-unit">
                <option value="">—</option>
                ${unitOptions}
            </select>
        </td>
        <td><input type="number" class="form-control form-control-sm item-qty" min="0" step="any" value="${data ? data.quantity : ''}" oninput="calcRowTotal(this)"></td>
        <td><input type="number" class="form-control form-control-sm item-price" min="0" step="any" value="${data ? data.unit_price : ''}" oninput="calcRowTotal(this)"></td>
        <td class="item-total fw-bold text-end">${data ? formatNumber(data.total_price) : '0'}</td>
        <td class="text-center">
            <button class="btn btn-outline-danger btn-sm" onclick="removeRow(this, '${category}')" title="Удалить">
                <i class="bi bi-trash"></i>
            </button>
        </td>
    `;

    tbody.appendChild(tr);
    recalcSubtotal(category);
}

function removeRow(btn, category) {
    btn.closest('tr').remove();
    renumberRows(category);
    recalcSubtotal(category);
}

function renumberRows(category) {
    const rows = document.querySelectorAll(`#table-${category} tbody tr`);
    rows.forEach((tr, i) => {
        tr.querySelector('.row-num').textContent = i + 1;
    });
}

function calcRowTotal(input) {
    const tr = input.closest('tr');
    const qty = parseInputNumber(tr.querySelector('.item-qty').value);
    const price = parseInputNumber(tr.querySelector('.item-price').value);
    const total = qty * price;
    tr.querySelector('.item-total').textContent = formatNumber(total);

    const category = tr.dataset.category;
    recalcSubtotal(category);
}

function recalcSubtotal(category) {
    let subtotal = 0;
    const rows = document.querySelectorAll(`#table-${category} tbody tr`);
    rows.forEach(tr => {
        const qty = parseInputNumber(tr.querySelector('.item-qty').value);
        const price = parseInputNumber(tr.querySelector('.item-price').value);
        subtotal += qty * price;
    });

    const el = document.getElementById(`subtotal-${category}`);
    if (el) el.textContent = formatNumber(subtotal);

    recalcTotal();
}

function getSubtotal(category) {
    let subtotal = 0;
    const rows = document.querySelectorAll(`#table-${category} tbody tr`);
    rows.forEach(tr => {
        const qty = parseInputNumber(tr.querySelector('.item-qty').value);
        const price = parseInputNumber(tr.querySelector('.item-price').value);
        subtotal += qty * price;
    });
    return subtotal;
}

function recalcTotal() {
    const totals = {};
    CATEGORIES.forEach(cat => {
        totals[cat] = getSubtotal(cat);
    });

    const contingencyPct = parseInputNumber(document.getElementById('contingency-percent').value);
    const baseForContingency = totals.materials + totals.works;
    const contingency = baseForContingency * (contingencyPct / 100);

    const cEl = document.getElementById('contingency-amount');
    if (cEl) cEl.textContent = formatNumber(contingency) + ' ₽';

    const grandTotal = Object.values(totals).reduce((s, v) => s + v, 0) + contingency;

    document.getElementById('total-materials').textContent = formatNumber(totals.materials) + ' ₽';
    document.getElementById('total-works').textContent = formatNumber(totals.works) + ' ₽';
    document.getElementById('total-equipment').textContent = formatNumber(totals.equipment) + ' ₽';
    document.getElementById('total-delivery').textContent = formatNumber(totals.delivery) + ' ₽';
    document.getElementById('total-overhead').textContent = formatNumber(totals.overhead) + ' ₽';
    document.getElementById('total-contingency-pct').textContent = contingencyPct;
    document.getElementById('total-contingency').textContent = formatNumber(contingency) + ' ₽';
    document.getElementById('grand-total').textContent = formatNumber(grandTotal) + ' ₽';

    const area = parseInputNumber(document.getElementById('total-area').value);
    const costPerSqm = area > 0 ? grandTotal / area : 0;
    document.getElementById('cost-per-sqm').textContent = formatNumber(costPerSqm) + ' ₽/м²';
}

function collectData() {
    const params = {
        name: document.getElementById('calc-name').value || 'Без названия',
        object_type: document.getElementById('object-type').value,
        total_area: document.getElementById('total-area').value,
        floors: document.getElementById('floors').value,
        foundation_type: document.getElementById('foundation-type').value,
        roof_type: document.getElementById('roof-type').value,
        notes: document.getElementById('notes').value,
    };

    const items = [];
    CATEGORIES.forEach(cat => {
        const rows = document.querySelectorAll(`#table-${cat} tbody tr`);
        rows.forEach(tr => {
            const name = tr.querySelector('.item-name').value.trim();
            if (!name) return;
            items.push({
                category: cat,
                name: name,
                unit: tr.querySelector('.item-unit').value,
                quantity: parseInputNumber(tr.querySelector('.item-qty').value),
                unit_price: parseInputNumber(tr.querySelector('.item-price').value),
                total_price: parseInputNumber(tr.querySelector('.item-qty').value) * parseInputNumber(tr.querySelector('.item-price').value),
            });
        });
    });

    const contingencyPct = parseInputNumber(document.getElementById('contingency-percent').value);
    const baseForContingency = getSubtotal('materials') + getSubtotal('works');
    const contingency = baseForContingency * (contingencyPct / 100);
    if (contingency > 0) {
        items.push({
            category: 'overhead',
            name: `Непредвиденные расходы (${contingencyPct}%)`,
            unit: '%',
            quantity: contingencyPct,
            unit_price: baseForContingency / 100,
            total_price: contingency,
        });
    }

    let totalCost = 0;
    items.forEach(item => totalCost += item.total_price);

    return { params, items, total_cost: totalCost };
}

function saveCalculation() {
    const data = collectData();
    if (data.items.length === 0) {
        alert('Добавьте хотя бы одну позицию в расчёт.');
        return;
    }

    fetch('/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            alert('Расчёт сохранён!');
            window.location.href = '/history';
        } else {
            alert('Ошибка: ' + (result.error || 'Неизвестная ошибка'));
        }
    })
    .catch(() => alert('Ошибка сети при сохранении.'));
}

function loadCalculation(calcId) {
    fetch(`/load/${calcId}`)
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }

        document.getElementById('calc-name').value = data.params.name || '';
        document.getElementById('object-type').value = data.params.object_type || 'residential';
        document.getElementById('total-area').value = data.params.total_area || 100;
        document.getElementById('floors').value = data.params.floors || 1;
        document.getElementById('foundation-type').value = data.params.foundation_type || 'strip';
        document.getElementById('roof-type').value = data.params.roof_type || 'gable';
        document.getElementById('notes').value = data.params.notes || '';

        CATEGORIES.forEach(cat => {
            document.querySelector(`#table-${cat} tbody`).innerHTML = '';
        });

        data.items.forEach(item => {
            if (item.name.startsWith('Непредвиденные расходы')) return;
            addRow(item.category, item);
        });

        recalcTotal();
    })
    .catch(() => alert('Ошибка загрузки расчёта.'));
}

function printCalculation() {
    window.print();
}

document.getElementById('total-area').addEventListener('input', recalcTotal);

document.addEventListener('DOMContentLoaded', () => {
    CATEGORIES.forEach(cat => addRow(cat));
});
