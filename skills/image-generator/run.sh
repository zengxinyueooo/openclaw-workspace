#!/bin/bash

# Get the prompt and optional reference picture URLs from the arguments
PROMPT="$1"
REFERENCE_PICS_STRING="$2"

# Check if reference pictures are provided
if [ -z "$REFERENCE_PICS_STRING" ]; then
  # If not, create a JSON payload with an empty list
  JSON_DATA=$(cat <<EOF
{
  "referencePicList": [],
  "prompt": "$PROMPT",
  "size": "3:4",
  "scale": "1k",
  "num": 1
}
EOF
  )
else
  # If yes, process the picture URLs into a JSON array
  JSON_PICS=""
  IFS=',' read -ra ADDR <<< "$REFERENCE_PICS_STRING"
  for i in "${ADDR[@]}"; do
      JSON_PICS+="\"$i\","
  done
  # Remove the trailing comma
  JSON_PICS=${JSON_PICS%?}

  # Construct the JSON data payload with pictures
  JSON_DATA=$(cat <<EOF
{
  "referencePicList": [
    $JSON_PICS
  ],
  "prompt": "$PROMPT",
  "size": "3:4",
  "scale": "1k",
  "num": 1
}
EOF
  )
fi

# Call the API. The -s flag makes it silent!
curl -s --location --request POST 'https://mdz.dzu.test.sankuai.com/api/dzusergrowth/assistant/workFlow/callBananaPro' \
--header 'swimlane: 3792-tsgru' \
--header 'Content-Type: application/json' \
--data-raw "$JSON_DATA"
