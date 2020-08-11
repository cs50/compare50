echo "=== Building match page ==="
export REACT_APP_BUILD_TARGET=match
npm run build
mv build/index.html ../compare50/_renderer/static/match.html

echo "=== Building home page ==="
export REACT_APP_BUILD_TARGET=home
npm run build
mv build/index.html ../compare50/_renderer/static/home.html
