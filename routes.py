import csv
import logging
from io import StringIO
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from app import app, db
from models import ProductionCell, Component

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    cells = ProductionCell.query.all()
    logger.debug(f"Retrieved {len(cells)} production cells from database")
    return render_template('index.html', cells=cells)

@app.route('/cell/add', methods=['GET', 'POST'])
def add_cell():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if not name:
            flash('Cell name is required', 'danger')
            return redirect(url_for('add_cell'))

        try:
            cell = ProductionCell(name=name, description=description)
            db.session.add(cell)
            db.session.commit()
            logger.debug(f"Successfully added new production cell: {name}")
            flash('Production cell added successfully', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding production cell: {str(e)}")
            flash(f'Error adding cell: {str(e)}', 'danger')
            return redirect(url_for('add_cell'))

    return render_template('cell_form.html')

@app.route('/component/add', methods=['GET', 'POST'])
def add_component():
    if request.method == 'POST':
        name = request.form.get('name')
        cell_id = request.form.get('cell_id')
        completion_time = request.form.get('completion_time')
        min_operators = request.form.get('min_operators')

        if not all([name, cell_id, completion_time, min_operators]):
            flash('All fields are required', 'danger')
            return redirect(url_for('add_component'))

        try:
            component = Component(
                name=name,
                cell_id=cell_id,
                completion_time=float(completion_time),
                min_operators=int(min_operators)
            )
            db.session.add(component)
            db.session.commit()
            logger.debug(f"Successfully added new component: {name} to cell_id: {cell_id}")
            flash('Component added successfully', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding component: {str(e)}")
            flash(f'Error adding component: {str(e)}', 'danger')
            return redirect(url_for('add_component'))

    cells = ProductionCell.query.all()
    return render_template('component_form.html', cells=cells)

@app.route('/view/<int:cell_id>')
def view_cell(cell_id):
    cell = ProductionCell.query.get_or_404(cell_id)
    logger.debug(f"Retrieved cell {cell_id} with {len(cell.components)} components")
    return render_template('view_data.html', cell=cell)

@app.route('/export/csv')
def export_csv():
    si = StringIO()
    cw = csv.writer(si)

    # Write headers
    cw.writerow(['Cell', 'Component', 'Completion Time (min)', 'Min Operators'])

    # Write data
    cells = ProductionCell.query.all()
    for cell in cells:
        for component in cell.components:
            cw.writerow([
                cell.name,
                component.name,
                component.completion_time,
                component.min_operators
            ])

    output = si.getvalue()
    si.close()

    return send_file(
        StringIO(output),
        mimetype='text/csv',
        as_attachment=True,
        download_name='production_data.csv'
    )