import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

def generate_overview_charts(datasets, results):
    """
    Generate overview data for dashboard charts.
    
    Parameters:
    -----------
    datasets : list
        List of Dataset objects
    results : list
        List of AnomalyResult objects
        
    Returns:
    --------
    overview_data : dict
        Dictionary with chart data for the dashboard
    """
    overview_data = {}
    
    # Data summary
    overview_data['dataset_count'] = len(datasets)
    overview_data['result_count'] = len(results)
    
    # Datasets over time
    if datasets:
        dataset_dates = [ds.upload_date for ds in datasets]
        dataset_counts = pd.Series(dataset_dates).dt.date.value_counts().sort_index()
        
        overview_data['datasets_over_time'] = {
            'labels': [str(date) for date in dataset_counts.index],
            'values': dataset_counts.values.tolist()
        }
    else:
        overview_data['datasets_over_time'] = {
            'labels': [],
            'values': []
        }
    
    # Results by algorithm
    if results:
        algorithm_counts = pd.Series([r.algorithm for r in results]).value_counts()
        
        overview_data['results_by_algorithm'] = {
            'labels': algorithm_counts.index.tolist(),
            'values': algorithm_counts.values.tolist()
        }
    else:
        overview_data['results_by_algorithm'] = {
            'labels': [],
            'values': []
        }
    
    # Anomaly distribution by hour (using latest result if available)
    if results:
        latest_result = max(results, key=lambda r: r.creation_date)
        
        try:
            # Load result data
            result_df = pd.read_csv(latest_result.result_path)
            
            # Get dataset for time column
            dataset = latest_result.dataset
            
            # Convert time column to datetime
            if not pd.api.types.is_datetime64_any_dtype(result_df[dataset.time_column]):
                result_df[dataset.time_column] = pd.to_datetime(result_df[dataset.time_column])
            
            # Group anomalies by hour
            result_df['hour'] = result_df[dataset.time_column].dt.hour
            anomalies_by_hour = result_df[result_df['is_anomaly'] == 1]['hour'].value_counts().sort_index()
            
            # Generate all hours (0-23) to ensure complete data
            all_hours = pd.Series(range(24), name='hour')
            anomalies_by_hour = anomalies_by_hour.reindex(all_hours, fill_value=0)
            
            overview_data['anomalies_by_hour'] = {
                'labels': list(range(24)),
                'values': anomalies_by_hour.values.tolist()
            }
        except Exception as e:
            # Fallback if there's an error
            overview_data['anomalies_by_hour'] = {
                'labels': list(range(24)),
                'values': [0] * 24
            }
    else:
        overview_data['anomalies_by_hour'] = {
            'labels': list(range(24)),
            'values': [0] * 24
        }
    
    # Generate model performance data if metrics are available
    if results:
        metrics_data = {
            'algorithms': [],
            'precision': [],
            'recall': [],
            'f1_score': []
        }
        
        for algorithm in ['isolation_forest', 'autoencoder', 'kmeans']:
            # Filter results by algorithm
            algo_results = [r for r in results if r.algorithm == algorithm]
            
            if algo_results:
                # Get the latest result for this algorithm
                latest = max(algo_results, key=lambda r: r.creation_date)
                
                # Add metrics if available
                if latest.metrics:
                    metrics = latest.metrics
                    metrics_data['algorithms'].append(algorithm)
                    metrics_data['precision'].append(metrics.get('precision', 0))
                    metrics_data['recall'].append(metrics.get('recall', 0))
                    metrics_data['f1_score'].append(metrics.get('f1_score', 0))
        
        overview_data['model_performance'] = metrics_data
    else:
        overview_data['model_performance'] = {
            'algorithms': [],
            'precision': [],
            'recall': [],
            'f1_score': []
        }
    
    return overview_data

def generate_result_visualizations(result, dataset):
    """
    Generate visualization data for a specific result.
    
    Parameters:
    -----------
    result : AnomalyResult
        AnomalyResult object
    dataset : Dataset
        Dataset object associated with the result
        
    Returns:
    --------
    visualization_data : dict
        Dictionary with visualization data for the result
    """
    visualization_data = {}
    
    try:
        # Load result data
        result_df = pd.read_csv(result.result_path)
        
        # Convert time column to datetime
        if not pd.api.types.is_datetime64_any_dtype(result_df[dataset.time_column]):
            result_df[dataset.time_column] = pd.to_datetime(result_df[dataset.time_column])
        
        # Time series data with anomalies
        time_series = {
            'timestamps': result_df[dataset.time_column].astype(str).tolist(),
            'values': result_df[dataset.value_column].tolist(),
            'anomalies': result_df['is_anomaly'].tolist(),
            'anomaly_scores': result_df['anomaly_score'].tolist() if 'anomaly_score' in result_df.columns else []
        }
        visualization_data['time_series'] = time_series
        
        # Anomaly distribution by time
        if 'hour' not in result_df.columns:
            result_df['hour'] = result_df[dataset.time_column].dt.hour
            
        if 'day_of_week' not in result_df.columns:
            result_df['day_of_week'] = result_df[dataset.time_column].dt.dayofweek
            
        if 'month' not in result_df.columns:
            result_df['month'] = result_df[dataset.time_column].dt.month
        
        # Anomalies by hour
        anomalies_by_hour = result_df[result_df['is_anomaly'] == 1]['hour'].value_counts().sort_index()
        all_hours = pd.Series(range(24), name='hour')
        anomalies_by_hour = anomalies_by_hour.reindex(all_hours, fill_value=0)
        
        visualization_data['anomalies_by_hour'] = {
            'labels': list(range(24)),
            'values': anomalies_by_hour.values.tolist()
        }
        
        # Anomalies by day of week
        dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        anomalies_by_dow = result_df[result_df['is_anomaly'] == 1]['day_of_week'].value_counts().sort_index()
        all_dows = pd.Series(range(7), name='day_of_week')
        anomalies_by_dow = anomalies_by_dow.reindex(all_dows, fill_value=0)
        
        visualization_data['anomalies_by_dow'] = {
            'labels': dow_names,
            'values': anomalies_by_dow.values.tolist()
        }
        
        # Algorithm metrics
        if result.metrics:
            visualization_data['metrics'] = result.metrics
        
    except Exception as e:
        # Return error information
        visualization_data['error'] = str(e)
    
    return visualization_data

