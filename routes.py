import os
import pandas as pd
import json
import logging
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Dataset, AnomalyResult
from forms import LoginForm, RegistrationForm, UploadDatasetForm, DetectionForm, SettingsForm
from ml_models.isolation_forest import IsolationForestModel
from ml_models.autoencoder import AutoEncoderModel
from ml_models.kmeans import KMeansModel
from utils.data_processor import preprocess_data, save_processed_data
from utils.visualizer import generate_overview_charts

logger = logging.getLogger(__name__)

def init_routes(app):
    # Get Started page (entry point)
    @app.route('/')
    def get_started():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        return render_template('index.html')
        
    # Original welcome page (kept for reference)
    @app.route('/original')
    def original_get_started():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        return render_template('get_started.html')

    # Login page
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        logger.debug("Login route accessed. Method: %s", request.method)
        if current_user.is_authenticated:
            logger.debug("User already authenticated, redirecting to home")
            return redirect(url_for('home'))
        
        # For GET requests, redirect to the direct login page
        if request.method == 'GET':
            return redirect(url_for('login_direct'))
        
        # Process POST requests (form submission)
        if request.method == 'POST':
            logger.debug("Login form submitted")
            # Process manual form submission (not using WTForms)
            username = request.form.get('username')
            password = request.form.get('password')
            logger.debug(f"Login attempt for username: {username}")
            
            if username and password:
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    logger.debug("User authenticated successfully")
                    login_user(user)
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('home'))
                else:
                    logger.debug("Authentication failed")
                    flash('Login unsuccessful. Please check username and password', 'danger')
                    return redirect(url_for('login_direct'))
            else:
                logger.debug("Missing username or password")
                flash('Username and password are required', 'danger')
                return redirect(url_for('login_direct'))
        
        # Fallback
        return redirect(url_for('login_direct'))
    
    # Direct login page (alternative)
    @app.route('/login_direct', methods=['GET'])
    def login_direct():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        return render_template('login_direct.html')

    # Registration page (for initial setup)
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        logger.debug("Register route accessed. Method: %s", request.method)
        if current_user.is_authenticated:
            logger.debug("User already authenticated, redirecting to home")
            return redirect(url_for('home'))
        
        # For GET requests, redirect to the direct register page
        if request.method == 'GET':
            return redirect(url_for('register_direct'))
        
        # Process POST requests (form submission)
        if request.method == 'POST':
            logger.debug("Registration form submitted")
            # Process manual form submission (not using WTForms)
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            logger.debug(f"Registration attempt for username: {username}, email: {email}")
            
            if username and email and password and confirm_password:
                if password != confirm_password:
                    flash('Passwords must match', 'danger')
                    return redirect(url_for('register_direct'))
                
                try:
                    user = User(username=username, email=email)
                    user.set_password(password)
                    db.session.add(user)
                    db.session.commit()
                    logger.debug("User created successfully")
                    flash('Your account has been created! You can now log in.', 'success')
                    return redirect(url_for('login_direct'))
                except Exception as e:
                    logger.error("Error creating user: %s", str(e))
                    db.session.rollback()
                    flash(f'Error creating account: {str(e)}', 'danger')
                    return redirect(url_for('register_direct'))
            else:
                logger.debug("Missing required fields")
                flash('All fields are required', 'danger')
                return redirect(url_for('register_direct'))
        
        # Fallback
        return redirect(url_for('register_direct'))
    
    # Direct registration page (alternative)
    @app.route('/register_direct', methods=['GET'])
    def register_direct():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        return render_template('register_direct.html')

    # Logout route
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('get_started'))

    # Home page (after login)
    @app.route('/home')
    @login_required
    def home():
        datasets_count = Dataset.query.filter_by(user_id=current_user.id).count()
        results_count = AnomalyResult.query.filter_by(user_id=current_user.id).count()
        
        # Get latest results for quick access
        recent_results = AnomalyResult.query.filter_by(user_id=current_user.id).order_by(AnomalyResult.creation_date.desc()).limit(5).all()
        
        return render_template('home.html', 
                              datasets_count=datasets_count, 
                              results_count=results_count,
                              recent_results=recent_results)

    # Dashboard page
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get datasets and results for the current user
        datasets = Dataset.query.filter_by(user_id=current_user.id).all()
        results = AnomalyResult.query.filter_by(user_id=current_user.id).all()
        
        # Generate overview data
        overview_data = generate_overview_charts(datasets, results)
        
        return render_template('dashboard.html', 
                              datasets=datasets, 
                              results=results,
                              overview_data=json.dumps(overview_data))

    # Upload Data page
    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    def upload():
        form = UploadDatasetForm()
        preview_data = None
        detected_columns = None
        
        # Handle auto-detect columns button
        if request.method == 'POST' and 'auto_detect' in request.form:
            try:
                file = form.file.data
                if file:
                    # Save the file temporarily
                    filename = secure_filename(file.filename)
                    temp_dir = os.path.join(app.root_path, 'uploads', 'temp')
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_path = os.path.join(temp_dir, filename)
                    file.save(temp_path)
                    
                    # Read the CSV and auto-detect columns
                    df = pd.read_csv(temp_path)
                    
                    # Display a preview of the data
                    preview_data = df.head(5).to_html(classes='table table-striped table-sm')
                    
                    # Detect time column
                    time_column = None
                    for col in df.columns:
                        if any(time_pattern in col.lower() for time_pattern in ['time', 'date', 'timestamp']):
                            time_column = col
                            break
                    
                    # Detect numeric columns (excluding time-related columns)
                    exclude_patterns = ['date', 'time', 'timestamp', 'id', 'index']
                    numeric_cols = [col for col in df.select_dtypes(include=['number']).columns 
                                  if not any(pattern in col.lower() for pattern in exclude_patterns)]
                    
                    detected_columns = {
                        'time_column': time_column,
                        'numeric_columns': numeric_cols
                    }
                    
                    # Update form with detected values
                    if time_column:
                        form.time_column.data = time_column
                    
                    # For value column, suggest the first numeric column that's not time-related
                    if numeric_cols:
                        form.value_column.data = numeric_cols[0]
                        
                    # Keep the file in session for the next submission
                    if not os.path.exists(os.path.join(temp_dir, 'session')):
                        os.makedirs(os.path.join(temp_dir, 'session'), exist_ok=True)
                    session_file_path = os.path.join(temp_dir, 'session', f'{current_user.id}_{filename}')
                    os.replace(temp_path, session_file_path)
                    session['temp_file_path'] = session_file_path
                    session['original_filename'] = filename
                    
                    flash(f'Columns auto-detected from "{filename}". Please review and confirm.', 'info')
                else:
                    flash('Please select a file first', 'warning')
            except Exception as e:
                logger.error(f"Error in auto-detection: {str(e)}")
                flash(f'Error detecting columns: {str(e)}', 'danger')
        
        # Handle form submission for upload
        elif form.validate_on_submit():
            try:
                # Get the file - either from the form or from session if auto-detected
                if 'temp_file_path' in session and os.path.exists(session['temp_file_path']):
                    # Use the file from auto-detection
                    file_path = session['temp_file_path']
                    filename = session['original_filename']
                else:
                    # Save the newly uploaded file
                    file = form.file.data
                    filename = secure_filename(file.filename)
                    
                    # Create uploads directory if it doesn't exist
                    upload_dir = os.path.join(app.root_path, 'uploads', str(current_user.id))
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    file_path = os.path.join(upload_dir, filename)
                    file.save(file_path)
                
                # Read the file to get row count and verify columns
                df = pd.read_csv(file_path)
                row_count = len(df)
                
                # Use provided column names or leave empty for auto-detection later
                time_column = form.time_column.data or None
                value_column = form.value_column.data or None
                
                # If columns were specified, verify they exist
                if time_column and time_column not in df.columns:
                    flash(f'Warning: Time column "{time_column}" not found in the dataset. It will be auto-detected during analysis.', 'warning')
                    time_column = None
                    
                if value_column and value_column not in df.columns:
                    flash(f'Warning: Value column "{value_column}" not found in the dataset. All numeric columns will be used during analysis.', 'warning')
                    value_column = None
                
                # Create dataset record
                dataset = Dataset(
                    filename=filename,
                    description=form.description.data,
                    file_path=file_path,
                    row_count=row_count,
                    time_column=time_column,
                    value_column=value_column,
                    user_id=current_user.id
                )
                
                db.session.add(dataset)
                db.session.commit()
                
                # Clear session data
                if 'temp_file_path' in session:
                    del session['temp_file_path']
                if 'original_filename' in session:
                    del session['original_filename']
                
                flash(f'Dataset "{filename}" uploaded successfully!', 'success')
                return redirect(url_for('upload'))
                
            except Exception as e:
                logger.error(f"Error uploading dataset: {str(e)}")
                flash(f'Error uploading dataset: {str(e)}', 'danger')
        
        # Get existing datasets
        datasets = Dataset.query.filter_by(user_id=current_user.id).all()
        
        return render_template('upload.html', form=form, datasets=datasets, 
                              preview_data=preview_data, detected_columns=detected_columns)

    # Run Detection page
    @app.route('/detection', methods=['GET', 'POST'])
    @login_required
    def detection():
        form = DetectionForm()
        
        # Populate dataset choices
        datasets = Dataset.query.filter_by(user_id=current_user.id).all()
        form.dataset.choices = [(d.id, d.filename) for d in datasets]
        
        if form.validate_on_submit():
            try:
                dataset_id = form.dataset.data
                algorithm = form.algorithm.data
                
                # Get the dataset
                dataset = Dataset.query.get_or_404(dataset_id)
                
                # Read the data from CSV
                df = pd.read_csv(dataset.file_path)
                
                # Minimal processing - let the algorithm handle most preprocessing
                # This allows using all numeric columns for multi-column anomaly detection
                
                # Run the selected algorithm
                if algorithm == 'isolation_forest':
                    model = IsolationForestModel()
                elif algorithm == 'autoencoder':
                    model = AutoEncoderModel()
                elif algorithm == 'kmeans':
                    model = KMeansModel()
                
                logger.info(f"Running {algorithm} on dataset {dataset.filename} (ID: {dataset.id})")
                
                # Get time and value columns (if specified in the dataset)
                time_col = dataset.time_column
                value_col = dataset.value_column
                
                # Use advanced anomaly detection with auto-detection capabilities
                logger.info(f"Using time_column: {time_col}, value_column: {value_col}")
                anomalies, metrics = model.detect_anomalies(df, time_column=time_col, value_column=value_col)
                
                # Save complete result (including all detected anomalies for each feature)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                result_filename = f"{algorithm}_{timestamp}.csv"
                result_dir = os.path.join(app.root_path, 'results', str(current_user.id))
                os.makedirs(result_dir, exist_ok=True)
                
                result_path = os.path.join(result_dir, result_filename)
                anomalies.to_csv(result_path, index=False)
                
                # Log feature importance if available
                if 'feature_importance' in metrics:
                    feature_importance = metrics['feature_importance']
                    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
                    logger.info(f"Feature importance: {sorted_features}")
                
                # Create result record with enhanced metrics
                anomaly_count = int(anomalies['is_anomaly'].sum())
                result = AnomalyResult(
                    algorithm=algorithm,
                    anomaly_count=anomaly_count,
                    result_path=result_path,
                    metrics=metrics,
                    user_id=current_user.id,
                    dataset_id=dataset_id
                )
                
                db.session.add(result)
                db.session.commit()
                
                # Provide more detailed success message
                importance_msg = ""
                if 'feature_importance' in metrics and metrics['feature_importance']:
                    # Get the most important feature
                    top_feature = sorted_features[0][0] if sorted_features else None
                    if top_feature:
                        importance_msg = f" The most significant anomaly contributor was {top_feature}."
                
                flash(f'Anomaly detection completed successfully using {algorithm}! Found {anomaly_count} anomalies in {len(df)} records.{importance_msg}', 'success')
                return redirect(url_for('results', result_id=result.id))
                
            except Exception as e:
                logger.error(f"Error running detection: {str(e)}")
                flash(f'Error running detection: {str(e)}', 'danger')
        
        return render_template('detection.html', form=form)

    # Results page
    @app.route('/results')
    @login_required
    def results():
        # Get all results or specific result if ID provided
        result_id = request.args.get('result_id')
        
        if result_id:
            result = AnomalyResult.query.get_or_404(result_id)
            if result.user_id != current_user.id:
                flash('You do not have permission to view this result', 'danger')
                return redirect(url_for('results'))
            
            results = [result]
        else:
            results = AnomalyResult.query.filter_by(user_id=current_user.id).order_by(AnomalyResult.creation_date.desc()).all()
        
        return render_template('results.html', results=results, selected_id=result_id)

    # AJAX endpoint to get result data for visualization
    @app.route('/api/result/<int:result_id>')
    @login_required
    def get_result_data(result_id):
        result = AnomalyResult.query.get_or_404(result_id)
        
        if result.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Load the result data
        df = pd.read_csv(result.result_path)
        
        # Prepare data for visualizations - handle both single and multi-column cases
        time_series_data = {}
        dataset = result.dataset
        
        # Auto-detect time column if not specified
        time_column = dataset.time_column
        if not time_column:
            # Find a time-related column
            for col in df.columns:
                if any(time_pattern in col.lower() for time_pattern in ['time', 'date', 'timestamp']):
                    time_column = col
                    break
            # If still not found, use the index
            if not time_column and 'index' in df.columns:
                time_column = 'index'
        
        # If we have a time column, use it for timestamps
        if time_column and time_column in df.columns:
            time_series_data['timestamps'] = df[time_column].tolist()
        else:
            # Generate sequential timestamps
            time_series_data['timestamps'] = list(range(len(df)))
        
        # Get main anomaly data
        time_series_data['anomalies'] = df['is_anomaly'].tolist()
        
        # Add value column data if specified
        value_column = dataset.value_column
        if value_column and value_column in df.columns:
            time_series_data['values'] = df[value_column].tolist()
            
            # Add column-specific anomaly data if available
            column_key = f'{value_column}_anomaly'
            if column_key in df.columns:
                time_series_data[f'{value_column}_anomalies'] = df[column_key].tolist()
        
        # For multi-column case, detect all feature-specific anomaly columns
        feature_columns = {}
        for col in df.columns:
            if col.endswith('_anomaly'):
                base_col = col.replace('_anomaly', '')
                if base_col in df.columns:
                    # Only include if the base column also exists
                    feature_columns[base_col] = {
                        'values': df[base_col].tolist(),
                        'anomalies': df[col].tolist()
                    }
        
        # Get feature importance from metrics if available
        feature_importance = {}
        if result.metrics and isinstance(result.metrics, dict):
            if 'feature_importance' in result.metrics:
                feature_importance = result.metrics['feature_importance']
            
            # Add anomaly details if available
            anomaly_details = {}
            if 'anomaly_details' in result.metrics:
                anomaly_details = result.metrics['anomaly_details']
            
        return jsonify({
            'time_series': time_series_data,
            'feature_columns': feature_columns,
            'feature_importance': feature_importance, 
            'anomaly_details': anomaly_details,
            'metrics': result.metrics,
            'anomaly_count': result.anomaly_count,
            'algorithm': result.algorithm
        })

    # Model Insights page
    @app.route('/model-insights')
    @login_required
    def model_insights():
        # Get all results grouped by algorithm
        results_by_algorithm = {}
        
        algorithms = ['isolation_forest', 'autoencoder', 'kmeans']
        for algo in algorithms:
            results_by_algorithm[algo] = AnomalyResult.query.filter_by(
                user_id=current_user.id, 
                algorithm=algo
            ).order_by(AnomalyResult.creation_date.desc()).all()
        
        return render_template('model_insights.html', results_by_algorithm=results_by_algorithm)

    # Recommendations page
    @app.route('/recommendations')
    @login_required
    def recommendations():
        # Get latest results for recommendation generation
        recent_results = AnomalyResult.query.filter_by(user_id=current_user.id).order_by(AnomalyResult.creation_date.desc()).limit(5).all()
        
        return render_template('recommendations.html', results=recent_results)

    # Settings page
    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        form = SettingsForm()
        
        if request.method == 'GET':
            form.email.data = current_user.email
        
        if form.validate_on_submit():
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect', 'danger')
                return render_template('settings.html', form=form)
            
            current_user.email = form.email.data
            
            if form.new_password.data:
                current_user.set_password(form.new_password.data)
            
            db.session.commit()
            flash('Your settings have been updated!', 'success')
            return redirect(url_for('settings'))
        
        return render_template('settings.html', form=form)

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
