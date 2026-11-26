
#include "MarketData.h"
#include "Indicators.h"
#include "Strategy.h"
#include "DataSplitter.h"
#include "PaperTrader.h"

#include <iostream>
#include <vector>
#include <cmath>
#include <cassert>

std::vector<Candle> createTestData(int count) {

    std::vector<Candle> candles;

    for (int i = 0; i < count; i++) {
        Candle candle;

        candle.date = "2026-01-01";
        candle.open = 100 + i;
        candle.high = 105 + i;
        candle.low = 95 + i;
        candle.close = 100 + i;
        candle.volume = 1000;

        candles.push_back(candle);
    }

    return candles;
}

void testIndicators() {

    auto candles = createTestData(20);

    auto indicators = Indicators::calculate(candles, 20);

    assert(indicators.size() == 20);

    // First 19 values should be unavailable
    assert(std::isnan(indicators[18].sma));

    // SMA of values 100 to 119 = 109.5
    assert(std::abs(indicators[19].sma - 109.5) < 0.0001);

    std::cout << "Indicators test passed\n";
}

void testStrategy() {

    assert(
        Strategy::generateSignal(-2.5, false)
        == Signal::BUY
    );

    assert(
        Strategy::generateSignal(0.5, true)
        == Signal::SELL
    );

    assert(
        Strategy::generateSignal(-3.5, true)
        == Signal::SELL
    );

    assert(
        Strategy::generateSignal(1.0, false)
        == Signal::HOLD
    );

    std::cout << "Strategy test passed\n";
}

void testDataSplitter() {

    auto candles = createTestData(100);

    DataSplit split = DataSplitter::split(candles, 0.70);

    assert(split.trainingData.size() == 70);
    assert(split.testingData.size() == 30);

    std::cout << "DataSplitter test passed\n";
}

void testPaperTrader() {

    PaperTrader trader(
        100000.0,
        0.10,
        0.001,
        0.0005
    );

    trader.processSignal(
        Signal::BUY,
        "2026-01-01",
        100.0
    );

    assert(trader.isHoldingPosition());

    assert(trader.getCashBalance() < 100000.0);

    trader.processSignal(
        Signal::SELL,
        "2026-01-02",
        110.0
    );

    assert(!trader.isHoldingPosition());

    assert(trader.getTrades().size() == 1);

    assert(trader.getTrades()[0].netProfitLoss > 0.0);

    std::cout << "PaperTrader test passed\n";
}

int main() {

    std::cout << "\nRunning Unit Tests...\n\n";

    testIndicators();
    testStrategy();
    testDataSplitter();
    testPaperTrader();

    std::cout << "\nAll unit tests passed!\n";

    return 0;
}
