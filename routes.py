import csv
import logging
from io import StringIO, BytesIO
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from app import app, db
from models import ProductionCell, Component, Customer, Job, JobComponent

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    jobs = Job.query.order_by(Job.estimated_completion_date).all()

    for job in jobs:
        # Calculate completion percentage
        total_components = len(job.components)
        completed_components = sum(1 for c in job.components if c.completed)
        job.completed_components = completed_components
        job.total_components = total_components

        # Calculate current production time
        completed_times = [c.actual_completion_time for c in job.components if c.completed and c.actual_completion_time]
        job.current_production_time = sum(completed_times) / 60 if completed_times else 0  # Convert to hours

        # Determine current cell (last non-completed component's cell)
        current_component = next((c for c in job.components if not c.completed), None)
        job.current_cell = Component.query.get(current_component.component_id).cell.name if current_component else None

    logger.debug(f"Retrieved {len(jobs)} jobs for dashboard")
    return render_template('index.html', jobs=jobs)

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

@app.route('/order/create', methods=['GET', 'POST'])
def create_order():
    if request.method == 'POST':
        # Get customer information
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        components = request.form.getlist('components')  # List of component IDs

        if not all([name, phone, email, components]):
            flash('All fields are required', 'danger')
            return redirect(url_for('create_order'))

        try:
            # Create customer
            customer = Customer(name=name, phone=phone, email=email)
            db.session.add(customer)
            db.session.flush()  # Get customer ID before committing

            # Generate job number (YYYYMMDD-XXX format)
            today = datetime.utcnow()
            job_prefix = today.strftime('%Y%m%d')
            last_job = Job.query.filter(Job.job_number.like(f'{job_prefix}-%')).order_by(Job.job_number.desc()).first()
            if last_job:
                last_number = int(last_job.job_number.split('-')[1])
                job_number = f"{job_prefix}-{str(last_number + 1).zfill(3)}"
            else:
                job_number = f"{job_prefix}-001"

            # Calculate job metrics
            selected_components = Component.query.filter(Component.id.in_(components)).all()
            total_time = sum(c.completion_time for c in selected_components)
            min_operators = max(c.min_operators for c in selected_components)
            max_operators = min_operators * 2  # Assuming max is double the minimum

            # Create job
            job = Job(
                job_number=job_number,
                customer_id=customer.id,
                total_hours=total_time / 60,  # Convert minutes to hours
                min_operators=min_operators,
                max_operators=max_operators,
                estimated_completion_date=today + timedelta(hours=total_time/60/min_operators),
                current_operators=0, # Added for operator tracking.
                status = 'Pending' # Added for job status tracking.
            )
            db.session.add(job)
            db.session.flush()  # Get job ID before creating components

            # Add components to job
            for component_id in components:
                job_component = JobComponent(
                    job_id=job.id,
                    component_id=int(component_id),
                    start_time=None,
                    end_time=None,
                    completed=False
                )
                db.session.add(job_component)

            db.session.commit()
            logger.debug(f"Created new job {job_number} for customer {name}")

            flash('Order created successfully', 'success')
            return redirect(url_for('view_job', job_id=job.id))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating order: {str(e)}")
            flash(f'Error creating order: {str(e)}', 'danger')
            return redirect(url_for('create_order'))

    cells = ProductionCell.query.all()
    return render_template('order_form.html', cells=cells)

@app.route('/job/<int:job_id>')
def view_job(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('view_job.html', job=job, Component=Component)

@app.route('/job/<int:job_id>/operator-checklist.pdf')
def operator_checklist(job_id):
    job = Job.query.get_or_404(job_id)

    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Add header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, f"Operator Checklist - Job #{job.job_number}")

    # Add job info
    p.setFont("Helvetica", 12)
    y = 700
    p.drawString(50, y, f"Customer: {job.customer.name}")
    y -= 20
    p.drawString(50, y, f"Order Date: {job.order_date.strftime('%Y-%m-%d')}")

    # Add component checklist
    y -= 40
    p.drawString(50, y, "Components to Install:")
    y -= 20

    for job_component in job.components:
        component = Component.query.get(job_component.component_id)
        p.drawString(70, y, f"[ ] {component.name}")
        y -= 20

    p.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'operator_checklist_{job.job_number}.pdf'
    )

