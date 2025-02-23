# Import Libraries
import os
import pandas as pd
import requests
import zipfile
import io
from typing import Tuple, Dict, Generator
from urllib.parse import urlparse

# Import Configurations
from config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    DAY_MAPPING,
    MONTH_MAPPING,
    RELEVANT_COLUMNS,
)

def download_and_extract(url: str) -> pd.DataFrame:
    """
    Download and extract a zip file from S3 URL.
    """
    try:
        # Download the zip file
        response = requests.get(url)
        response.raise_for_status()
        
        # Extract the zip file in memory
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # Get the CSV file name (assuming one CSV per zip)
            csv_file = [f for f in zip_ref.namelist() if f.endswith('.csv')][0]
            
            # Read the CSV directly from the zip file
            with zip_ref.open(csv_file) as csv_file:
                return pd.read_csv(csv_file)
    except Exception as e:
        raise Exception(f"Error downloading/extracting {url}: {str(e)}")

def integrate_data(urls: list) -> Tuple[pd.DataFrame, Dict]:
    """
    Integrate multiple CSV files from S3 URLs into a single dataset.
    """
    integration_stats = {
        "files_processed": 0,
        "total_records": 0,
        "files_with_errors": [],
        "data_structure": {
            "columns": [],
            "data_types": {},
            "unique_identifiers": [],
            "missing_values": {},
        },
    }

    def read_s3_files() -> Generator[pd.DataFrame, None, None]:
        """Generator function to read files from S3 one at a time."""
        if not urls:
            raise ValueError("No URLs provided in RAW_DATA_DIR")

        for url in urls:
            try:
                # Extract filename from URL for error reporting
                filename = os.path.basename(urlparse(url).path)
                trip_data = download_and_extract(url)
                integration_stats["files_processed"] += 1
                integration_stats["total_records"] += len(trip_data)
                yield trip_data
            except Exception as e:
                integration_stats["files_with_errors"].append(filename)
                print(f"Error processing {filename}: {str(e)}")

    try:
        # Use generator to read and concatenate files
        merged_data = pd.concat(read_s3_files(), ignore_index=True)

        # Document initial data structure
        integration_stats["data_structure"] = {
            "columns": list(merged_data.columns),
            "data_types": {
                col: str(dtype) for col, dtype in merged_data.dtypes.items()
            },
            "unique_identifiers": ["ride_id"],
            "missing_values": merged_data.isnull().sum().to_dict(),
            "total_records": len(merged_data),
        }

        metadata_df = pd.DataFrame([integration_stats["data_structure"]])
        metadata_file = os.path.join(PROCESSED_DATA_DIR, "initial_data_structure.csv")
        metadata_df.to_csv(metadata_file, index=False)

        return merged_data, integration_stats

    except Exception as e:
        raise Exception(f"Error in integrate_data: {str(e)}") from e
    
