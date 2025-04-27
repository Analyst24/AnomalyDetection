import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score

class IsolationForestModel:
    def __init__(self, contamination=0.05, random_state=42):
        """
        Initialize Isolation Forest model for anomaly detection.
        
        Parameters:
        -----------
        contamination : float, default=0.05
            The proportion of outliers in the dataset
        random_state : int, default=42
            Random seed for reproducibility
        """
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
            max_samples='auto'
        )
        self.scaler = StandardScaler()
        
    def preprocess(self, df, value_column):
        """
        Preprocess the data for Isolation Forest.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Input dataframe with time series data
        value_column : str
            Column name of the energy consumption values
            
        Returns:
        --------
        X : numpy.ndarray
            Preprocessed features for the model
        """
        # Extract features (add more if needed)
        X = df[[value_column]].copy()
        
        # Add rolling statistics as features
        X['rolling_mean'] = df[value_column].rolling(window=24, min_periods=1).mean()
        X['rolling_std'] = df[value_column].rolling(window=24, min_periods=1).std().fillna(0)
        X['rolling_max'] = df[value_column].rolling(window=24, min_periods=1).max()
        X['rolling_min'] = df[value_column].rolling(window=24, min_periods=1).min()
        
        # Scale the features
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled
    
    def detect_anomalies(self, df, time_column='timestamp', value_column='value'):
        """
        Detect anomalies in the time series data.
        
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
        # Preprocess the data
        X = self.preprocess(df, value_column)
        
        # Fit the model and predict
        self.model.fit(X)
        predictions = self.model.predict(X)
        
        # Convert predictions to binary labels (1 for anomalies, 0 for normal)
        # In Isolation Forest, -1 is anomaly, 1 is normal
        anomalies = np.where(predictions == -1, 1, 0)
        
        # Calculate anomaly scores
        anomaly_scores = -self.model.decision_function(X)
        
        # Create result dataframe
        result_df = df.copy()
        result_df['is_anomaly'] = anomalies
        result_df['anomaly_score'] = anomaly_scores
        
        # Calculate metrics (using synthetic labels for demonstration)
        # In a real scenario, you would need labeled data for proper evaluation
        # Here we're using a heuristic approach for demonstration
        synthetic_labels = np.zeros(len(df))
        threshold = np.percentile(df[value_column], 95)
        synthetic_labels[df[value_column] > threshold] = 1
        
        metrics = {
            'precision': float(precision_score(synthetic_labels, anomalies, zero_division=0)),
            'recall': float(recall_score(synthetic_labels, anomalies, zero_division=0)),
            'f1_score': float(f1_score(synthetic_labels, anomalies, zero_division=0)),
            'anomaly_count': int(np.sum(anomalies)),
            'total_points': len(df)
        }
        
        return result_df, metrics
