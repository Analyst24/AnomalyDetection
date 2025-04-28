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
        # Make a copy to avoid modifying the original
        df_copy = df.copy()
        
        # Replace any infinity values with NaN
        df_copy = df_copy.replace([np.inf, -np.inf], np.nan)
        
        # Handle missing values in the value column
        if value_column in df_copy.columns:
            # Use median for imputation (more robust than mean)
            median_value = df_copy[value_column].median()
            if pd.isna(median_value):  # If median is NaN (all values are NaN)
                df_copy[value_column] = df_copy[value_column].fillna(0)
            else:
                df_copy[value_column] = df_copy[value_column].fillna(median_value)
                
            # Clip extreme values to prevent outliers from skewing the model
            # Use 5 standard deviations as a reasonable bound
            mean_val = df_copy[value_column].mean()
            std_val = df_copy[value_column].std()
            
            if not pd.isna(std_val) and std_val > 0:
                lower_bound = mean_val - 5 * std_val
                upper_bound = mean_val + 5 * std_val
                df_copy[value_column] = df_copy[value_column].clip(lower_bound, upper_bound)
        else:
            raise ValueError(f"Value column '{value_column}' not found in the dataframe")
        
        # Extract time-based features
        features = pd.DataFrame()
        
        try:
            # Add the cleaned value
            features['value'] = df_copy[value_column]
            
            # Add rolling window statistics with error handling
            features['rolling_mean'] = df_copy[value_column].rolling(window=self.window_size, min_periods=1).mean().fillna(0)
            features['rolling_std'] = df_copy[value_column].rolling(window=self.window_size, min_periods=1).std().fillna(0)
            features['rolling_median'] = df_copy[value_column].rolling(window=self.window_size, min_periods=1).median().fillna(0)
            features['rolling_max'] = df_copy[value_column].rolling(window=self.window_size, min_periods=1).max().fillna(0)
            features['rolling_min'] = df_copy[value_column].rolling(window=self.window_size, min_periods=1).min().fillna(0)
            
            # Add rate of change with careful handling of potential infinity issues
            diff = df_copy[value_column].diff()
            features['rate_of_change'] = diff.replace([np.inf, -np.inf], np.nan).fillna(0)
            
        except Exception as e:
            # Log the error and provide graceful fallback
            print(f"Error extracting features: {str(e)}. Using basic features only.")
            features['value'] = df_copy[value_column]
            features['rolling_mean'] = features['value']
            features['rolling_std'] = 0
            features['rolling_median'] = features['value']
            features['rolling_max'] = features['value']
            features['rolling_min'] = features['value']
            features['rate_of_change'] = 0
        
        # Final safety check - replace any remaining NaN or Inf
        features = features.replace([np.inf, -np.inf], np.nan).fillna(0)
        
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
        try:
            # Make a copy of the input dataframe to avoid modifying it
            df_copy = df.copy()
            
            # Extract features with error handling
            features = self.extract_features(df_copy, value_column)
            
            # Ensure there are no NaN or infinity values
            features = features.replace([np.inf, -np.inf], np.nan).fillna(0)
            
            # Scale features with error handling
            try:
                features_scaled = self.scaler.fit_transform(features)
                # Double-check for any NaNs after scaling
                features_scaled = np.nan_to_num(features_scaled, nan=0.0)
            except Exception as e:
                print(f"Error during feature scaling: {str(e)}. Using unscaled features.")
                # If scaling fails, use unscaled but normalized features
                features_vals = features.values
                features_scaled = np.nan_to_num(features_vals, nan=0.0)
                # Simple normalization as fallback
                col_max = np.max(np.abs(features_scaled), axis=0)
                col_max[col_max == 0] = 1.0  # Avoid division by zero
                features_scaled = features_scaled / col_max
            
            # Fit K-Means model with error handling
            try:
                # Adjust n_clusters if we have fewer samples than clusters
                effective_n_clusters = min(self.n_clusters, len(features_scaled) - 1)
                if effective_n_clusters < 2:
                    effective_n_clusters = 2  # At least 2 clusters needed
                
                if effective_n_clusters != self.n_clusters:
                    temp_model = KMeans(n_clusters=effective_n_clusters, random_state=self.random_state)
                    temp_model.fit(features_scaled)
                    self.cluster_centers = temp_model.cluster_centers_
                    cluster_labels = temp_model.predict(features_scaled)
                else:
                    self.model.fit(features_scaled)
                    self.cluster_centers = self.model.cluster_centers_
                    cluster_labels = self.model.predict(features_scaled)
            except Exception as e:
                print(f"Error fitting KMeans model: {str(e)}. Using simplified approach.")
                # Fallback to a simpler approach - use percentile-based anomaly detection
                anomalies = np.zeros(len(features_scaled))
                anomaly_scores = np.zeros(len(features_scaled))
                
                # Compute anomaly score based on distance from mean for each feature
                for col_idx in range(features_scaled.shape[1]):
                    col_data = features_scaled[:, col_idx]
                    col_mean = np.mean(col_data)
                    col_std = np.std(col_data)
                    if col_std > 0:
                        z_scores = np.abs((col_data - col_mean) / col_std)
                        anomaly_scores += z_scores
                
                # Normalize scores
                if np.max(anomaly_scores) > 0:
                    anomaly_scores = anomaly_scores / np.max(anomaly_scores)
                
                # Tag anomalies (top 5%)
                threshold = np.percentile(anomaly_scores, 95)
                anomalies = (anomaly_scores > threshold).astype(int)
                
                # Create result dataframe
                result_df = df_copy.copy()
                result_df['is_anomaly'] = anomalies
                result_df['anomaly_score'] = anomaly_scores
                result_df['cluster'] = 0  # All assigned to the same cluster in fallback
                
                # Calculate metrics
                metrics = {
                    'anomaly_count': int(np.sum(anomalies)),
                    'anomaly_ratio': float(np.mean(anomalies)),
                    'total_points': len(df_copy),
                    'threshold': float(threshold),
                    'clusters': 1,  # Fallback used no clustering
                    'note': 'Used fallback detection method due to KMeans fitting error'
                }
                
                return result_df, metrics
            
            # Calculate distance to cluster center for each point
            distances = np.zeros(len(features_scaled))
            for i in range(len(features_scaled)):
                try:
                    distances[i] = np.linalg.norm(features_scaled[i] - self.cluster_centers[cluster_labels[i]])
                except Exception as e:
                    print(f"Error calculating distance for point {i}: {str(e)}. Using default value.")
                    distances[i] = 0.0
            
            # Determine threshold for anomalies with robustness
            avg_distances = []
            for i in range(len(self.cluster_centers)):
                cluster_points = distances[cluster_labels == i]
                if len(cluster_points) > 0:
                    avg_distances.append(np.mean(cluster_points))
                else:
                    avg_distances.append(0.0)
            
            if len(avg_distances) > 0 and max(avg_distances) > 0:
                self.threshold = self.threshold_factor * max(avg_distances)
            else:
                # Fallback threshold based on percentile of all distances
                self.threshold = np.percentile(distances, 95)
            
            # Flag anomalies
            anomalies = (distances > self.threshold).astype(int)
            
            # Create result dataframe
            result_df = df_copy.copy()
            result_df['is_anomaly'] = anomalies
            result_df['anomaly_score'] = distances
            result_df['cluster'] = cluster_labels
            
            # Calculate metrics with robust handling
            try:
                # Get a synthetic baseline for metrics calculation
                synthetic_labels = np.zeros(len(df_copy))
                if value_column in df_copy.columns:
                    # Protect against NA values
                    value_data = df_copy[value_column].fillna(df_copy[value_column].median())
                    value_threshold = np.percentile(value_data, 95)
                    synthetic_labels[df_copy[value_column] > value_threshold] = 1
                
                metrics = {
                    'precision': float(precision_score(synthetic_labels, anomalies, zero_division=0)),
                    'recall': float(recall_score(synthetic_labels, anomalies, zero_division=0)),
                    'f1_score': float(f1_score(synthetic_labels, anomalies, zero_division=0)),
                    'anomaly_count': int(np.sum(anomalies)),
                    'total_points': len(df_copy),
                    'threshold': float(self.threshold),
                    'clusters': int(len(self.cluster_centers))
                }
            except Exception as e:
                print(f"Error calculating metrics: {str(e)}. Using basic metrics only.")
                metrics = {
                    'anomaly_count': int(np.sum(anomalies)),
                    'total_points': len(df_copy),
                    'threshold': float(self.threshold),
                    'clusters': int(len(self.cluster_centers))
                }
        except Exception as e:
            # Last resort fallback
            print(f"Critical error in anomaly detection: {str(e)}. Using simple outlier detection.")
            result_df = df.copy()
            # Implement a very basic outlier detection method as final fallback
            basic_scores = np.zeros(len(df))
            if value_column in df.columns:
                values = df[value_column].fillna(0).values
                mean_val = np.mean(values)
                std_val = np.std(values)
                if std_val > 0:
                    basic_scores = np.abs((values - mean_val) / std_val)
            
            # Mark top 5% as anomalies
            threshold = np.percentile(basic_scores, 95)
            basic_anomalies = (basic_scores > threshold).astype(int)
            
            result_df['is_anomaly'] = basic_anomalies
            result_df['anomaly_score'] = basic_scores
            result_df['cluster'] = 0
            
            metrics = {
                'anomaly_count': int(np.sum(basic_anomalies)),
                'total_points': len(df),
                'threshold': float(threshold),
                'clusters': 1,
                'note': 'Used emergency fallback method due to critical error'
            }
        
        return result_df, metrics
