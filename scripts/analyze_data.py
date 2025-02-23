# Import Libraries
import os
import numpy as np
import pandas as pd

# Import Configuration
from config import (
    PROCESSED_DATA_DIR,
)

# Prepare to work with cleaned dataset 
DATA_PATH = os.path.join(PROCESSED_DATA_DIR, "cleaned_bike_data.csv")
os.makedirs("results/analysis_outputs", exist_ok=True)


# Utility Functions
def validate_dataframe(df, required_columns):
    """Validate DataFrame and required columns."""
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame.")
    if not set(required_columns).issubset(df.columns):
        raise ValueError(
            f"DataFrame must contain the following columns: {required_columns}"
        )
    return True


def safe_file_operation(filepath, mode, content=None):
    """Handle file operations safely."""
    try:
        if mode in ("w", "a") and content is not None:
            with open(filepath, mode) as f:
                f.write(content)
        elif mode == "r":
            with open(filepath, mode) as f:
                return f.read()
    except IOError as e:
        print(f"Error in file operation ({filepath}, {mode}): {str(e)}")
        return None


def calculate_gini(x):
    """Calculate Gini coefficient for station concentration using numpy."""
    x = np.asarray(x)
    if np.any(x < 0):
        raise ValueError("Input values must be non-negative.")
    x = x / np.sum(x)  # Normalize to avoid overflow
    return 0.5 * np.abs(np.subtract.outer(x, x)).mean() / np.mean(x)


# Analysis Functions
def analyze_rider_segments(df):
    """Analyze the distribution of casual riders vs members."""
    try:
        validate_dataframe(df, ["member_casual"])

        trips_by_rider_group = df.groupby("member_casual").size()
        rider_group_distribution = (
            trips_by_rider_group / trips_by_rider_group.sum() * 100
        ).round(2)

        output_text = (
            f"Analyze Rider Segments\n"
            f"---------------------------\n"
            f"Total rides by rider group:\n{trips_by_rider_group.to_string()}\n\n"
            f"Percentage distribution:\n{rider_group_distribution.to_string()}\n"
        )

        safe_file_operation("results/analysis_outputs//analysis_output.txt", "w", output_text)
        trips_by_rider_group.to_csv("results/analysis_outputs//trips_by_rider_group.csv")
        rider_group_distribution.to_csv("results/analysis_outputs//rider_group_distribution.csv")

    except Exception as e:
        print(f"Error in analyze_rider_segments: {str(e)}")


def calculate_pattern_stats(usage_data, pattern_name):
    """Calculate statistics for usage patterns."""
    try:
        pct_data = (usage_data.div(usage_data.sum(axis=1), axis=0) * 100).round(2)
        differences = pct_data.loc["casual"] - pct_data.loc["member"]

        stats_summary = {
            "max_difference": differences.abs().max(),
            "max_difference_period": differences.abs().idxmax(),
            "mean_difference": differences.abs().mean(),
            "std_difference": differences.std(),
        }

        magnitude = (
            "large"
            if stats_summary["mean_difference"] > 5
            else "moderate" if stats_summary["mean_difference"] > 2 else "small"
        )

        max_diff = differences[stats_summary["max_difference_period"]]
        direction = "higher casual usage" if max_diff > 0 else "higher member usage"

        interpretation = (
            f"Statistical Analysis for {pattern_name}:\n"
            f"- Average absolute difference is {magnitude} ({stats_summary['mean_difference']:.1f}%)\n"
            f"- Largest difference occurs on {stats_summary['max_difference_period']} "
            f"({abs(max_diff):.1f}% {direction})"
        )

        return pct_data, stats_summary, interpretation

    except Exception as e:
        print(f"Error in calculate_pattern_stats: {str(e)}")
        return None, None, None


