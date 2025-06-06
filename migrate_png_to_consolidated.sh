#!/bin/bash
# migrate_png_to_consolidated.sh
#
# This script migrates existing PNG files from their individual processing folders
# to the consolidated png_outputs directory.
#
# Usage:
#   ./migrate_png_to_consolidated.sh <region_name>
#
# Example:
#   ./migrate_png_to_consolidated.sh FoxIsland

# Check if a region name was provided
if [ $# -lt 1 ]; then
  echo "Usage: $0 <region_name>"
  echo "Example: $0 FoxIsland"
  exit 1
fi

REGION_NAME="$1"
BASE_DIR="output/$REGION_NAME/lidar"
CONSOLIDATED_DIR="$BASE_DIR/png_outputs"

# Create the consolidated directory if it doesn't exist
mkdir -p "$CONSOLIDATED_DIR"
echo "Created consolidated directory: $CONSOLIDATED_DIR"

# Process each processing type
PROCESSING_TYPES=("DTM" "DSM" "Hillshade" "Slope" "Aspect" "TRI" "TPI" "Roughness")

for TYPE in "${PROCESSING_TYPES[@]}"; do
  TYPE_LOWER=$(echo "$TYPE" | tr '[:upper:]' '[:lower:]')
  TYPE_DIR="$BASE_DIR/$TYPE"
  
  if [ -d "$TYPE_DIR" ]; then
    echo "Processing $TYPE_DIR..."
    
    # Find all PNG files in the processing type directory
    find "$TYPE_DIR" -name "*.png" | while read PNG_FILE; do
      PNG_BASENAME=$(basename "$PNG_FILE")
      
      # Skip if it's already in the consolidated format
      if [[ "$PNG_BASENAME" == *"_elevation_"* ]]; then
        continue
      fi
      
      # Special handling for Hillshade with parameters
      if [[ "$TYPE" == "Hillshade" && "$PNG_BASENAME" == *"_315_45_08"* ]]; then
        TARGET_NAME="${REGION_NAME}_elevation_${TYPE_LOWER}_315_45_08.png"
      else
        TARGET_NAME="${REGION_NAME}_elevation_${TYPE_LOWER}.png"
      fi
      
      TARGET_PATH="$CONSOLIDATED_DIR/$TARGET_NAME"
      
      # Copy the PNG file to the consolidated directory
      cp "$PNG_FILE" "$TARGET_PATH"
      echo "  Copied: $PNG_FILE -> $TARGET_PATH"
      
      # Copy the worldfile if it exists
      WORLD_FILE="${PNG_FILE%.*}.pgw"
      TARGET_WORLD="${TARGET_PATH%.*}.pgw"
      if [ -f "$WORLD_FILE" ]; then
        cp "$WORLD_FILE" "$TARGET_WORLD"
        echo "  Copied worldfile: $WORLD_FILE -> $TARGET_WORLD"
      fi
    done
  else
    echo "Directory not found: $TYPE_DIR (skipping)"
  fi
done

echo "Migration complete!"
echo "PNG files have been consolidated in: $CONSOLIDATED_DIR"
