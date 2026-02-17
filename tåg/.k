export BUILD_LOG_LEVEL=DEBUG

go() {
    ./build --livejs --pretty tåg.html && cat tåg.html
}
