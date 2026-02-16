#!/bin/bash

# Function to merge dashcam videos for each ride
echo "Starting dashcam video merging..."

merge_dashcam_videos() {
    local directory="$1"

    # Sort files by name (to ensure chronological order)
    local files=($(ls "$directory"/NO*.MP4 | sort))

    local current_ride=()
    local last_timestamp=""
    local current_date=""
    local ride_start_time=""
    local temp_list="ffmpeg_file_list.txt"

    # Function to merge the current ride
    merge_current_ride() {
        if [[ ${#current_ride[@]} -gt 0 ]]; then
            echo >"$temp_list"
            for ride_file in "${current_ride[@]}"; do
                echo "file '$ride_file'" >>"$temp_list"
            done

            local ride_end_time="$last_timestamp"
            output_file="${current_date}_${ride_start_time}-${ride_end_time}.mp4"

            cat "$temp_list"
            echo "Creating: $output_file"

            ffmpeg -f concat -safe 0 -i "$temp_list" -c copy "$output_file"

            if [[ $? -eq 0 ]]; then
                echo "Successfully created: $output_file"
            else
                echo "Failed to create: $output_file"
            fi

            current_ride=()
        fi
    }

    # Process files to group rides by time gaps
    for file in "${files[@]}"; do
        filename=$(basename "$file")
        date=$(echo "$filename" | cut -d'-' -f1 | cut -c3-)
        timestamp=$(echo "$filename" | cut -d'-' -f2 | cut -c1-6) # Extract timestamp (HHMMSS)

        if [[ "$date" != "$current_date" ]]; then
            # New date detected, reset variables and merge previous date's rides
            merge_current_ride
            current_date="$date"
            ride_start_time="$timestamp"
        fi

        if [[ -n "$last_timestamp" ]]; then
            # Calculate time difference in seconds
            last_seconds=$((10#${last_timestamp:0:2} * 3600 + 10#${last_timestamp:2:2} * 60 + 10#${last_timestamp:4:2}))
            current_seconds=$((10#${timestamp:0:2} * 3600 + 10#${timestamp:2:2} * 60 + 10#${timestamp:4:2}))
            time_diff=$((current_seconds - last_seconds))

            if ((time_diff > 121)); then
                # Time gap detected, merge current ride
                merge_current_ride
                ride_start_time="$timestamp"
            fi
        fi

        # Add the file to the current ride
        current_ride+=("$file")
        last_timestamp="$timestamp"
    done

    # Merge the last ride if any files are left
    merge_current_ride

    rm -f "$temp_list"
}

# Example usage
# Pass the directory containing the dashcam files as the first argument
if [[ $# -ne 1 ]]; then
    echo "Usage: $0 /path/to/dashcam/files"
    exit 1
fi

merge_dashcam_videos "$1"
echo "Done."
