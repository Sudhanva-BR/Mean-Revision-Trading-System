
#include "MarketData.h"
#include "Indicators.h"
#include "Strategy.h"
#include "PaperTrader.h"
#include "Performance.h"
#include "Benchmark.h"
#include "DataSplitter.h"
#include "ParameterOptimizer.h"

#include <iostream>
#include <iomanip>
#include <vector>
#include <exception>

int main() {

    // 1. Load historical stock data
    auto candles = MarketData::loadCSV("data/RELIANCE.csv");

    if (candles.empty()) {
        std::cout << "No market data found!\n";
        return 1;
    }

    std::cout << "Total Candles: " << candles.size() << '\n';

    // 2. Split data into training and testing periods
    DataSplit split;

    try {
        split = DataSplitter::split(candles, 0.70);
    }
    catch (const std::exception& e) {
        std::cout << "Data split error: " << e.what() << '\n';
        return 1;
    }

    std::cout << "\n========== DATA SPLIT ==========\n";

    std::cout << "Training Candles: "
              << split.trainingData.size() << '\n';

    std::cout << "Testing Candles: "
              << split.testingData.size() << '\n';

    // 3. Check minimum data requirements
    const int window = 20;

    if (split.trainingData.size() < window ||
        split.testingData.size() < 2) {

        std::cout << "Insufficient data for testing.\n";
        return 1;
    }

    // 4. Prepare testing data
    // Include the previous 19 training candles
    // to calculate the first testing indicator.

    std::vector<Candle> testInput;

    testInput.insert(
        testInput.end(),
        split.trainingData.end() - (window - 1),
        split.trainingData.end()
    );

    testInput.insert(
        testInput.end(),
        split.testingData.begin(),
        split.testingData.end()
    );

    // 5. Calculate indicators
    auto testIndicators =
        Indicators::calculate(testInput, window);

    // 6. Create a fresh portfolio for testing
    const double initialCapital = 100000.0;

    PaperTrader testTrader(
        initialCapital,
        0.10,       // 10% capital allocation
        0.001,      // Transaction cost: 0.1%
        0.0005      // Slippage: 0.05%
    );

    std::cout << "\n========== TESTING PERIOD ==========\n";

    std::cout << "Start Date: "
              << split.testingData.front().date << '\n';

    std::cout << "End Date: "
              << split.testingData.back().date << '\n';

    // 7. Record initial testing-period equity
    // No position is held at the start.
    testTrader.recordEquity(
        split.testingData.front().date,
        split.testingData.front().close
    );

    // 8. Run Mean Reversion strategy
    // Signal uses today's close.
    // Execution happens at the next day's open.

    for (size_t i = window - 1;
         i + 1 < testInput.size();
         i++) {

        Signal signal = Strategy::generateSignal(
            testIndicators[i].zScore,
            testTrader.isHoldingPosition()
        );

        testTrader.processSignal(
            signal,
            testInput[i + 1].date,
            testInput[i + 1].open
        );

        // Record daily equity.
        // The final day is recorded after liquidation.
        if (i + 1 != testInput.size() - 1) {

            testTrader.recordEquity(
                testInput[i + 1].date,
                testInput[i + 1].close
            );
        }
    }

    // 9. Close any remaining position at final day's close
    if (testTrader.isHoldingPosition()) {

        testTrader.processSignal(
            Signal::SELL,
            testInput.back().date,
            testInput.back().close
        );
    }

    // 10. Record final equity after liquidation
    testTrader.recordEquity(
        testInput.back().date,
        testInput.back().close
    );

    // 11. Print completed trades
    std::cout << "\n========== COMPLETED TRADES ==========\n";

    const auto& trades = testTrader.getTrades();

    for (const auto& trade : trades) {

        std::cout << "Entry Date: " << trade.entryDate
                  << " | Exit Date: " << trade.exitDate
                  << " | Quantity: " << trade.quantity
                  << " | Net P&L: " << trade.netProfitLoss
                  << '\n';
    }

    std::cout << "Total Trades: " << trades.size() << '\n';

    // 12. Calculate strategy performance
    std::cout << "\n========== STRATEGY PERFORMANCE ==========\n";

    double strategyReturn = Performance::calculate(
        testTrader.getEquityHistory(),
        initialCapital
    );

    TradeMetrics tradeMetrics =
        Performance::calculateTradeMetrics(trades);

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "Win Rate: " << tradeMetrics.winRate << "% ("
              << tradeMetrics.winningTrades << "W / "
              << tradeMetrics.losingTrades << "L)\n";
    std::cout << "Profit Factor: " << tradeMetrics.profitFactor << '\n';

    // 13. Calculate Buy-and-Hold benchmark
    double benchmarkReturn =
        Benchmark::calculateBuyAndHoldReturn(
            split.testingData
        );

    // 14. Compare strategy against benchmark
    std::cout << "\n========== BENCHMARK COMPARISON ==========\n";

    std::cout << std::fixed << std::setprecision(4);

    std::cout << "Mean Reversion Return: "
              << strategyReturn << "%\n";

    std::cout << "Buy and Hold Return: "
              << benchmarkReturn << "%\n";

    std::cout << "Difference: "
              << strategyReturn - benchmarkReturn << "%\n";

    // 15. Final portfolio details
    std::cout << "\n========== FINAL PORTFOLIO ==========\n";

    std::cout << "Initial Capital: "
              << initialCapital << '\n';

    std::cout << "Final Cash Balance: "
              << testTrader.getCashBalance() << '\n';

    std::cout << "Final Equity: "
              << testTrader.getEquity(testInput.back().close) << '\n';

    std::cout << "\nBacktesting completed.\n";

    Parameters bestParameters =
    ParameterOptimizer::optimize(split.trainingData);

    return 0;
}