def analyze_usage_patterns(df):
    """Analyze when different rider groups ride."""
    try:
        validate_dataframe(df, ["member_casual", "month", "day_of_week", "day_period"])

        # Monthly patterns
        monthly_usage = (
            df.groupby(["member_casual", "month"], observed=False)
            .size()
            .unstack(fill_value=0)
        )
        monthly_pct, monthly_stats, monthly_interpretation = calculate_pattern_stats(
            monthly_usage, "Monthly Patterns"
        )

        # Daily patterns
        daily_usage = (
            df.groupby(["member_casual", "day_of_week"], observed=False)
            .size()
            .unstack(fill_value=0)
        )
        daily_pct, daily_stats, daily_interpretation = calculate_pattern_stats(
            daily_usage, "Daily Patterns"
        )

        # Time patterns
        hourly_usage = (
            df.groupby(["member_casual", "day_period"]).size().unstack(fill_value=0)
        )
        hourly_pct, hourly_stats, hourly_interpretation = calculate_pattern_stats(
            hourly_usage, "Time of Day Patterns"
        )

        output_text = (
            f"Analyze Usage Patterns\n"
            f"---------------------------\n"
            f"Monthly usage patterns:\n{monthly_usage.T.to_string()}\n\n"
            f"Monthly usage patterns (%):\n{monthly_pct.T.to_string()}\n"
            f"{monthly_interpretation}\n\n"
            f"Daily usage patterns:\n{daily_usage.T.to_string()}\n\n"
            f"Daily usage patterns (%):\n{daily_pct.T.to_string()}\n"
            f"{daily_interpretation}\n\n"
            f"Time usage patterns:\n{hourly_usage.T.to_string()}\n\n"
            f"Time usage patterns (%):\n{hourly_pct.T.to_string()}\n"
            f"{hourly_interpretation}\n"
        )

        safe_file_operation("results/analysis_outputs//analysis_output.txt", "a", "\n" + output_text)

        if monthly_pct is not None:
            monthly_pct.T.to_csv("results/analysis_outputs//monthly_usage_pct.csv")
        if daily_pct is not None:
            daily_pct.T.to_csv("results/analysis_outputs//daily_usage_pct.csv")
        if hourly_pct is not None:
            hourly_pct.T.to_csv("results/analysis_outputs//hourly_usage_pct.csv")

        stats_df = pd.DataFrame(
            {
                "Monthly": monthly_stats if monthly_stats is not None else {},
                "Daily": daily_stats if daily_stats is not None else {},
                "Hourly": hourly_stats if hourly_stats is not None else {},
            }
        )
        stats_df.to_csv("results/analysis_outputs//usage_patterns_stats.csv")

    except Exception as e:
        print(f"Error in analyze_usage_patterns: {str(e)}")


def analyze_ride_metrics(df):
    """Analyze differences in ride duration between rider groups."""
    try:
        validate_dataframe(df, ["member_casual", "trip_duration"])

        mean_trip_duration = df.groupby("member_casual")["trip_duration"].agg(
            ["mean", "std", "count"]
        )
        trip_duration_gap = (
            mean_trip_duration.loc["casual", "mean"]
            - mean_trip_duration.loc["member", "mean"]
        )

        # Categorize trip durations
        duration_bins = [0, 10, 20, 30, 40, 50, 60, 120]
        duration_labels = ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60+"]
        df["trip_duration_category"] = pd.cut(
            df["trip_duration"],
            bins=duration_bins,
            labels=duration_labels,
            include_lowest=True,
        )

        # Calculate duration distribution
        trip_duration_dist = (
            df.groupby(["member_casual", "trip_duration_category"], observed=True)
            .size()
            .unstack(fill_value=0)
        )
        trip_duration_dist_pct = (
            trip_duration_dist.div(trip_duration_dist.sum(axis=1), axis=0) * 100
        ).round(2)

        output_text = (
            f"Analyze Ride Metrics\n"
            f"---------------------------\n"
            f"Average Trip Duration Statistics:\n{mean_trip_duration.to_string()}\n\n"
            f"Distribution of Trip Durations:\n{trip_duration_dist_pct.T.to_string()}\n\n"
            f"- Mean difference is {trip_duration_gap:.2f} minutes"
        )

        safe_file_operation("results/analysis_outputs//analysis_output.txt", "a", "\n" + output_text)
        trip_duration_dist_pct.T.to_csv("results/analysis_outputs//trip_duration_dist_pct.csv")

    except Exception as e:
        print(f"Error in analyze_ride_metrics: {str(e)}")


def analyze_bike_preferences(df):
    """Analyze bike type preferences between rider groups."""
    try:
        validate_dataframe(df, ["member_casual", "rideable_type"])

        bike_preference_counts = (
            df.groupby(["member_casual", "rideable_type"]).size().unstack(fill_value=0)
        )
        bike_preference_pct = (
            bike_preference_counts.div(bike_preference_counts.sum(axis=1), axis=0) * 100
        ).round(2)

        output_text = (
            f"Analyze Bike Preferences\n"
            f"---------------------------\n"
            f"Usage Count:\n{bike_preference_counts.T.to_string()}\n\n"
            f"Usage Percentage:\n{bike_preference_pct.T.to_string()}\n"
        )

        safe_file_operation("results/analysis_outputs//analysis_output.txt", "a", "\n" + output_text)
        bike_preference_counts.to_csv("results/analysis_outputs//bike_preference_counts.csv")
        bike_preference_pct.to_csv("results/analysis_outputs//bike_preference_pct.csv")

    except Exception as e:
        print(f"Error in analyze_bike_preferences: {str(e)}")


