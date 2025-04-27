# Energy Anomaly Detection System

A professional energy anomaly detection system leveraging machine learning to provide intelligent insights and efficiency recommendations.

## Features

- Advanced anomaly detection using multiple ML algorithms (Isolation Forest, AutoEncoder, K-Means)
- Interactive visualizations of energy consumption patterns
- User authentication system
- Offline operation - no internet connection required
- Responsive design for cross-device accessibility

## Setup for Local Development

### Prerequisites

- Python 3.8 or higher
- Optional: PostgreSQL (SQLite is used as fallback if no database connection is provided)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/energy-anomaly-detection.git
   cd energy-anomaly-detection
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the environment:
   - Copy `.env.example` to `.env`
   - Edit `.env` to set your database connection details or leave as is to use SQLite

5. Run the application:
   ```bash
   python main.py
   ```

6. Access the application at http://localhost:5000

## Offline Usage

This application is designed to run completely offline. All required resources (CSS, JavaScript, fonts, images) are included in the project.

If you're using the application offline:
- The system will automatically use SQLite instead of PostgreSQL
- All UI elements will work without internet connection
- Data analysis is performed locally using the machine learning libraries

## Machine Learning Models

The system includes three anomaly detection algorithms:

1. **Isolation Forest**: Effective for detecting point anomalies in time series data
2. **AutoEncoder**: Neural network-based approach for complex pattern recognition
3. **K-Means Clustering**: Uses statistical distances to identify outliers

## License

[MIT License](LICENSE)

## Author

Opulent Chikwiramakomo

Copyright © 2025