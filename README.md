# Cyclistic Bike Share Analysis

## Business Problem
Cyclistic, a bike-sharing company in Chicago, aims to maximize annual memberships for future growth. This analysis explores how casual riders and annual members use Cyclistic bikes differently to inform marketing strategies for converting casual riders into annual members.

## Project Overview
The analysis examines historical ride data from Cyclistic's bike-share program to uncover actionable insights about usage patterns between casual riders and members. Key analyses include:
- User segmentation
- Temporal usage patterns (daily, weekly, monthly)
- Ride duration analysis
- Bike type preferences
- Station popularity and geographic patterns

## Prerequisites
- Python 3.8+
- pandas
- numpy
- requests (for S3 data retrieval)
- Required packages listed in `requirements.txt`

## Project Structure
```
.
├── data/
│   └── processed/  # Cleaned and preprocessed data outputs
├── scripts/
│   ├── config.py  # Configuration and S3 data sources
│   ├── clean_data.py  # Data cleaning and processing
│   └── analyze_data.py # Analysis implementation
├── results/          
│   └── analysis_outputs/  # Analysis outputs and statistics
│   └── figures/       # Generated visualizations and plots
├── notebooks/
│   └── visualization_dashboard.ipynb  
└── requirements.txt   # Project dependencies
```

## Dataset Description
The analysis uses Cyclistic's historical trip data, accessed directly from public S3 buckets. Data includes:
- Ride timestamps (start/end)
- Station information (names, coordinates)
- Bike types
- User types (casual/member)

Note: Data excludes personally identifiable information due to privacy requirements.

## Data Source
The analysis pulls data directly from Divvy Bikes' public S3 buckets, eliminating the need for local storage of large data files. Data URLs are configured in `config.py` and automatically downloaded during processing.

## Installation & Usage

1. **Clone the Repository**
   ```bash
   git clone https://github.com/vxa8502/cyclistic-analysis.git
   cd cyclistic-analysis
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Analysis**
   ```bash
   python scripts/clean_data.py    # Downloads data from S3, cleans and processes it
   python scripts/analyze_data.py # Generate analysis
   ```

## Data Processing Steps
1. Data retrieval and integration
   - Automatic download from S3 buckets
   - In-memory extraction of ZIP files
   - Integration of multiple datasets
2. Cleaning and standardization
   - Handling missing values
   - Removing duplicates
   - Standardizing data types
3. Feature engineering
   - Calculating trip durations
   - Deriving temporal features
   - Computing usage metrics

## Key Findings
1. Usage Patterns
   - Temporal differences between casual riders and members
   - Peak usage periods for each user segment
   - Station popularity variations

2. Ride Characteristics
   - Duration differences between user types
   - Bike type preferences

## Troubleshooting
Common issues and solutions:
- Internet connectivity: Ensure stable internet connection for S3 data retrieval
- Memory management: Data is processed in streams to minimize memory usage
- Download issues: Check S3 URL validity in config.py
- ZIP extraction errors: Verify S3 files are properly formatted

## Performance Notes
- The analysis streams data directly from S3, reducing local storage requirements
- Processing time may vary based on internet connection speed
- Memory usage is optimized through streaming data processing

## Contributing
Suggestions and feedback are welcome through issues and pull requests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
For questions or feedback about this analysis, please create an issue in the repository.

## Acknowledgments
- Data provided by Motivate International Inc. through public S3 buckets
- Analysis conducted as part of the Google Data Analytics Professional Certificate case study
