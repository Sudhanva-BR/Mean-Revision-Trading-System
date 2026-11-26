#pragma once

#include "MarketData.h"
#include "Indicators.h"

#include <vector>
#include <string>

struct Trade {
    std::string entryDate;
    std::string exitDate;

    double entryPrice;
    double exitPrice;

    double grossProfitLoss;
    double transactionCosts;
    double netProfitLoss;
};

class Backtester {
public:
    static std::vector<Trade> run(
        const std::vector<Candle>& candles,
        const std::vector<Indicator>& indicators,
        double transactionCostRate = 0.001,
        double slippageRate = 0.0005
    );
};