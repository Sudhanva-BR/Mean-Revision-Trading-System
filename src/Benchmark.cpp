#include "Benchmark.h"

#include <iostream>
#include <cmath>

double Benchmark::calculateBuyAndHoldReturn(
    const std::vector<Candle>& candles
) {
    if (candles.size() < 2)
        return 0.0;

    double initialPrice = candles.front().close;
    double finalPrice = candles.back().close;

    if (initialPrice <= 0.0)
        return 0.0;

    double buyAndHoldReturn =
        ((finalPrice - initialPrice) / initialPrice) * 100.0;

    return buyAndHoldReturn;
}