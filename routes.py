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
        return render_template('get_started.html')

    # Login page
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        logger.debug("Login route accessed. Method: %s", request.method)
        if current_user.is_authenticated:
            logger.debug("User already authenticated, redirecting to home")
            return redirect(url_for('home'))
        
        form = LoginForm()
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
            else:
                logger.debug("Missing username or password")
                flash('Username and password are required', 'danger')
        
        return render_template('login.html', form=form)
    
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
        
        form = RegistrationForm()
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
                    return render_template('register_direct.html')
                
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
            else:
                logger.debug("Missing required fields")
                flash('All fields are required', 'danger')
        
        return render_template('login.html', form=form, register=True)
    
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
        
        if form.validate_on_submit():
            try:
                # Save the uploaded file
                file = form.file.data
                filename = secure_filename(file.filename)
                
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join(app.root_path, 'uploads', str(current_user.id))
                os.makedirs(upload_dir, exist_ok=True)
                
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                
                # Read the file to get row count
                df = pd.read_csv(file_path)
                row_count = len(df)
                
                # Create dataset record
                dataset = Dataset(
                    filename=filename,
                    description=form.description.data,
                    file_path=file_path,
                    row_count=row_count,
                    time_column=form.time_column.data,
                    value_column=form.value_column.data,
                    user_id=current_user.id
                )
                
                db.session.add(dataset)
                db.session.commit()
                
                flash(f'Dataset "{filename}" uploaded successfully!', 'success')
                return redirect(url_for('upload'))
                
            except Exception as e:
                logger.error(f"Error uploading dataset: {str(e)}")
                flash(f'Error uploading dataset: {str(e)}', 'danger')
        
        # Get existing datasets
        datasets = Dataset.query.filter_by(user_id=current_user.id).all()
        
        return render_template('upload.html', form=form, datasets=datasets)

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
                
                # Process the data
                df = pd.read_csv(dataset.file_path)
                processed_df = preprocess_data(df, dataset.time_column, dataset.value_column)
                
                # Run the selected algorithm
                if algorithm == 'isolation_forest':
                    model = IsolationForestModel()
                elif algorithm == 'autoencoder':
                    model = AutoEncoderModel()
                elif algorithm == 'kmeans':
                    model = KMeansModel()
                
                # Train and get results
                time_col = dataset.time_column
                value_col = dataset.value_column
                if time_col in processed_df.columns and value_col in processed_df.columns:
                    anomalies, metrics = model.detect_anomalies(processed_df, time_column=time_col, value_column=value_col)
                else:
                    anomalies, metrics = model.detect_anomalies(processed_df)
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                result_filename = f"{algorithm}_{timestamp}.csv"
                result_dir = os.path.join(app.root_path, 'results', str(current_user.id))
                os.makedirs(result_dir, exist_ok=True)
                
                result_path = os.path.join(result_dir, result_filename)
                anomalies.to_csv(result_path, index=False)
                
                # Create result record
                result = AnomalyResult(
                    algorithm=algorithm,
                    anomaly_count=len(anomalies[anomalies['is_anomaly'] == 1]),
                    result_path=result_path,
                    metrics=metrics,
                    user_id=current_user.id,
                    dataset_id=dataset_id
                )
                
                db.session.add(result)
                db.session.commit()
                
                flash(f'Anomaly detection completed successfully using {algorithm}!', 'success')
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
        
        # Prepare data for visualizations
        time_series_data = {
            'timestamps': df[result.dataset.time_column].tolist(),
            'values': df[result.dataset.value_column].tolist(),
            'anomalies': df['is_anomaly'].tolist()
        }
        
        # Additional metrics
        metrics = result.metrics
        
        return jsonify({
            'time_series': time_series_data,
            'metrics': metrics,
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
