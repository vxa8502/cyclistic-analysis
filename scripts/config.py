# Constants and Configurations
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = [
    "https://divvy-tripdata.s3.amazonaws.com/202311-divvy-tripdata.zip",
    "https://divvy-tripdata.s3.amazonaws.com/202312-divvy-tripdata.zip",
    "https://divvy-tripdata.s3.amazonaws.com/202401-divvy-tripdata.zip",
    "https://divvy-tripdata.s3.amazonaws.com/202402-divvy-tripdata.zip",
    "https://divvy-tripdata.s3.amazonaws.com/202403-divvy-tripdata.zip",
    "https://divvy-tripdata.s3.amazonaws.com/202404-divvy-tripdata.zip",
    "https://divvy-tripdata.s3.amazonaws.com/202405-divvy-tripdata.zip",
    "https://divvy-tripdata.s3.amazonaws.com/202406-divvy-tripdata.zip",
    "https://divvy-tripdata.s3.amazonaws.com/202407-divvy-tripdata.zip",
    "https://divvy-tripdata.s3.amazonaws.com/202408-divvy-tripdata.zip",
    "https://divvy-tripdata.s3.amazonaws.com/202409-divvy-tripdata.zip",
    "https://divvy-tripdata.s3.amazonaws.com/202410-divvy-tripdata.zip"
]

PROJECT_ROOT = os.path.dirname(BASE_DIR)
PROCESSED_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
ANALYSIS_OUTPUTS_DIR = os.path.join(RESULTS_DIR, "analysis_outputs")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")

DAY_MAPPING = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}
MONTH_MAPPING = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}
RELEVANT_COLUMNS = [
    "ride_id",
    "rideable_type",
    "started_at",
    "ended_at",
    "start_station_name",
    "end_station_name",
    "start_lat",
    "start_lng",
    "end_lat",
    "end_lng",
    "member_casual",
]
