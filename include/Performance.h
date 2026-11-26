#pragma once

#include "PaperTrader.h"
#include <vector>

struct TradeMetrics {
    int totalTrades = 0;
    int winningTrades = 0;
    int losingTrades = 0;
    double winRate = 0.0;       // Percentage (0-100)
    double grossProfits = 0.0;
    double grossLosses = 0.0;
    double profitFactor = 0.0;
};

class Performance {
public:
    static double calculate(
        const std::vector<EquityPoint>& equityHistory,
        double initialCapital
    );

    static TradeMetrics calculateTradeMetrics(
        const std::vector<PaperTrade>& trades
    );
};