@app.route('/job/<int:job_id>/sales-form.pdf')
def sales_form(job_id):
    job = Job.query.get_or_404(job_id)

    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Add header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, f"Sales Form - Job #{job.job_number}")

    # Add customer info
    p.setFont("Helvetica", 12)
    y = 700
    p.drawString(50, y, f"Customer Name: {job.customer.name}")
    y -= 20
    p.drawString(50, y, f"Phone: {job.customer.phone}")
    y -= 20
    p.drawString(50, y, f"Email: {job.customer.email}")

    # Add job details
    y -= 40
    p.drawString(50, y, f"Order Date: {job.order_date.strftime('%Y-%m-%d')}")
    y -= 20
    p.drawString(50, y, f"Estimated Completion: {job.estimated_completion_date.strftime('%Y-%m-%d')}")
    y -= 20
    p.drawString(50, y, f"Total Hours: {job.total_hours:.1f}")
    y -= 20
    p.drawString(50, y, f"Required Operators: {job.min_operators} - {job.max_operators}")

    p.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'sales_form_{job.job_number}.pdf'
    )

def generate_operator_checklist(job_id):
    """Generate and save operator checklist PDF"""
    operator_checklist(job_id)
    logger.debug(f"Generated operator checklist for job {job_id}")

def generate_sales_form(job_id):
    """Generate and save sales form PDF"""
    sales_form(job_id)
    logger.debug(f"Generated sales form for job {job_id}")

@app.route('/operator-portal')
def operator_portal():
    # Get jobs ordered by ETA
    jobs = Job.query.order_by(Job.estimated_completion_date).all()

    # Calculate pending components for each job
    for job in jobs:
        job.pending_components = sum(1 for c in job.components if not c.completed)

    # Get active tasks (components started but not completed)
    active_tasks = JobComponent.query.filter(
        JobComponent.start_time.isnot(None),
        JobComponent.end_time.is_(None)
    ).all()

    logger.debug(f"Retrieved {len(jobs)} jobs and {len(active_tasks)} active tasks for operator portal")
    return render_template('operator_portal.html', jobs=jobs, active_tasks=active_tasks, Component=Component)

@app.route('/job/<int:job_id>/component/<int:component_id>/start', methods=['POST'])
def start_task(job_id, component_id):
    try:
        job_component = JobComponent.query.filter_by(
            job_id=job_id,
            id=component_id
        ).first_or_404()

        if job_component.completed:
            flash('This component is already completed', 'warning')
        elif job_component.start_time and not job_component.end_time:
            flash('This task is already in progress', 'warning')
        else:
            job_component.start_time = datetime.utcnow()
            job = Job.query.get(job_id)
            job.current_operators += 1
            job.status = 'In Progress'
            db.session.commit()
            logger.debug(f"Started task for job {job_id}, component {component_id}")
            flash('Task started successfully', 'success')

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error starting task: {str(e)}")
        flash('Error starting task', 'danger')

    return redirect(url_for('operator_portal'))

@app.route('/job/<int:job_id>/component/<int:component_id>/end', methods=['POST'])
def end_task(job_id, component_id):
    try:
        job_component = JobComponent.query.filter_by(
            job_id=job_id,
            id=component_id
        ).first_or_404()

        if not job_component.start_time:
            flash('This task has not been started', 'warning')
        elif job_component.end_time:
            flash('This task is already completed', 'warning')
        else:
            end_time = datetime.utcnow()
            job_component.end_time = end_time
            job_component.completed = True

            # Calculate actual completion time in minutes
            duration = end_time - job_component.start_time
            job_component.actual_completion_time = duration.total_seconds() / 60

            # Update job status and operator count
            job = Job.query.get(job_id)
            job.current_operators -= 1

            # Check if all components are completed
            if all(c.completed for c in job.components):
                job.status = 'Completed'

            db.session.commit()
            logger.debug(f"Completed task for job {job_id}, component {component_id}")
            flash('Task completed successfully', 'success')

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error completing task: {str(e)}")
        flash('Error completing task', 'danger')

    return redirect(url_for('operator_portal'))