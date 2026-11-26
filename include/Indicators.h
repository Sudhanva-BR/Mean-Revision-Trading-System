#pragma once

#include "MarketData.h"
#include <vector>

struct Indicator {
    double sma;
    double standardDeviation;
    double zScore;
};

class Indicators {
public:
    static std::vector<Indicator> calculate(
        const std::vector<Candle>& candles,
        int window = 20
        );
};