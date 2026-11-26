#include "PaperTrader.h"

#include <cmath>
#include <stdexcept>

PaperTrader::PaperTrader(
    double capital,
    double allocation,
    double costRate,
    double slipRate
)
    : initialCapital(capital),
      cashBalance(capital),
      allocationPercent(allocation),
      transactionCostRate(costRate),
      slippageRate(slipRate) {

    if (capital <= 0.0 ||
        allocation <= 0.0 || allocation > 1.0 ||
        costRate < 0.0 ||
        slipRate < 0.0 || slipRate >= 1.0) {

        throw std::invalid_argument("Invalid trading parameters");
    }
}

void PaperTrader::processSignal(
    Signal signal,
    const std::string& date,
    double marketPrice
) {
    if (!std::isfinite(marketPrice) || marketPrice <= 0.0)
        return;

    // BUY
    if (signal == Signal::BUY && !hasPosition) {

        entryPrice = marketPrice * (1.0 + slippageRate);

        // Allocate only a percentage of available cash
        double allocatedCash = cashBalance * allocationPercent;

        quantity = static_cast<int>(
            std::floor(
                allocatedCash /
                (entryPrice * (1.0 + transactionCostRate))
            )
        );

        if (quantity <= 0)
            return;

        entryCost = quantity * entryPrice * transactionCostRate;

        double purchaseAmount = quantity * entryPrice;

        cashBalance -= purchaseAmount + entryCost;

        entryDate = date;
        hasPosition = true;
    }

    // SELL
    else if (signal == Signal::SELL && hasPosition) {

        double exitPrice = marketPrice * (1.0 - slippageRate);

        double exitCost =
            quantity * exitPrice * transactionCostRate;

        double saleAmount = quantity * exitPrice;

        cashBalance += saleAmount - exitCost;

        PaperTrade trade;

        trade.entryDate = entryDate;
        trade.exitDate = date;

        trade.quantity = quantity;

        trade.entryPrice = entryPrice;
        trade.exitPrice = exitPrice;

        trade.grossProfitLoss =
            (exitPrice - entryPrice) * quantity;

        trade.transactionCosts = entryCost + exitCost;

        trade.netProfitLoss =
            trade.grossProfitLoss - trade.transactionCosts;

        completedTrades.push_back(trade);

        quantity = 0;
        hasPosition = false;
    }
}

const std::vector<PaperTrade>& PaperTrader::getTrades() const {
    return completedTrades;
}

bool PaperTrader::isHoldingPosition() const {
    return hasPosition;
}

double PaperTrader::getCashBalance() const {
    return cashBalance;
}

double PaperTrader::getEquity(double marketPrice) const {
    if (!hasPosition)
        return cashBalance;

    return cashBalance + quantity * marketPrice;
}

void PaperTrader::recordEquity(
    const std::string& date,
    double marketPrice
) {
    double marketValue = hasPosition
        ? quantity * marketPrice
        : 0.0;

    EquityPoint point;

    point.date = date;
    point.cash = cashBalance;
    point.marketValue = marketValue;
    point.totalEquity = cashBalance + marketValue;

    equityHistory.push_back(point);
}

const std::vector<EquityPoint>&
PaperTrader::getEquityHistory() const {
    return equityHistory;
}