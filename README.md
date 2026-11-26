# C++ Mean Reversion Trading System

A quantitative trading system that implements a **mean reversion strategy** using statistical indicators (Z-Score, SMA, Standard Deviation) with backtesting, paper trading, parameter optimization, and benchmark comparison.

## Features

- **Market Data Loading** — Parses OHLCV data from CSV files
- **Technical Indicators** — SMA, Standard Deviation, and Z-Score calculation
- **Mean Reversion Strategy** — Signal generation based on Z-Score thresholds
- **Paper Trading** — Simulated execution with transaction costs and slippage
- **Backtesting Engine** — Historical strategy evaluation
- **Performance Analysis** — Total return, Sharpe ratio, and maximum drawdown
- **Buy & Hold Benchmark** — Strategy comparison against passive investing
- **Parameter Optimization** — Grid search over trading parameters
- **Unit Tests** — Automated testing of core components

## Project Structure

```
├── CMakeLists.txt           # Build configuration
├── download_data.py         # Stock data downloader (yfinance)
├── data/                    # Market data (CSV)
├── include/                 # Header files
│   ├── MarketData.h
│   ├── Indicators.h
│   ├── Strategy.h
│   ├── Backtester.h
│   ├── PaperTrader.h
│   ├── Performance.h
│   ├── Benchmark.h
│   ├── DataSplitter.h
│   └── ParameterOptimizer.h
├── src/                     # Source files
│   ├── main.cpp
│   ├── MarketData.cpp
│   ├── Indicators.cpp
│   ├── Strategy.cpp
│   ├── Backtester.cpp
│   ├── PaperTrader.cpp
│   ├── Performance.cpp
│   ├── Benchmark.cpp
│   ├── DataSplitter.cpp
│   └── ParameterOptimizer.cpp
└── tests/
    └── tests.cpp            # Unit tests
```

## Requirements

- **C++17** compiler (GCC, Clang, or MSVC)
- **CMake** 3.20+
- **Ninja** (or another CMake generator)
- **Python 3** with `yfinance` (for downloading data)

## Build & Run

```bash
# Download stock data
pip install yfinance
python download_data.py

# Configure and build
cmake -S . -B build -G Ninja
cmake --build build

# Run the trading system
./build/MeanReversion

# Run unit tests
./build/MeanReversionTests
```

## Strategy Overview

The mean reversion strategy operates on the principle that stock prices tend to revert to their historical mean:

1. **Buy Signal** — When the Z-Score drops below −2.0 (price is 2 standard deviations below the mean)
2. **Sell Signal** — When the Z-Score returns to 0.0 (price reverts to the mean)
3. **Risk Exit** — When the Z-Score drops below −3.0 (stop-loss to limit downside)

## License

This project is for educational purposes.
