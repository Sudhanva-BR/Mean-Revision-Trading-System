#pragma once

#include "MarketData.h"

class Benchmark {
public:
    static double calculateBuyAndHoldReturn(
        const std::vector<Candle>& candles
    );
};