def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Clean the integrated dataset by handling missing values, duplicates, and data type inconsistencies.
    """
    cleaning_stats = {
        "initial_records": len(df),
        "ride_id_checks": {},
        "missing_data": {},
        "records_after_missing": {},
        "datetime_parsing_errors": {"started_at": 0, "ended_at": 0},
        "final_clean_records": 0,
        "data_type_issues": {},
        "final_clean_records": 0,
    }

    try:
        df_clean = df[RELEVANT_COLUMNS].copy()

        # Remove duplicates based on ride_id
        df_clean.drop_duplicates(subset=["ride_id"], keep="last", inplace=True)
        cleaning_stats["ride_id_checks"]["remaining_duplicates"] = df_clean.duplicated(
            subset=["ride_id"]
        ).sum()

        # Check missing values
        missing_counts = df_clean.isnull().sum()
        missing_percentage = (missing_counts / len(df_clean)) * 100
        cleaning_stats["missing_data"] = {
            col: {
                "count": missing_counts[col],
                "percent": round(missing_percentage[col], 2),
            }
            for col in df_clean.columns
            if missing_counts[col] > 0
        }

        # Handle missing values
        required_columns = [
            "started_at",
            "ended_at",
            "start_station_name",
            "member_casual",
        ]
        df_clean.dropna(subset=required_columns, inplace=True)
        cleaning_stats["records_after_missing"] = len(df_clean)

        # Convert datetime columns and track errors separately
        df_clean["started_at"] = pd.to_datetime(
            df_clean["started_at"], errors="coerce", format="mixed"
        )
        df_clean["ended_at"] = pd.to_datetime(
            df_clean["ended_at"], errors="coerce", format="mixed"
        )
        cleaning_stats["datetime_parsing_errors"]["started_at"] = (
            df_clean["started_at"].isnull().sum()
        )
        cleaning_stats["datetime_parsing_errors"]["ended_at"] = (
            df_clean["ended_at"].isnull().sum()
        )

        # Truncate datetime columns to seconds precision (remove milliseconds)

        df_clean["started_at"] = df_clean["started_at"].dt.floor("s")
        df_clean["ended_at"] = df_clean["ended_at"].dt.floor("s")

        # Data type consistency check
        expected_dtypes = {
            "ride_id": str,
            "started_at": "datetime64[ns]",
            "ended_at": "datetime64[ns]",
            "start_station_name": str,
            "member_casual": str,
        }

        for col, expected_dtype in expected_dtypes.items():
            if col in df_clean.columns:
                if not pd.api.types.is_dtype_equal(df_clean[col].dtype, expected_dtype):
                    cleaning_stats["data_type_issues"][col] = {
                        "expected": expected_dtype,
                        "actual": str(df_clean[col].dtype),
                    }
                    try:
                        df_clean[col] = df_clean[col].astype(expected_dtype)
                    except Exception as e:
                        print(f"Error converting {col} to {expected_dtype}: {str(e)}")

        cleaning_stats["final_clean_records"] = len(df_clean)

        return df_clean, cleaning_stats

    except Exception as e:
        raise Exception(f"Error in clean_data: {str(e)}") from e


def transform_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Transform the cleaned dataset by adding new features for analysis.
    """
    transformation_stats = {
        "value_range_issues": {},
        "consistency_issues": {},
        "final_records": {},
        "final_variables": {},
        "date_range": {},
    }

    try:
        df_transformed = df.copy()

        # Calculate ride duration and filter invalid durations
        df_transformed["trip_duration"] = (
            df_transformed["ended_at"] - df_transformed["started_at"]
        ).dt.total_seconds() / 60

        df_transformed = df_transformed[
            (df_transformed["trip_duration"] > 0)
            & (df_transformed["trip_duration"] <= 1440)
        ]

        # Extract hour directly from datetime
        df_transformed["hour"] = df_transformed["started_at"].dt.hour
        df_transformed["day_period"] = df_transformed["hour"].apply(
            categorize_day_period
        )

        # Process day of week and month
        df_transformed["day_of_week"] = df_transformed["started_at"].dt.day_of_week
        df_transformed["day_of_week"] = df_transformed["day_of_week"].map(DAY_MAPPING)
        df_transformed["day_of_week"] = pd.Categorical(
            df_transformed["day_of_week"],
            categories=list(DAY_MAPPING.values()),
            ordered=True,
        )

        df_transformed["month"] = df_transformed["started_at"].dt.month
        df_transformed["month"] = df_transformed["month"].map(MONTH_MAPPING)
        df_transformed["month"] = pd.Categorical(
            df_transformed["month"],
            categories=list(MONTH_MAPPING.values()),
            ordered=True,
        )

        # Validate member/casual values only
        transformation_stats["value_range_issues"] = {
            "member_casual": {
                "invalid_values": df_transformed[
                    ~df_transformed["member_casual"].isin(["member", "casual"])
                ].shape[0]
            }
        }

        transformation_stats["consistency_issues"] = {
            "ended_before_started": df_transformed[
                df_transformed["ended_at"] < df_transformed["started_at"]
            ].shape[0]
        }

        transformation_stats["final_records"] = len(df_transformed)
        transformation_stats["final_variables"] = len(df_transformed.columns)
        transformation_stats["date_range"] = {
            "start_date": df_transformed["started_at"].min(),
            "end_date": df_transformed["started_at"].max(),
        }

        return df_transformed, transformation_stats

    except Exception as e:
        raise Exception(f"Error in transform_data: {str(e)}") from e


def categorize_day_period(hour: int) -> str:
    """
    Classify the hour into time of day categories.

    Args:
        hour (int): Hour of the day (0-23)

    Returns:
        str: Classification of time (Morning/Afternoon/Evening/Night)
    """
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    else:
        return "Night"


def process_and_save() -> Tuple[pd.DataFrame, Dict]:
    """
    Execute the full data processing pipeline and save results.
    """
    try:
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

        raw_data, integration_stats = integrate_data(RAW_DATA_DIR)
        cleaned_data, cleaning_stats = clean_data(raw_data)
        final_data, transformation_stats = transform_data(cleaned_data)

        # Calculate data retention with zero-division protection
        initial_records = integration_stats["data_structure"]["total_records"]
        records_after_cleaning = cleaning_stats["final_clean_records"]
        records_after_transformation = transformation_stats["final_records"]

        data_retention = {
            "initial_records": initial_records,
            "after_cleaning": {
                "records": records_after_cleaning,
                "retention_percentage": (
                    round((records_after_cleaning / initial_records) * 100, 2)
                    if initial_records > 0
                    else 0
                ),
            },
            "after_transformation": {
                "records": records_after_transformation,
                "retention_percentage": (
                    round((records_after_transformation / initial_records) * 100, 2)
                    if initial_records > 0
                    else 0
                ),
            },
        }

        # Aggregrate all stats into one report 
        quality_report = {
            **integration_stats,
            **cleaning_stats,
            **transformation_stats,
            "data_retention": data_retention,
        }

        # Save processed data
        output_file = os.path.join(PROCESSED_DATA_DIR, "cleaned_bike_data.csv")
        final_data.to_csv(output_file, index=False)

        # Save data quality report
        quality_report_file = os.path.join(
            PROCESSED_DATA_DIR, "data_quality_report.csv"
        )
        pd.DataFrame([quality_report]).to_csv(quality_report_file, index=False)

        return final_data, quality_report

    except Exception as e:
        raise Exception(f"Error in process_and_save: {str(e)}") from e


if __name__ == "__main__":
    final_data, quality_report = process_and_save()