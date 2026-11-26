#pragma once

#include "Strategy.h"

#include <string>
#include <vector>

struct PaperTrade {
    std::string entryDate;
    std::string exitDate;

    int quantity = 0;

    double entryPrice = 0.0;
    double exitPrice = 0.0;

    double grossProfitLoss = 0.0;
    double transactionCosts = 0.0;
    double netProfitLoss = 0.0;
};

struct EquityPoint {
    std::string date;
    double cash;
    double marketValue;
    double totalEquity;
};

class PaperTrader {
private:
    bool hasPosition = false;

    int quantity = 0;

    double initialCapital;
    double cashBalance;
    double allocationPercent;

    double entryPrice = 0.0;
    double entryCost = 0.0;

    std::string entryDate;

    double transactionCostRate;
    double slippageRate;

    std::vector<PaperTrade> completedTrades;
    std::vector<EquityPoint> equityHistory;
public:
    PaperTrader(
        double capital = 100000.0,
        double allocation = 0.10,
        double costRate = 0.001,
        double slipRate = 0.0005
    );

    void processSignal(
        Signal signal,
        const std::string& date,
        double marketPrice
    );

    void recordEquity(
    const std::string& date,
    double marketPrice
);

    const std::vector<EquityPoint>& getEquityHistory() const;

    const std::vector<PaperTrade>& getTrades() const;

    bool isHoldingPosition() const;

    double getCashBalance() const;

    double getEquity(double marketPrice) const;
};