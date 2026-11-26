cmake_minimum_required(VERSION 3.20)

project(MeanReversion)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

enable_testing()

# Main executable
add_executable(MeanReversion
        src/main.cpp
        src/MarketData.cpp
        src/Indicators.cpp
        src/Strategy.cpp
        src/Backtester.cpp
        src/Performance.cpp
        src/PaperTrader.cpp
        src/Benchmark.cpp
        src/DataSplitter.cpp
        src/ParameterOptimizer.cpp
)

target_include_directories(MeanReversion PRIVATE include)

# Test executable (separate target so it has its own main)
add_executable(MeanReversionTests
        tests/tests.cpp
        src/MarketData.cpp
        src/Indicators.cpp
        src/Strategy.cpp
        src/Backtester.cpp
        src/Performance.cpp
        src/PaperTrader.cpp
        src/Benchmark.cpp
        src/DataSplitter.cpp
        src/ParameterOptimizer.cpp
)

target_include_directories(MeanReversionTests PRIVATE
        ${CMAKE_SOURCE_DIR}/include
)

# Register tests
add_test(
        NAME TradingSystemTests
        COMMAND MeanReversionTests
)
