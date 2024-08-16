#!/bin/bash

# Create beets config directory if it doesn't exist
mkdir -p ~/.config/beets

# Create beets config file
cat << EOF > ~/.config/beets/config.yaml
directory: ~/Music
library: ~/Music/musiclibrary.db
import:
    move: no
plugins: fetchart lyrics
EOF

# Install beets and its plugins
pip install beets[fetchart,lyrics]

# Fetch MusicBrainz data
beet mb submenu update

echo "Beets setup completed."