def generate_recommendations(results):
    """
    Generate recommendations based on detected anomalies.
    
    Parameters:
    -----------
    results : list
        List of AnomalyResult objects
        
    Returns:
    --------
    recommendations : list
        List of recommendation dictionaries
    """
    recommendations = []
    
    if not results:
        return recommendations
    
    try:
        # Get the latest result
        latest_result = max(results, key=lambda r: r.creation_date)
        result_df = pd.read_csv(latest_result.result_path)
        dataset = latest_result.dataset
        
        # Ensure datetime conversion
        if not pd.api.types.is_datetime64_any_dtype(result_df[dataset.time_column]):
            result_df[dataset.time_column] = pd.to_datetime(result_df[dataset.time_column])
        
        # Add hour if not present
        if 'hour' not in result_df.columns:
            result_df['hour'] = result_df[dataset.time_column].dt.hour
            
        # Filter anomalies
        anomalies = result_df[result_df['is_anomaly'] == 1]
        
        if len(anomalies) > 0:
            # Check for patterns in anomalies
            
            # 1. Check for time-based patterns
            hour_counts = anomalies['hour'].value_counts()
            peak_hours = hour_counts[hour_counts > hour_counts.mean()].index.tolist()
            
            if peak_hours:
                peak_hours_str = ', '.join([f"{h}:00" for h in sorted(peak_hours)])
                recommendations.append({
                    'title': 'Time-based Anomaly Pattern Detected',
                    'description': f'Energy anomalies occur frequently during these hours: {peak_hours_str}. '
                                   f'Consider investigating equipment operation during these times.',
                    'type': 'time_pattern'
                })
            
            # 2. Check for intensity-based patterns
            if 'anomaly_score' in anomalies.columns:
                high_score_anomalies = anomalies[anomalies['anomaly_score'] > anomalies['anomaly_score'].quantile(0.75)]
                
                if len(high_score_anomalies) > 0:
                    recommendations.append({
                        'title': 'High Severity Anomalies Detected',
                        'description': f'Found {len(high_score_anomalies)} high-severity anomalies that significantly '
                                       f'deviate from normal patterns. Prioritize investigation of these incidents.',
                        'type': 'intensity'
                    })
            
            # 3. General recommendations based on anomaly count
            anomaly_percentage = (len(anomalies) / len(result_df)) * 100
            
            if anomaly_percentage > 10:
                recommendations.append({
                    'title': 'High Anomaly Rate Detected',
                    'description': f'Your system shows an unusually high anomaly rate ({anomaly_percentage:.2f}%). '
                                   f'Consider reviewing overall system operation and maintenance schedules.',
                    'type': 'frequency'
                })
            elif anomaly_percentage > 5:
                recommendations.append({
                    'title': 'Moderate Anomaly Rate',
                    'description': f'Your system shows a moderate anomaly rate ({anomaly_percentage:.2f}%). '
                                   f'Regular monitoring and preventive maintenance is recommended.',
                    'type': 'frequency'
                })
            
            # 4. Recommendation based on the algorithm used
            if latest_result.algorithm == 'isolation_forest':
                recommendations.append({
                    'title': 'Algorithm Recommendation',
                    'description': 'Isolation Forest works well for identifying global anomalies. '
                                   'For more context-aware detection, consider trying the AutoEncoder model.',
                    'type': 'algorithm'
                })
            elif latest_result.algorithm == 'autoencoder':
                recommendations.append({
                    'title': 'Algorithm Recommendation',
                    'description': 'AutoEncoder is effective for complex patterns. '
                                   'For faster detection on larger datasets, consider Isolation Forest.',
                    'type': 'algorithm'
                })
            elif latest_result.algorithm == 'kmeans':
                recommendations.append({
                    'title': 'Algorithm Recommendation',
                    'description': 'K-Means clustering works well for separated patterns. '
                                   'For more robust detection of subtle anomalies, try AutoEncoder.',
                    'type': 'algorithm'
                })
        else:
            recommendations.append({
                'title': 'No Anomalies Detected',
                'description': 'No anomalies were detected with the current algorithm and settings. '
                               'Consider adjusting sensitivity parameters or trying a different algorithm.',
                'type': 'general'
            })
    
    except Exception as e:
        recommendations.append({
            'title': 'Error Generating Recommendations',
            'description': f'An error occurred while generating recommendations: {str(e)}',
            'type': 'error'
        })
    
    return recommendations
