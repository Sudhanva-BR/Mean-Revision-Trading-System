#include "Backtester.h"
#include "Strategy.h"

#include <cmath>

std::vector<Trade> Backtester::run(
    const std::vector<Candle>& candles,
    const std::vector<Indicator>& indicators,
    double transactionCostRate,
    double slippageRate
) {
    std::vector<Trade> trades;

    if (candles.size() != indicators.size() ||
        transactionCostRate < 0.0 ||
        slippageRate < 0.0 ||
        slippageRate >= 1.0) {
        return trades;
    }

    bool hasPosition = false;
    double entryPrice = 0.0;
    double entryCost = 0.0;
    std::string entryDate;

    for (size_t i = 0; i + 1 < candles.size(); i++) {

        Signal signal = Strategy::generateSignal(
            indicators[i].zScore,
            hasPosition
        );

        double nextOpen = candles[i + 1].open;

        if (!std::isfinite(nextOpen) || nextOpen <= 0.0)
            continue;

        if (signal == Signal::BUY && !hasPosition) {

            // Slippage increases buying price
            entryPrice = nextOpen * (1.0 + slippageRate);

            entryCost = entryPrice * transactionCostRate;
            entryDate = candles[i + 1].date;

            hasPosition = true;
        }

        else if (signal == Signal::SELL && hasPosition) {

            // Slippage decreases selling price
            double exitPrice =
                nextOpen * (1.0 - slippageRate);

            double exitCost =
                exitPrice * transactionCostRate;

            Trade trade;

            trade.entryDate = entryDate;
            trade.exitDate = candles[i + 1].date;

            trade.entryPrice = entryPrice;
            trade.exitPrice = exitPrice;

            trade.grossProfitLoss =
                exitPrice - entryPrice;

            trade.transactionCosts =
                entryCost + exitCost;

            trade.netProfitLoss =
                trade.grossProfitLoss - trade.transactionCosts;

            trades.push_back(trade);

            hasPosition = false;
        }
    }

    // Close remaining position at final closing price
    if (hasPosition && !candles.empty()) {

        double finalPrice = candles.back().close;

        if (std::isfinite(finalPrice) && finalPrice > 0.0) {

            double exitPrice =
                finalPrice * (1.0 - slippageRate);

            double exitCost =
                exitPrice * transactionCostRate;

            Trade trade;

            trade.entryDate = entryDate;
            trade.exitDate = candles.back().date;

            trade.entryPrice = entryPrice;
            trade.exitPrice = exitPrice;

            trade.grossProfitLoss =
                exitPrice - entryPrice;

            trade.transactionCosts =
                entryCost + exitCost;

            trade.netProfitLoss =
                trade.grossProfitLoss - trade.transactionCosts;

            trades.push_back(trade);
        }
    }

    return trades;
}