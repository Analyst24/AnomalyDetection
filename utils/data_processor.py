import os
import pandas as pd
import numpy as np
from datetime import datetime

def preprocess_data(df, time_column, value_column):
    """
    Preprocess time series data for anomaly detection.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input dataframe with time series data
    time_column : str
        Column name containing timestamps
    value_column : str
        Column name containing energy consumption values
        
    Returns:
    --------
    processed_df : pandas.DataFrame
        Preprocessed dataframe
    """
    # Make a copy to avoid modifying the original
    processed_df = df.copy()
    
    # Convert time column to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(processed_df[time_column]):
        processed_df[time_column] = pd.to_datetime(processed_df[time_column], errors='coerce')
    
    # Drop rows with invalid timestamps
    processed_df = processed_df.dropna(subset=[time_column])
    
    # Handle missing values in the value column
    if processed_df[value_column].isna().any():
        # Fill missing values with interpolation
        processed_df[value_column] = processed_df[value_column].interpolate(method='linear')
    
    # Sort by timestamp
    processed_df = processed_df.sort_values(by=time_column)
    
    # Remove duplicates
    processed_df = processed_df.drop_duplicates(subset=[time_column])
    
    # Handle outliers - cap values at 3 standard deviations from the mean
    mean = processed_df[value_column].mean()
    std = processed_df[value_column].std()
    lower_bound = mean - 3 * std
    upper_bound = mean + 3 * std
    
    # Cap extreme values (store original values for reference)
    processed_df['original_value'] = processed_df[value_column]
    processed_df[value_column] = np.clip(processed_df[value_column], lower_bound, upper_bound)
    
    # Extract time-based features
    processed_df['hour'] = processed_df[time_column].dt.hour
    processed_df['day_of_week'] = processed_df[time_column].dt.dayofweek
    processed_df['month'] = processed_df[time_column].dt.month
    processed_df['is_weekend'] = (processed_df['day_of_week'] >= 5).astype(int)
    
    # Add lagged features
    for lag in [1, 6, 12, 24]:
        processed_df[f'lag_{lag}'] = processed_df[value_column].shift(lag).fillna(0)
    
    # Add rolling statistics
    processed_df['rolling_mean_24h'] = processed_df[value_column].rolling(window=24, min_periods=1).mean()
    processed_df['rolling_std_24h'] = processed_df[value_column].rolling(window=24, min_periods=1).std().fillna(0)
    
    return processed_df

def save_processed_data(df, output_path):
    """
    Save preprocessed data to a CSV file.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Processed dataframe to save
    output_path : str
        Path to save the CSV file
        
    Returns:
    --------
    str
        Path to the saved file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    return output_path

def generate_sample_data(n_samples=1000, anomaly_percentage=5):
    """
    Generate sample energy consumption data for testing.
    
    Parameters:
    -----------
    n_samples : int, default=1000
        Number of data points to generate
    anomaly_percentage : int, default=5
        Percentage of data points that should be anomalies
        
    Returns:
    --------
    df : pandas.DataFrame
        DataFrame with generated sample data
    """
    # Generate timestamps
    start_date = datetime(2023, 1, 1)
    timestamps = pd.date_range(start=start_date, periods=n_samples, freq='H')
    
    # Generate normal consumption values with daily and weekly patterns
    hour_effect = np.sin(np.arange(0, n_samples) % 24 * (2 * np.pi / 24)) * 20 + 50
    weekly_effect = np.sin(np.arange(0, n_samples) % (24*7) * (2 * np.pi / (24*7))) * 10
    random_noise = np.random.normal(0, 5, n_samples)
    
    # Combine effects
    values = hour_effect + weekly_effect + random_noise
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'energy_consumption': values
    })
    
    # Add some anomalies
    n_anomalies = int(n_samples * anomaly_percentage / 100)
    anomaly_indices = np.random.choice(range(n_samples), n_anomalies, replace=False)
    
    # Introduce different types of anomalies
    for idx in anomaly_indices:
        anomaly_type = np.random.choice(['spike', 'dip', 'level_shift'])
        
        if anomaly_type == 'spike':
            df.loc[idx, 'energy_consumption'] += np.random.uniform(40, 100)
        elif anomaly_type == 'dip':
            df.loc[idx, 'energy_consumption'] -= np.random.uniform(30, 50)
        elif anomaly_type == 'level_shift':
            shift_length = np.random.randint(5, 15)
            shift_value = np.random.uniform(30, 50) * np.random.choice([-1, 1])
            end_idx = min(idx + shift_length, n_samples - 1)
            df.loc[idx:end_idx, 'energy_consumption'] += shift_value
    
    return df
