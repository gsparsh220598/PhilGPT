#!/bin/bash

# folder_path="source_documents/gpu/"

# # Find all .htm files recursively in the folder
# find "$folder_path" -type f -name "*.htm#*" | while read -r file; do
#     file_name=$(basename "$file" ".htm#*")

#     # Construct the new file path with the .html extension
#     new_file="${file%.*}.html"

#     # Rename the file
#     mv "$file" "$new_file"
# done

folder_path="source_documents/"

# Find all .htm files recursively in the folder
find "$folder_path" -type f -name "*.htm*" | while read -r file; do
    # Rename the file by changing the extension
    new_file="${file%.htm}.html"
    mv "$file" "$new_file"
done