def analyze_station_popularity(df):
    """Analyze station popularity using Gini coefficient."""
    try:
        validate_dataframe(
            df, ["member_casual", "start_station_name", "end_station_name"]
        )

        def calculate_station_metrics(station_data, station_type):
            """Calculate station usage metrics."""
            try:
                top_stations = rank_stations_by_usage(
                    station_data, f"{station_type}_station_name"
                )
                station_counts = (
                    station_data.groupby(
                        ["member_casual", f"{station_type}_station_name"]
                    )
                    .size()
                    .reset_index(name="count")
                )

                station_concentrations = station_counts.groupby("member_casual").agg(
                    total_stations=("count", "count"),
                    gini_coefficient=("count", calculate_gini),
                    top_10_share=(
                        "count",
                        lambda x: x.nlargest(10).sum() / x.sum() * 100,
                    ),
                )
                return top_stations, station_concentrations
            except Exception as e:
                print(
                    f"Error in calculate_station_metrics for {station_type} stations: {str(e)}"
                )
                return None, None

        start_top_stations, start_concentration = calculate_station_metrics(df, "start")
        end_top_stations, end_concentration = calculate_station_metrics(df, "end")

        interpretation = (
            f"\nStation Usage Patterns:\n"
            f"Start Stations:\n"
            f"- Casual riders: Top 10 stations account for {start_concentration.loc['casual', 'top_10_share']:.1f}% of rides\n"
            f"- Members: Top 10 stations account for {start_concentration.loc['member', 'top_10_share']:.1f}% of rides\n"
            f"End Stations:\n"
            f"- Casual riders: Top 10 stations account for {end_concentration.loc['casual', 'top_10_share']:.1f}% of rides\n"
            f"- Members: Top 10 stations account for {end_concentration.loc['member', 'top_10_share']:.1f}% of rides\n"
        )

        output_text = (
            f"Analyze Station Popularity\n"
            f"---------------------------\n"
            f"Top Start Stations:\n{start_top_stations.to_string()}\n\n"
            f"Top End Stations:\n{end_top_stations.to_string()}\n"
            f"{interpretation}"
        )

        safe_file_operation("results/analysis_outputs//analysis_output.txt", "a", "\n" + output_text)
        start_top_stations.to_csv("results/analysis_outputs//popular_start_stations.csv", index=False)
        end_top_stations.to_csv("results/analysis_outputs//popular_end_stations.csv", index=False)

    except Exception as e:
        print(f"Error in analyze_station_popularity: {str(e)}")


def rank_stations_by_usage(df, station_column):
    """Get top 10 stations by rider group."""
    try:
        lat_column = (
            "start_lat" if station_column == "start_station_name" else "end_lat"
        )
        lng_column = (
            "start_lng" if station_column == "start_station_name" else "end_lng"
        )

        top_stations = (
            df.groupby(["member_casual", station_column, lat_column, lng_column])
            .size()
            .reset_index(name="count")
            .sort_values(["member_casual", "count"], ascending=[True, False])
            .groupby("member_casual")
            .head(10)
            .rename(columns={lat_column: "latitude", lng_column: "longitude"})
        )

        return top_stations
    except Exception as e:
        print(f"Error in rank_stations_by_usage: {str(e)}")
        return pd.DataFrame()


def main():
    try:
        df = pd.read_csv(
            DATA_PATH,
            parse_dates=["started_at", "ended_at"],
            dtype={"day_of_week": "category", "month": "category"},
        )
        # Make categorical columns
        df["day_of_week"] = pd.Categorical(
            df["day_of_week"],
            categories=[
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
            ordered=True,
        )
        df["month"] = pd.Categorical(
            df["month"],
            categories=[
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ],
            ordered=True,
        )

        # Run analyses
        analyze_rider_segments(df)
        analyze_usage_patterns(df)
        analyze_ride_metrics(df)
        analyze_bike_preferences(df)
        analyze_station_popularity(df)

    except FileNotFoundError:
        print(f"Error: Could not find data file at {DATA_PATH}")
    except pd.errors.EmptyDataError:
        print("Error: The data file is empty")
    except Exception as e:
        print(f"Error in main: {str(e)}")


if __name__ == "__main__":
    main()
