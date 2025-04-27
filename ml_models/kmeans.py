import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score
from scipy.spatial.distance import cdist

class KMeansModel:
    def __init__(self, n_clusters=5, window_size=24, threshold_factor=1.5, random_state=42):
        """
        Initialize K-Means Clustering model for anomaly detection.
        
        Parameters:
        -----------
        n_clusters : int, default=5
            Number of clusters to use
        window_size : int, default=24
            Size of rolling window for feature extraction
        threshold_factor : float, default=1.5
            Factor to multiply with the max average distance to determine anomalies
        random_state : int, default=42
            Random seed for reproducibility
        """
        self.n_clusters = n_clusters
        self.window_size = window_size
        self.threshold_factor = threshold_factor
        self.random_state = random_state
        self.model = KMeans(n_clusters=n_clusters, random_state=random_state)
        self.scaler = StandardScaler()
        self.cluster_centers = None
        self.threshold = None
        
    def extract_features(self, df, value_column):
        """
        Extract features from time series data.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Input dataframe with time series data
        value_column : str
            Column name of the energy consumption values
            
        Returns:
        --------
        features : pandas.DataFrame
            Dataframe with extracted features
        """
        # Extract time-based features
        features = pd.DataFrame()
        
        # Add the value itself
        features['value'] = df[value_column]
        
        # Add rolling window statistics
        features['rolling_mean'] = df[value_column].rolling(window=self.window_size, min_periods=1).mean()
        features['rolling_std'] = df[value_column].rolling(window=self.window_size, min_periods=1).std().fillna(0)
        features['rolling_median'] = df[value_column].rolling(window=self.window_size, min_periods=1).median()
        features['rolling_max'] = df[value_column].rolling(window=self.window_size, min_periods=1).max()
        features['rolling_min'] = df[value_column].rolling(window=self.window_size, min_periods=1).min()
        
        # Add rate of change
        features['rate_of_change'] = df[value_column].diff().fillna(0)
        
        return features
    
    def detect_anomalies(self, df, time_column='timestamp', value_column='value'):
        """
        Detect anomalies in the time series data using K-Means clustering.
        
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
        # Extract features
        features = self.extract_features(df, value_column)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Fit K-Means model
        self.model.fit(features_scaled)
        self.cluster_centers = self.model.cluster_centers_
        
        # Predict clusters
        cluster_labels = self.model.predict(features_scaled)
        
        # Calculate distance to cluster center for each point
        distances = np.zeros(len(features_scaled))
        for i in range(len(features_scaled)):
            distances[i] = np.linalg.norm(features_scaled[i] - self.cluster_centers[cluster_labels[i]])
        
        # Determine threshold for anomalies
        # Points with distance greater than threshold_factor * max average distance are anomalies
        avg_distances = [np.mean(distances[cluster_labels == i]) for i in range(self.n_clusters)]
        self.threshold = self.threshold_factor * max(avg_distances)
        
        # Flag anomalies
        anomalies = (distances > self.threshold).astype(int)
        
        # Create result dataframe
        result_df = df.copy()
        result_df['is_anomaly'] = anomalies
        result_df['anomaly_score'] = distances
        result_df['cluster'] = cluster_labels
        
        # Calculate metrics (using synthetic labels for demonstration)
        # In a real scenario, you would need labeled data for proper evaluation
        synthetic_labels = np.zeros(len(df))
        value_threshold = np.percentile(df[value_column], 95)
        synthetic_labels[df[value_column] > value_threshold] = 1
        
        metrics = {
            'precision': float(precision_score(synthetic_labels, anomalies, zero_division=0)),
            'recall': float(recall_score(synthetic_labels, anomalies, zero_division=0)),
            'f1_score': float(f1_score(synthetic_labels, anomalies, zero_division=0)),
            'anomaly_count': int(np.sum(anomalies)),
            'total_points': len(df),
            'threshold': float(self.threshold),
            'clusters': int(self.n_clusters)
        }
        
        return result_df, metrics
