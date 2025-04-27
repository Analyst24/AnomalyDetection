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
        # Extract and scale data
        data = df[value_column].values.reshape(-1, 1)
        data_scaled = self.scaler.fit_transform(data)
        
        # Create time-based features for more context
        # Use a rolling window approach to capture temporal patterns
        window_sizes = [3, 6, 12, 24]
        features = [data_scaled]
        
        for w in window_sizes:
            # Add rolling mean
            roll_mean = pd.Series(data_scaled.flatten()).rolling(window=w).mean().values
            # Add rolling std
            roll_std = pd.Series(data_scaled.flatten()).rolling(window=w).std().values
            
            features.append(roll_mean.reshape(-1, 1))
            features.append(roll_std.reshape(-1, 1))
        
        # Combine features, ignoring NaN values from the beginning of rolling windows
        X = np.hstack([f for f in features])
        X = np.nan_to_num(X)
        
        # Fit PCA model
        self.model.fit(X)
        
        # Transform data to reduced dimension and back to calculate reconstruction error
        X_reduced = self.model.transform(X)
        X_reconstructed = self.model.inverse_transform(X_reduced)
        
        # Calculate reconstruction error
        mse = np.mean(np.square(X - X_reconstructed), axis=1)
        
        # Determine threshold based on percentile
        self.threshold = np.percentile(mse, self.threshold_percentile)
        
        # Identify anomalies
        anomalies = (mse > self.threshold).astype(int)
        
        # Create result dataframe
        result_df = df.copy()
        
        # Initialize columns
        result_df['is_anomaly'] = anomalies
        result_df['anomaly_score'] = mse
        
        # Calculate metrics (using high values as synthetic anomalies for demonstration)
        # In a real scenario, you would need labeled data for proper evaluation
        synthetic_labels = np.zeros(len(df))
        threshold = np.percentile(df[value_column], 95)
        synthetic_labels[df[value_column] > threshold] = 1
        
        metrics = {
            'precision': float(precision_score(synthetic_labels, anomalies, zero_division=0)),
            'recall': float(recall_score(synthetic_labels, anomalies, zero_division=0)),
            'f1_score': float(f1_score(synthetic_labels, anomalies, zero_division=0)),
            'anomaly_count': int(np.sum(anomalies)),
            'total_points': len(anomalies),
            'threshold': float(self.threshold)
        }
        
        return result_df, metrics
