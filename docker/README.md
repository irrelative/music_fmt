# How to run

`docker run -v "$(pwd)":/workdir -e PUID=$(id -u) -e PGID=$(id -g) -it dockerflac bash`

`find . -name "*.flac" -print0 | xargs -0 -n1 -P2 flac2mp3.sh`


# Build a new image
`docker build -t dockerflac .`
