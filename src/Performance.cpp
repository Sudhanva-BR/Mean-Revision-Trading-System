#include "Performance.h"

#include <iostream>
#include <cmath>
#include <iomanip>
#include <algorithm>
#include <numeric>

double Performance::calculate(
    const std::vector<EquityPoint>& equityHistory,
    double initialCapital
) {
    if (equityHistory.size() < 2 || initialCapital <= 0.0) {
        std::cout << "Insufficient equity data.\n";
        return 0.0;
    }

    std::vector<double> dailyReturns;

    // Calculate daily returns
    for (size_t i = 1; i < equityHistory.size(); i++) {

        double previousEquity = equityHistory[i - 1].totalEquity;
        double currentEquity = equityHistory[i].totalEquity;

        if (previousEquity <= 0.0) {
            std::cout << "Invalid equity value.\n";
            return 0.0;
        }

        double dailyReturn =
            (currentEquity - previousEquity) / previousEquity;

        dailyReturns.push_back(dailyReturn);
    }

    // Total portfolio return
    double finalEquity = equityHistory.back().totalEquity;

    double totalReturn =
        ((finalEquity - initialCapital) / initialCapital) * 100.0;

    // Average daily return
    double meanReturn =
        std::accumulate(
            dailyReturns.begin(),
            dailyReturns.end(),
            0.0
        ) / dailyReturns.size();

    // Daily standard deviation (sample)
    double variance = 0.0;

    for (double r : dailyReturns) {
        variance += (r - meanReturn) * (r - meanReturn);
    }

    variance /= (dailyReturns.size() - 1);

    double dailyStdDev = std::sqrt(variance);

    // Annualized Sharpe ratio (assuming zero risk-free rate)
    double sharpeRatio = 0.0;

    if (dailyStdDev > 0.0) {
        sharpeRatio =
            (meanReturn / dailyStdDev) * std::sqrt(252.0);
    }

    // Maximum drawdown
    double peakEquity = equityHistory[0].totalEquity;
    double maxDrawdown = 0.0;

    for (const auto& point : equityHistory) {

        peakEquity = std::max(peakEquity, point.totalEquity);

        double drawdown =
            (peakEquity - point.totalEquity) / peakEquity;

        maxDrawdown = std::max(maxDrawdown, drawdown);
    }

    // Print results
    std::cout << std::fixed << std::setprecision(4);

    std::cout << "\n========== PERFORMANCE REPORT ==========\n";

    std::cout << "Initial Capital: "
              << initialCapital << '\n';

    std::cout << "Final Equity: "
              << finalEquity << '\n';

    std::cout << "Total Return: "
              << totalReturn << "%\n";

    std::cout << "Annualized Sharpe Ratio: "
              << sharpeRatio << '\n';

    std::cout << "Maximum Drawdown: "
              << maxDrawdown * 100.0 << "%\n";

    std::cout << "========================================\n";

    return totalReturn;
}
