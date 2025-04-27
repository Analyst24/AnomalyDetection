import numpy as np
import pandas as pd
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)

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
        
    def preprocess(self, df, feature_columns=None):
        """
        Preprocess the data for Isolation Forest with multi-column support.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Input dataframe with time series data
        feature_columns : list or None
            List of column names to use as features. If None, all numeric columns
            except obvious timestamp columns will be used.
            
        Returns:
        --------
        X : numpy.ndarray
            Preprocessed features for the model
        feature_names : list
            Names of all features used (original and derived)
        """
        # Make a copy to avoid modifying the original
        df_copy = df.copy()
        
        # Auto-detect feature columns if not specified
        if feature_columns is None:
            # Exclude typical timestamp or ID columns
            exclude_patterns = ['date', 'time', 'timestamp', 'id', 'index']
            numeric_cols = df.select_dtypes(include=['number']).columns
            
            feature_columns = [col for col in numeric_cols if not any(
                pattern in col.lower() for pattern in exclude_patterns)]
            
            logger.info(f"Automatically selected feature columns: {feature_columns}")
        
        if not feature_columns:
            raise ValueError("No valid feature columns found in the dataset")
        
        # Create a dataframe to hold all features
        X = pd.DataFrame(index=df.index)
        
        # Process each feature column
        for col in feature_columns:
            if col not in df.columns:
                logger.warning(f"Column {col} not found in dataframe. Skipping.")
                continue
                
            # Add original feature
            X[col] = df[col]
            
            # Add rolling statistics as features
            window_size = min(24, len(df) // 10) if len(df) > 30 else 3
            
            X[f'{col}_rolling_mean'] = df[col].rolling(window=window_size, min_periods=1).mean()
            X[f'{col}_rolling_std'] = df[col].rolling(window=window_size, min_periods=1).std().fillna(0)
            X[f'{col}_rolling_max'] = df[col].rolling(window=window_size, min_periods=1).max()
            X[f'{col}_rolling_min'] = df[col].rolling(window=window_size, min_periods=1).min()
            
            # Add additional features
            X[f'{col}_diff'] = df[col].diff().fillna(0)
            X[f'{col}_pct_change'] = df[col].pct_change().fillna(0)
        
        # Scale all features
        feature_names = X.columns.tolist()
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, feature_names, feature_columns
    
    def detect_anomalies(self, df, time_column=None, value_column=None):
        """
        Detect anomalies in the time series data across multiple columns.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Input dataframe with time series data
        time_column : str or None
            Column name of the timestamps. If None, it will be auto-detected.
        value_column : str or None
            Column name of the energy consumption value. If None, all numeric 
            columns will be used for anomaly detection.
            
        Returns:
        --------
        result_df : pandas.DataFrame
            Dataframe with the original data and anomaly predictions
        metrics : dict
            Dictionary with performance metrics and feature importance
        """
        # Auto-detect time column if not provided
        if time_column is None:
            for col in df.columns:
                if any(time_pattern in col.lower() for time_pattern in ['time', 'date', 'timestamp']):
                    time_column = col
                    logger.info(f"Auto-detected time column: {time_column}")
                    break
        
        # If value_column is specified, use only that column, otherwise use all suitable numeric columns
        feature_columns = [value_column] if value_column else None
        
        # Preprocess the data
        X, feature_names, original_features = self.preprocess(df, feature_columns)
        
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
        
        # Identify which features contribute most to anomalies
        feature_importance = {}
        anomaly_details = {}
        
        # For each original feature, determine its contribution to anomalies
        for feature in original_features:
            if feature not in df.columns:
                continue
                
            # Get feature values
            feature_values = df[feature].values
            
            # Calculate feature-specific anomaly threshold
            threshold = np.percentile(feature_values, 95)
            feature_anomalies = np.where(feature_values > threshold, 1, 0)
            
            # Add feature-specific anomaly flags
            result_df[f'{feature}_anomaly'] = feature_anomalies
            
            # Calculate importance of this feature
            if np.sum(anomalies) > 0:
                # Compare feature values at anomaly points vs. normal points
                anomaly_feature_vals = feature_values[anomalies == 1]
                normal_feature_vals = feature_values[anomalies == 0]
                
                if len(normal_feature_vals) > 0 and len(anomaly_feature_vals) > 0:
                    importance = abs(np.mean(anomaly_feature_vals) - np.mean(normal_feature_vals))
                    feature_importance[feature] = float(importance)
                    
                    # Store detailed information about this feature's anomalies
                    anomaly_details[feature] = {
                        'mean_at_anomalies': float(np.mean(anomaly_feature_vals)) if len(anomaly_feature_vals) > 0 else 0,
                        'std_at_anomalies': float(np.std(anomaly_feature_vals)) if len(anomaly_feature_vals) > 0 else 0,
                        'max_at_anomalies': float(np.max(anomaly_feature_vals)) if len(anomaly_feature_vals) > 0 else 0,
                        'mean_at_normal': float(np.mean(normal_feature_vals)) if len(normal_feature_vals) > 0 else 0,
                        'anomaly_count': int(np.sum(feature_anomalies))
                    }
        
        # Calculate metrics
        metrics = {
            'anomaly_count': int(np.sum(anomalies)),
            'anomaly_ratio': float(np.mean(anomalies)),
            'total_points': len(df),
            'feature_importance': feature_importance,
            'anomaly_details': anomaly_details
        }
        
        return result_df, metrics
