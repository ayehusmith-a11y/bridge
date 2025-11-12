from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os
from decimal import Decimal
import threading
import time
import pandas as pd
import io
import serial
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weighing_bridge.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Enhanced User Model for Authentication and Management
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='operator')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Transport Company Model
class TransportCompany(db.Model):
    __tablename__ = 'transport_companies'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), unique=True, nullable=False)
    contact_person = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Driver Model
class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    driver_name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    transport_company_id = db.Column(db.Integer, db.ForeignKey('transport_companies.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Enhanced Truck Model with unique constraints
class Truck(db.Model):
    __tablename__ = 'trucks'
    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(20), unique=True, nullable=False)
    transporter_name = db.Column(db.String(100), nullable=False)
    axles = db.Column(db.Integer, nullable=False, default=4)
    transport_company_id = db.Column(db.Integer, db.ForeignKey('transport_companies.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transport_company = db.relationship('TransportCompany', backref='trucks')

# Truck-Driver Assignment Model
class TruckDriver(db.Model):
    __tablename__ = 'truck_drivers'
    id = db.Column(db.Integer, primary_key=True)
    truck_id = db.Column(db.Integer, db.ForeignKey('trucks.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    assigned_date = db.Column(db.Date, default=date.today)
    is_active = db.Column(db.Boolean, default=True)
    
    truck = db.relationship('Truck', backref='driver_assignments')
    driver = db.relationship('Driver', backref='truck_assignments')

# Product Model with LNG specifications
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), unique=True, nullable=False)
    product_code = db.Column(db.String(50))
    unit_price = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Material Model for manganese mining
class Material(db.Model):
    __tablename__ = 'materials'
    id = db.Column(db.Integer, primary_key=True)
    material_name = db.Column(db.String(50), unique=True, nullable=False)
    material_code = db.Column(db.String(20))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Destination Model
class Destination(db.Model):
    __tablename__ = 'destinations'
    id = db.Column(db.Integer, primary_key=True)
    destination_name = db.Column(db.String(100), unique=True, nullable=False)
    location_code = db.Column(db.String(50))
    distance_km = db.Column(db.Numeric(8, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Operator Model
class Operator(db.Model):
    __tablename__ = 'operators'
    id = db.Column(db.Integer, primary_key=True)
    operator_name = db.Column(db.String(100), unique=True, nullable=False)
    employee_id = db.Column(db.String(50))
    department = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Loader Model
class Loader(db.Model):
    __tablename__ = 'loaders'
    id = db.Column(db.Integer, primary_key=True)
    loader_name = db.Column(db.String(100), unique=True, nullable=False)
    equipment_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Enhanced Weighing Record Model matching requirements exactly
class WeighingRecord(db.Model):
    __tablename__ = 'weighing_records'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    date_in = db.Column(db.Date, nullable=False)
    time_in = db.Column(db.Time, nullable=False)
    date_out = db.Column(db.Date)
    time_out = db.Column(db.Time)
    way_bill = db.Column(db.String(50), unique=True, nullable=False)
    registration = db.Column(db.String(20), nullable=False)
    axles = db.Column(db.Integer, nullable=False)
    trip_number = db.Column(db.Integer, nullable=False)
    transporter_name = db.Column(db.String(100), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'))
    mass1 = db.Column(db.Numeric(10, 2), nullable=False)
    mass2 = db.Column(db.Numeric(10, 2), nullable=False)
    net_load = db.Column(db.Numeric(10, 2), nullable=False)
    operator_weigh = db.Column(db.String(100), nullable=False)
    loader = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    material = db.relationship('Material', backref='weighing_records')

# Offline Sync Table
class OfflineSync(db.Model):
    __tablename__ = 'offline_sync'
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('weighing_records.id'), nullable=False)
    sync_status = db.Column(db.String(20), default='pending')
    last_sync_attempt = db.Column(db.DateTime)
    sync_error = db.Column(db.Text)
    
    record = db.relationship('WeighingRecord', backref='sync_status')

# System Settings Model
class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Smart Weight Weighbridge Integration
weighbridge_status = {
    'connected': False, 
    'weight': 0.0, 
    'stable': False,
    'tare_weight': 0.0,
    'serial_port': None
}

def smart_weight_connect():
    """Connect to Smart Weight weighing machine"""
    try:
        # Get connection settings from database
        port_setting = SystemSetting.query.filter_by(setting_key='smart_weight_port').first()
        baudrate_setting = SystemSetting.query.filter_by(setting_key='smart_weight_baudrate').first()
        
        port = port_setting.setting_value if port_setting else 'COM1'
        baudrate = int(baudrate_setting.setting_value) if baudrate_setting else 9600
        
        # For simulation, we'll use a mock connection
        weighbridge_status['connected'] = True
        weighbridge_status['tare_weight'] = 0.0
        logging.info(f"Smart Weight connected to {port} at {baudrate}")
        return True
    except Exception as e:
        logging.error(f"Failed to connect to Smart Weight: {e}")
        return False

def smart_weight_read():
    """Read weight from Smart Weight machine"""
    if weighbridge_status['connected']:
        # Simulate weight reading for Smart Weight
        import random
        base_weight = 25.0
        fluctuation = random.uniform(-0.5, 0.5)
        current_weight = round(base_weight + fluctuation - weighbridge_status['tare_weight'], 2)
        weighbridge_status['stable'] = abs(fluctuation) < 0.1
        return current_weight
    return 0.0

def smart_weight_tare():
    """Tare the Smart Weight scale"""
    if weighbridge_status['connected']:
        weighbridge_status['tare_weight'] = weighbridge_status['weight']
        return True
    return False

# Routes

@app.route('/')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return admin_dashboard()
    else:
        return operator_dashboard()

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    total_records = WeighingRecord.query.count()
    today_records = WeighingRecord.query.filter_by(date_in=date.today()).count()
    total_weight = db.session.query(db.func.sum(WeighingRecord.net_load)).scalar() or 0
    total_trucks = Truck.query.count()
    active_drivers = Driver.query.count()
    
    recent_records = WeighingRecord.query.order_by(WeighingRecord.created_at.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html', 
                         total_records=total_records,
                         today_records=today_records,
                         total_weight=total_weight,
                         total_trucks=total_trucks,
                         active_drivers=active_drivers,
                         recent_records=recent_records)

@app.route('/operator/dashboard')
@login_required
def operator_dashboard():
    current_date = date.today().isoformat()
    return render_template('operator_dashboard.html', current_date=current_date)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.is_active and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials or account deactivated', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# User Management Routes (Admin only)
@app.route('/admin/users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/api/users', methods=['GET', 'POST'])
@login_required
def api_users():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    if request.method == 'GET':
        users = User.query.all()
        return jsonify([{
            'id': u.id, 'username': u.username, 'role': u.role, 
            'is_active': u.is_active, 'created_at': u.created_at.isoformat()
        } for u in users])
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            user = User(
                username=data['username'],
                role=data.get('role', 'operator'),
                is_active=data.get('is_active', True)
            )
            user.set_password(data['password'])
            db.session.add(user)
            db.session.commit()
            return jsonify({'success': True, 'message': 'User created successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
@login_required
def api_user_detail(user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'PUT':
        try:
            data = request.get_json()
            user.role = data.get('role', user.role)
            user.is_active = data.get('is_active', user.is_active)
            
            if data.get('password'):
                user.set_password(data['password'])
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'User updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'success': True, 'message': 'User deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})

# Truck Management Routes
@app.route('/admin/trucks')
@login_required
def manage_trucks():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    
    trucks = Truck.query.all()
    drivers = Driver.query.all()
    return render_template('manage_trucks.html', trucks=trucks, drivers=drivers)

@app.route('/api/trucks', methods=['GET', 'POST'])
@login_required
def api_trucks():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    if request.method == 'GET':
        trucks = Truck.query.all()
        return jsonify([{
            'id': t.id, 'registration_number': t.registration_number,
            'transporter_name': t.transporter_name, 'axles': t.axles,
            'transport_company_id': t.transport_company_id
        } for t in trucks])
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            truck = Truck(
                registration_number=data['registration_number'],
                transporter_name=data['transporter_name'],
                axles=data.get('axles', 4),
                transport_company_id=data.get('transport_company_id')
            )
            db.session.add(truck)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Truck added successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/trucks/<int:truck_id>/assign_drivers', methods=['POST'])
@login_required
def assign_drivers_to_truck(truck_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        data = request.get_json()
        driver_ids = data.get('driver_ids', [])
        
        # Remove existing assignments
        TruckDriver.query.filter_by(truck_id=truck_id).delete()
        
        # Add new assignments
        for driver_id in driver_ids:
            assignment = TruckDriver(truck_id=truck_id, driver_id=driver_id)
            db.session.add(assignment)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Drivers assigned successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Weighing Routes
@app.route('/weighing')
@login_required
def weighing():
    materials = Material.query.all()
    products = Product.query.all()
    operators = Operator.query.all()
    loaders = Loader.query.all()
    destinations = Destination.query.all()
    
    return render_template('weighing.html',
                         materials=materials,
                         products=products,
                         operators=operators,
                         loaders=loaders,
                         destinations=destinations)

@app.route('/api/weighing', methods=['POST'])
@login_required
def create_weighing_record():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['way_bill', 'registration', 'axles', 'trip_number', 
                          'mass1', 'mass2', 'date_in', 'time_in', 'transporter_name',
                          'driver_name', 'product_name', 'operator_weigh', 'loader']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'{field} is required'})
        
        # Calculate net load automatically
        mass1 = Decimal(str(data['mass1']))
        mass2 = Decimal(str(data['mass2']))
        net_load = abs(mass2 - mass1)
        
        # Parse date and time
        date_in = datetime.strptime(data['date_in'], '%Y-%m-%d').date()
        time_in = datetime.strptime(data['time_in'], '%H:%M').time()
        
        # Create weighing record
        record = WeighingRecord(
            year=date_in.year,
            month=date_in.month,
            date_in=date_in,
            time_in=time_in,
            way_bill=data['way_bill'],
            registration=data['registration'],
            axles=int(data['axles']),
            trip_number=int(data['trip_number']),
            transporter_name=data['transporter_name'],
            driver_name=data['driver_name'],
            product_name=data['product_name'],
            material_id=data.get('material_id'),
            mass1=mass1,
            mass2=mass2,
            net_load=net_load,
            operator_weigh=data['operator_weigh'],
            loader=data['loader'],
            destination=data.get('destination')
        )
        
        # Handle date_out and time_out if provided
        if data.get('date_out'):
            record.date_out = datetime.strptime(data['date_out'], '%Y-%m-%d').date()
        if data.get('time_out'):
            record.time_out = datetime.strptime(data['time_out'], '%H:%M').time()
        
        db.session.add(record)
        db.session.commit()
        
        # Add to offline sync table if in offline mode
        offline_setting = SystemSetting.query.filter_by(setting_key='offline_mode').first()
        if offline_setting and offline_setting.setting_value == 'true':
            sync_record = OfflineSync(record_id=record.id)
            db.session.add(sync_record)
            db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Weighing record created successfully',
            'record_id': record.id,
            'net_load': float(net_load)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Records Management with Search and Filter
@app.route('/records')
@login_required
def records():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_column = request.args.get('filter_column', '')
    filter_value = request.args.get('filter_value', '')
    
    query = WeighingRecord.query
    
    if search:
        query = query.filter(
            db.or_(
                WeighingRecord.way_bill.ilike(f'%{search}%'),
                WeighingRecord.registration.ilike(f'%{search}%'),
                WeighingRecord.transporter_name.ilike(f'%{search}%'),
                WeighingRecord.driver_name.ilike(f'%{search}%')
            )
        )
    
    if filter_column and filter_value:
        if hasattr(WeighingRecord, filter_column):
            query = query.filter(getattr(WeighingRecord, filter_column).ilike(f'%{filter_value}%'))
    
    records = query.order_by(WeighingRecord.date_in.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    # Get all column names for filter dropdown
    columns = [column.name for column in WeighingRecord.__table__.columns 
               if column.name not in ['id', 'created_at', 'updated_at']]
    
    return render_template('records.html', records=records, search=search, 
                         filter_column=filter_column, filter_value=filter_value,
                         columns=columns)

# Records CRUD API
@app.route('/api/records/<int:record_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_record(record_id):
    record = WeighingRecord.query.get_or_404(record_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': record.id, 'year': record.year, 'month': record.month,
            'date_in': record.date_in.isoformat() if record.date_in else None,
            'time_in': record.time_in.isoformat() if record.time_in else None,
            'date_out': record.date_out.isoformat() if record.date_out else None,
            'time_out': record.time_out.isoformat() if record.time_out else None,
            'way_bill': record.way_bill, 'registration': record.registration,
            'axles': record.axles, 'trip_number': record.trip_number,
            'transporter_name': record.transporter_name, 'driver_name': record.driver_name,
            'product_name': record.product_name, 'material_id': record.material_id,
            'mass1': float(record.mass1), 'mass2': float(record.mass2),
            'net_load': float(record.net_load), 'operator_weigh': record.operator_weigh,
            'loader': record.loader, 'destination': record.destination,
            'status': record.status
        })
    
    elif request.method == 'PUT':
        try:
            if current_user.role != 'admin':
                return jsonify({'success': False, 'message': 'Access denied'})
            
            data = request.get_json()
            
            # Update fields
            for field in ['year', 'month', 'axles', 'trip_number', 'material_id']:
                if field in data:
                    setattr(record, field, int(data[field]) if data[field] else None)
            
            for field in ['date_in', 'date_out']:
                if field in data and data[field]:
                    setattr(record, field, datetime.strptime(data[field], '%Y-%m-%d').date())
            
            for field in ['time_in', 'time_out']:
                if field in data and data[field]:
                    setattr(record, field, datetime.strptime(data[field], '%H:%M').time())
            
            for field in ['way_bill', 'registration', 'transporter_name', 'driver_name',
                         'product_name', 'operator_weigh', 'loader', 'destination', 'status']:
                if field in data:
                    setattr(record, field, data[field])
            
            # Update masses and recalculate net load
            if 'mass1' in data and 'mass2' in data:
                record.mass1 = Decimal(str(data['mass1']))
                record.mass2 = Decimal(str(data['mass2']))
                record.net_load = abs(record.mass2 - record.mass1)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Record updated successfully'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})
    
    elif request.method == 'DELETE':
        try:
            if current_user.role != 'admin':
                return jsonify({'success': False, 'message': 'Access denied'})
            
            db.session.delete(record)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Record deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})

# Reports and Excel Export
@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/api/reports/summary')
@login_required
def reports_summary():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    filter_column = request.args.get('filter_column', '')
    filter_value = request.args.get('filter_value', '')
    
    query = db.session.query(
        WeighingRecord,
        Material.material_name
    ).outerjoin(
        Material, WeighingRecord.material_id == Material.id
    )
    
    if start_date:
        query = query.filter(WeighingRecord.date_in >= start_date)
    if end_date:
        query = query.filter(WeighingRecord.date_in <= end_date)
    
    if filter_column and filter_value:
        if hasattr(WeighingRecord, filter_column):
            query = query.filter(getattr(WeighingRecord, filter_column).ilike(f'%{filter_value}%'))
    
    records = query.all()
    
    # Format data for frontend and export
    data = []
    for record, material in records:
        data.append({
            'id': record.id, 'year': record.year, 'month': record.month,
            'date_in': record.date_in.isoformat() if record.date_in else None,
            'time_in': record.time_in.isoformat() if record.time_in else None,
            'date_out': record.date_out.isoformat() if record.date_out else None,
            'time_out': record.time_out.isoformat() if record.time_out else None,
            'way_bill': record.way_bill, 'registration': record.registration,
            'axles': record.axles, 'trip_number': record.trip_number,
            'transporter_name': record.transporter_name, 'driver_name': record.driver_name,
            'product_name': record.product_name, 'material': material or 'N/A',
            'mass1': float(record.mass1), 'mass2': float(record.mass2),
            'net_load': float(record.net_load), 'operator_weigh': record.operator_weigh,
            'loader': record.loader, 'destination': record.destination or 'N/A',
            'status': record.status, 'created_at': record.created_at.isoformat()
        })
    
    return jsonify(data)

@app.route('/api/reports/export')
@login_required
def export_to_excel():
    try:
        # Get the same data as reports_summary
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        filter_column = request.args.get('filter_column', '')
        filter_value = request.args.get('filter_value', '')
        
        query = db.session.query(WeighingRecord, Material.material_name).outerjoin(
            Material, WeighingRecord.material_id == Material.id)
        
        if start_date:
            query = query.filter(WeighingRecord.date_in >= start_date)
        if end_date:
            query = query.filter(WeighingRecord.date_in <= end_date)
        
        if filter_column and filter_value:
            if hasattr(WeighingRecord, filter_column):
                query = query.filter(getattr(WeighingRecord, filter_column).ilike(f'%{filter_value}%'))
        
        records = query.all()
        
        # Prepare data for DataFrame
        data = []
        for record, material in records:
            data.append({
                'ID': record.id,
                'Year': record.year,
                'Month': record.month,
                'Date In': record.date_in.strftime('%Y-%m-%d') if record.date_in else '',
                'Time In': record.time_in.strftime('%H:%M') if record.time_in else '',
                'Date Out': record.date_out.strftime('%Y-%m-%d') if record.date_out else '',
                'Time Out': record.time_out.strftime('%H:%M') if record.time_out else '',
                'Waybill': record.way_bill,
                'Registration': record.registration,
                'Axles': record.axles,
                'Trip Number': record.trip_number,
                'Transporter Name': record.transporter_name,
                'Driver Name': record.driver_name,
                'Product Name': record.product_name,
                'Material': material or 'N/A',
                'Mass 1': float(record.mass1),
                'Mass 2': float(record.mass2),
                'Net Load': float(record.net_load),
                'Operator Weigh': record.operator_weigh,
                'Loader': record.loader,
                'Destination': record.destination or 'N/A',
                'Status': record.status,
                'Created At': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Create DataFrame and Excel file
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Weighing Records', index=False)
            
            # Get the workbook and worksheet for formatting
            workbook = writer.book
            worksheet = writer.sheets['Weighing Records']
            
            # Adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=weighing_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Management API endpoints for dropdowns
@app.route('/api/materials', methods=['GET'])
@login_required
def get_materials():
    materials = Material.query.all()
    return jsonify([{'id': m.id, 'name': m.material_name, 'code': m.material_code} for m in materials])

@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    products = Product.query.all()
    return jsonify([{'id': p.id, 'name': p.product_name, 'code': p.product_code} for p in products])

@app.route('/api/operators', methods=['GET'])
@login_required
def get_operators():
    operators = Operator.query.all()
    return jsonify([{'id': o.id, 'name': o.operator_name, 'employee_id': o.employee_id} for o in operators])

@app.route('/api/loaders', methods=['GET'])
@login_required
def get_loaders():
    loaders = Loader.query.all()
    return jsonify([{'id': l.id, 'name': l.loader_name, 'type': l.equipment_type} for l in loaders])

@app.route('/api/destinations', methods=['GET'])
@login_required
def get_destinations():
    destinations = Destination.query.all()
    return jsonify([{'id': d.id, 'name': d.destination_name, 'code': d.location_code} for d in destinations])

# Smart Weight Weighbridge API endpoints
@app.route('/api/weighbridge/status')
@login_required
def get_weighbridge_status():
    # Update current weight
    if weighbridge_status['connected']:
        weighbridge_status['weight'] = smart_weight_read()
    return jsonify(weighbridge_status)

@app.route('/api/weighbridge/connect', methods=['POST'])
@login_required
def connect_weighbridge():
    try:
        success = smart_weight_connect()
        if success:
            return jsonify({'success': True, 'message': 'Smart Weight connected successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to connect to Smart Weight'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/weighbridge/disconnect', methods=['POST'])
@login_required
def disconnect_weighbridge():
    try:
        weighbridge_status['connected'] = False
        weighbridge_status['weight'] = 0.0
        weighbridge_status['stable'] = False
        weighbridge_status['tare_weight'] = 0.0
        return jsonify({'success': True, 'message': 'Smart Weight disconnected successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/weighbridge/tare', methods=['POST'])
@login_required
def tare_weighbridge():
    try:
        if not weighbridge_status['connected']:
            return jsonify({'success': False, 'message': 'Smart Weight not connected'})
        
        success = smart_weight_tare()
        if success:
            return jsonify({'success': True, 'message': 'Smart Weight tared successfully'})
        else:
            return jsonify({'success': False, 'message': 'Tare operation failed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/weighbridge/zero', methods=['POST'])
@login_required
def zero_weighbridge():
    try:
        if not weighbridge_status['connected']:
            return jsonify({'success': False, 'message': 'Smart Weight not connected'})
        
        weighbridge_status['tare_weight'] = 0.0
        return jsonify({'success': True, 'message': 'Smart Weight zeroed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/weighbridge/capture', methods=['POST'])
@login_required
def capture_weight():
    try:
        if not weighbridge_status['connected']:
            return jsonify({'success': False, 'message': 'Smart Weight not connected'})
        if not weighbridge_status['stable']:
            return jsonify({'success': False, 'message': 'Weight is not stable'})

        weight = weighbridge_status['weight']
        return jsonify({'success': True, 'weight': weight})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Ticket Generation
@app.route('/api/ticket/<int:record_id>')
@login_required
def generate_ticket(record_id):
    try:
        record = WeighingRecord.query.get_or_404(record_id)
        material = record.material.material_name if record.material else 'N/A'

        # Generate HTML ticket
        ticket_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Weighing Ticket - {record.way_bill}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .ticket {{ border: 2px solid #000; padding: 20px; max-width: 600px; margin: 0 auto; }}
                .header {{ text-align: center; border-bottom: 1px solid #000; padding-bottom: 10px; margin-bottom: 20px; }}
                .company {{ font-size: 24px; font-weight: bold; }}
                .details {{ margin-bottom: 20px; }}
                .detail-row {{ display: flex; margin-bottom: 5px; }}
                .label {{ font-weight: bold; width: 150px; }}
                .value {{ flex: 1; }}
                .weights {{ border: 1px solid #000; padding: 10px; margin: 10px 0; }}
                .weight-row {{ display: flex; justify-content: space-between; margin-bottom: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="ticket">
                <div class="header">
                    <div class="company">MANGANESE MINING CO.</div>
                    <div>SMART WEIGHT BRIDGE TICKET</div>
                    <div>Ticket No: {record.id}</div>
                </div>

                <div class="details">
                    <div class="detail-row">
                        <div class="label">Way Bill:</div>
                        <div class="value">{record.way_bill}</div>
                    </div>
                    <div class="detail-row">
                        <div class="label">Date In:</div>
                        <div class="value">{record.date_in.strftime('%Y-%m-%d')}</div>
                    </div>
                    <div class="detail-row">
                        <div class="label">Time In:</div>
                        <div class="value">{record.time_in.strftime('%H:%M')}</div>
                    </div>
                    <div class="detail-row">
                        <div class="label">Registration:</div>
                        <div class="value">{record.registration}</div>
                    </div>
                    <div class="detail-row">
                        <div class="label">Transporter:</div>
                        <div class="value">{record.transporter_name}</div>
                    </div>
                    <div class="detail-row">
                        <div class="label">Driver Name:</div>
                        <div class="value">{record.driver_name}</div>
                    </div>
                    <div class="detail-row">
                        <div class="label">Product:</div>
                        <div class="value">{record.product_name}</div>
                    </div>
                    <div class="detail-row">
                        <div class="label">Material:</div>
                        <div class="value">{material}</div>
                    </div>
                    <div class="detail-row">
                        <div class="label">Trip Number:</div>
                        <div class="value">{record.trip_number}</div>
                    </div>
                    <div class="detail-row">
                        <div class="label">Destination:</div>
                        <div class="value">{record.destination or 'N/A'}</div>
                    </div>
                    <div class="detail-row">
                        <div class="label">Operator:</div>
                        <div class="value">{record.operator_weigh}</div>
                    </div>
                    <div class="detail-row">
                        <div class="label">Loader:</div>
                        <div class="value">{record.loader}</div>
                    </div>
                </div>

                <div class="weights">
                    <div class="weight-row">
                        <span>Mass 1 (Initial):</span>
                        <span>{record.mass1} tons</span>
                    </div>
                    <div class="weight-row">
                        <span>Mass 2 (Final):</span>
                        <span>{record.mass2} tons</span>
                    </div>
                    <div class="weight-row" style="border-top: 1px solid #000; padding-top: 5px; font-weight: bold;">
                        <span>Net Load:</span>
                        <span>{record.net_load} tons</span>
                    </div>
                </div>

                <div class="footer">
                    <p>This ticket serves as official proof of weighing</p>
                    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return jsonify({'success': True, 'html': ticket_html})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Background thread to simulate weighbridge weight updates
def simulate_smart_weight():
    while True:
        if weighbridge_status['connected']:
            weighbridge_status['weight'] = smart_weight_read()
        time.sleep(1)

# Database Initialization
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin', is_active=True)
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Create sample operators
        if Operator.query.count() == 0:
            operators = [
                Operator(operator_name='Operator 1', employee_id='EMP001', department='Weighing'),
                Operator(operator_name='Operator 2', employee_id='EMP002', department='Weighing'),
                Operator(operator_name='Operator 3', employee_id='EMP003', department='Weighing')
            ]
            db.session.add_all(operators)
        
        # Create sample loaders
        if Loader.query.count() == 0:
            loaders = [
                Loader(loader_name='Loader Machine 1', equipment_type='Front Loader'),
                Loader(loader_name='Loader Machine 2', equipment_type='Excavator'),
                Loader(loader_name='Loader Machine 3', equipment_type='Wheel Loader')
            ]
            db.session.add_all(loaders)
        
        # Create sample destinations
        if Destination.query.count() == 0:
            destinations = [
                Destination(destination_name='Port Facility A', location_code='PRT001'),
                Destination(destination_name='Processing Plant B', location_code='PLN002'),
                Destination(destination_name='Storage Yard C', location_code='YRD003')
            ]
            db.session.add_all(destinations)
        
        db.session.commit()

if __name__ == '__main__':
    init_db()
    
    # Start the Smart Weight simulation thread
    weighbridge_thread = threading.Thread(target=simulate_smart_weight, daemon=True)
    weighbridge_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=8050)