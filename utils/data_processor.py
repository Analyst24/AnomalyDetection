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
    
    # Replace infinity values with NaN first
    processed_df = processed_df.replace([np.inf, -np.inf], np.nan)
    
    # Ensure the specified columns exist
    if time_column not in processed_df.columns:
        # Try to auto-detect a time column
        possible_time_cols = [col for col in processed_df.columns if 
                              any(time_str in col.lower() for time_str in 
                                  ['time', 'date', 'timestamp', 'period'])]
        if possible_time_cols:
            time_column = possible_time_cols[0]
            print(f"Auto-detected time column: {time_column}")
        else:
            raise ValueError(f"Time column '{time_column}' not found and could not auto-detect any time column")
    
    if value_column not in processed_df.columns:
        # Try to auto-detect a numeric value column
        numeric_cols = processed_df.select_dtypes(include=['number']).columns.tolist()
        # Exclude columns that are likely to be categorical or IDs
        exclude_patterns = ['id', 'code', 'category', 'type', 'class', 'year']
        value_candidates = [col for col in numeric_cols if not any(pattern in col.lower() for pattern in exclude_patterns)]
        
        if value_candidates:
            value_column = value_candidates[0]
            print(f"Auto-detected value column: {value_column}")
        else:
            raise ValueError(f"Value column '{value_column}' not found and could not auto-detect any suitable value column")
    
    # Convert time column to datetime if it's not already
    try:
        if not pd.api.types.is_datetime64_any_dtype(processed_df[time_column]):
            processed_df[time_column] = pd.to_datetime(processed_df[time_column], errors='coerce')
    except Exception as e:
        print(f"Error converting time column to datetime: {str(e)}. Using original column.")
    
    # Drop rows with invalid timestamps
    processed_df = processed_df.dropna(subset=[time_column])
    
    # Handle missing values in the value column
    if processed_df[value_column].isna().any():
        try:
            # Fill missing values with interpolation
            processed_df[value_column] = processed_df[value_column].interpolate(method='linear')
            # If any NaN values remain (at the edges), use forward and backward fill
            processed_df[value_column] = processed_df[value_column].fillna(method='ffill').fillna(method='bfill')
            # If there are still NaNs (possible if all values are NaN), fill with zeros
            processed_df[value_column] = processed_df[value_column].fillna(0)
        except Exception as e:
            print(f"Error handling missing values: {str(e)}. Using simple fill.")
            processed_df[value_column] = processed_df[value_column].fillna(processed_df[value_column].median() 
                                                                 if not processed_df[value_column].isna().all() else 0)
    
    # Sort by timestamp
    try:
        processed_df = processed_df.sort_values(by=time_column)
    except Exception as e:
        print(f"Error sorting by time column: {str(e)}. Continuing without sorting.")
    
    # Remove duplicates
    try:
        processed_df = processed_df.drop_duplicates(subset=[time_column])
    except Exception as e:
        print(f"Error removing duplicates: {str(e)}. Continuing with possible duplicates.")
    
    # Handle outliers robustly - cap values at 5 standard deviations from the mean
    try:
        # Get value column as numeric, forcing conversion if needed
        numeric_values = pd.to_numeric(processed_df[value_column], errors='coerce')
        numeric_values = numeric_values.fillna(numeric_values.median() if not numeric_values.isna().all() else 0)
        
        # Calculate robust statistics
        mean = numeric_values.mean()
        std = numeric_values.std()
        
        if not np.isnan(mean) and not np.isnan(std) and std > 0:
            lower_bound = mean - 5 * std
            upper_bound = mean + 5 * std
            
            # Cap extreme values (store original values for reference)
            processed_df['original_value'] = processed_df[value_column]
            processed_df[value_column] = np.clip(numeric_values, lower_bound, upper_bound)
        else:
            # If we can't calculate meaningful bounds, just store original values
            processed_df['original_value'] = processed_df[value_column]
            # Ensure the value column is numeric
            processed_df[value_column] = numeric_values
    except Exception as e:
        print(f"Error handling outliers: {str(e)}. Continuing with original values.")
        processed_df['original_value'] = processed_df[value_column]
    
    # Extract time-based features with error handling
    try:
        processed_df['hour'] = processed_df[time_column].dt.hour
        processed_df['day_of_week'] = processed_df[time_column].dt.dayofweek
        processed_df['month'] = processed_df[time_column].dt.month
        processed_df['is_weekend'] = (processed_df['day_of_week'] >= 5).astype(int)
    except Exception as e:
        print(f"Error extracting time features: {str(e)}. Skipping time feature extraction.")
    
    # Add lagged features with error handling
    try:
        for lag in [1, 6, 12, 24]:
            processed_df[f'lag_{lag}'] = processed_df[value_column].shift(lag).fillna(0)
    except Exception as e:
        print(f"Error creating lag features: {str(e)}. Skipping lag features.")
    
    # Add rolling statistics with error handling
    try:
        processed_df['rolling_mean_24h'] = processed_df[value_column].rolling(window=24, min_periods=1).mean().fillna(0)
        processed_df['rolling_std_24h'] = processed_df[value_column].rolling(window=24, min_periods=1).std().fillna(0)
    except Exception as e:
        print(f"Error calculating rolling statistics: {str(e)}. Skipping rolling statistics.")
        
    # Final check for any remaining infinities or NaNs across the entire dataframe
    processed_df = processed_df.replace([np.inf, -np.inf], np.nan)
    numeric_cols = processed_df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        if processed_df[col].isna().any():
            processed_df[col] = processed_df[col].fillna(0)
    
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
