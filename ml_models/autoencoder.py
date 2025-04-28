import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.metrics import precision_score, recall_score, f1_score

class AutoEncoderModel:
    def __init__(self, threshold_percentile=95, n_components=3):
        """
        Initialize a PCA-based Autoencoder model for anomaly detection.
        
        Parameters:
        -----------
        threshold_percentile : int, default=95
            Percentile to use for defining the anomaly threshold
        n_components : int, default=3
            Number of principal components to keep
        """
        self.threshold_percentile = threshold_percentile
        self.n_components = n_components
        self.scaler = MinMaxScaler()
        self.model = PCA(n_components=n_components)
        self.threshold = None
        
    def detect_anomalies(self, df, time_column='timestamp', value_column='value'):
        """
        Detect anomalies in the time series data using PCA reconstruction error.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Input dataframe with time series data
        time_column : str, default='timestamp'
            Column name of the timestamps
        value_column : str, default='value'
            Column name of the energy consumption values
            
        Returns:
        --------
        result_df : pandas.DataFrame
            Dataframe with the original data and anomaly predictions
        metrics : dict
            Dictionary with performance metrics
        """
        try:
            # Make a copy of the dataframe to avoid modifying the original
            df_copy = df.copy()
            
            # Handle missing or invalid columns
            if value_column not in df_copy.columns:
                # Try to find a suitable numeric column if value_column is not found
                numeric_cols = df_copy.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    value_column = numeric_cols[0]
                    print(f"Value column '{value_column}' not found. Using '{value_column}' instead.")
                else:
                    raise ValueError(f"No suitable numeric columns found in the dataframe")
            
            # Clean the data - replace infinity values and handle NaNs
            df_copy[value_column] = df_copy[value_column].replace([np.inf, -np.inf], np.nan)
            
            # Fill NaN values with median (more robust than mean for outliers)
            median_value = df_copy[value_column].median()
            if pd.isna(median_value): # If median is NaN (all values are NaN)
                df_copy[value_column] = df_copy[value_column].fillna(0)
            else:
                df_copy[value_column] = df_copy[value_column].fillna(median_value)
            
            # Check for extreme values and clip if necessary
            mean_val = df_copy[value_column].mean()
            std_val = df_copy[value_column].std()
            if not pd.isna(std_val) and std_val > 0:
                lower_bound = mean_val - 5 * std_val
                upper_bound = mean_val + 5 * std_val
                df_copy[value_column] = df_copy[value_column].clip(lower_bound, upper_bound)
            
            # Extract and scale data with error handling
            try:
                data = df_copy[value_column].values.reshape(-1, 1)
                data_scaled = self.scaler.fit_transform(data)
            except Exception as e:
                print(f"Error during data scaling: {str(e)}. Using normalized data.")
                # If scaling fails, use simple normalization
                data = df_copy[value_column].values.reshape(-1, 1)
                data_max = np.max(np.abs(data))
                if data_max > 0:
                    data_scaled = data / data_max
                else:
                    data_scaled = data
            
            # Create time-based features with robust error handling
            window_sizes = [3, 6, 12, 24]
            features = [data_scaled]
            
            try:
                for w in window_sizes:
                    # Add rolling mean with safe handling
                    try:
                        roll_mean = pd.Series(data_scaled.flatten()).rolling(window=w, min_periods=1).mean().values
                        features.append(roll_mean.reshape(-1, 1))
                    except Exception as e:
                        print(f"Error calculating rolling mean for window {w}: {str(e)}")
                        # Add a fallback feature
                        features.append(data_scaled)
                    
                    # Add rolling std with safe handling
                    try:
                        roll_std = pd.Series(data_scaled.flatten()).rolling(window=w, min_periods=1).std().fillna(0).values
                        features.append(roll_std.reshape(-1, 1))
                    except Exception as e:
                        print(f"Error calculating rolling std for window {w}: {str(e)}")
                        # Add a fallback feature (zeros)
                        features.append(np.zeros_like(data_scaled))
            except Exception as e:
                print(f"Error creating window features: {str(e)}. Using only original features.")
                features = [data_scaled]
            
            # Combine features, handling any NaN values
            try:
                X = np.hstack([f for f in features])
                X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            except Exception as e:
                print(f"Error combining features: {str(e)}. Using only original data.")
                X = np.nan_to_num(data_scaled, nan=0.0, posinf=0.0, neginf=0.0)
            
            # Ensure data has enough samples for PCA
            effective_n_components = min(self.n_components, X.shape[0] - 1, X.shape[1])
            if effective_n_components < 1:
                effective_n_components = 1
            
            # Update model if necessary
            if effective_n_components != self.n_components:
                print(f"Adjusting PCA components from {self.n_components} to {effective_n_components}")
                self.model = PCA(n_components=effective_n_components)
            
            # Fit PCA model with error handling
            try:
                self.model.fit(X)
                
                # Transform data to reduced dimension and back to calculate reconstruction error
                X_reduced = self.model.transform(X)
                X_reconstructed = self.model.inverse_transform(X_reduced)
                
                # Calculate reconstruction error
                mse = np.mean(np.square(X - X_reconstructed), axis=1)
            except Exception as e:
                print(f"Error in PCA decomposition: {str(e)}. Using simplified anomaly detection.")
                # Fallback to a simpler approach - z-score based
                mse = np.zeros(len(X))
                for col_idx in range(X.shape[1]):
                    col_data = X[:, col_idx]
                    col_mean = np.mean(col_data)
                    col_std = np.std(col_data)
                    if col_std > 0:
                        z_scores = np.abs((col_data - col_mean) / col_std)
                        mse += z_scores
                
                # Normalize scores
                if np.max(mse) > 0:
                    mse = mse / np.max(mse)
            
            # Safely determine threshold based on percentile
            try:
                self.threshold = np.percentile(mse, self.threshold_percentile)
            except Exception as e:
                print(f"Error calculating threshold: {str(e)}. Using default threshold.")
                self.threshold = np.mean(mse) + 2 * np.std(mse)
            
            # Identify anomalies
            anomalies = (mse > self.threshold).astype(int)
            
            # Create result dataframe
            result_df = df_copy.copy()
            
            # Initialize columns
            result_df['is_anomaly'] = anomalies
            result_df['anomaly_score'] = mse
            
            # Calculate metrics with robust error handling
            try:
                # Create synthetic labels for evaluation
                synthetic_labels = np.zeros(len(df_copy))
                value_data = df_copy[value_column].fillna(df_copy[value_column].median())
                value_threshold = np.percentile(value_data, 95)
                synthetic_labels[df_copy[value_column] > value_threshold] = 1
                
                metrics = {
                    'precision': float(precision_score(synthetic_labels, anomalies, zero_division=0)),
                    'recall': float(recall_score(synthetic_labels, anomalies, zero_division=0)),
                    'f1_score': float(f1_score(synthetic_labels, anomalies, zero_division=0)),
                    'anomaly_count': int(np.sum(anomalies)),
                    'total_points': len(anomalies),
                    'threshold': float(self.threshold),
                    'n_components': int(effective_n_components)
                }
            except Exception as e:
                print(f"Error calculating metrics: {str(e)}. Using basic metrics only.")
                metrics = {
                    'anomaly_count': int(np.sum(anomalies)),
                    'total_points': len(anomalies),
                    'threshold': float(self.threshold),
                    'n_components': int(effective_n_components)
                }
                
        except Exception as e:
            # Last resort fallback
            print(f"Critical error in anomaly detection: {str(e)}. Using simple outlier detection.")
            result_df = df.copy()
            
            # Implement a very basic outlier detection method
            if value_column in df.columns:
                values = df[value_column].replace([np.inf, -np.inf], np.nan).fillna(0).values
                mean_val = np.mean(values)
                std_val = np.std(values)
                if std_val > 0:
                    z_scores = np.abs((values - mean_val) / std_val)
                    threshold = np.percentile(z_scores, 95)
                    basic_anomalies = (z_scores > threshold).astype(int)
                    result_df['anomaly_score'] = z_scores
                else:
                    basic_anomalies = np.zeros(len(df))
                    result_df['anomaly_score'] = np.zeros(len(df))
                
                result_df['is_anomaly'] = basic_anomalies
            else:
                # If value column doesn't exist, just mark everything as normal
                result_df['is_anomaly'] = 0
                result_df['anomaly_score'] = 0
            
            metrics = {
                'anomaly_count': int(np.sum(result_df['is_anomaly'])),
                'total_points': len(df),
                'threshold': float(np.percentile(result_df['anomaly_score'], 95)) if std_val > 0 else 0,
                'note': 'Used emergency fallback method due to critical error'
            }
        
        return result_df, metrics
