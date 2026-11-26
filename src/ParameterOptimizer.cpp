
#include "ParameterOptimizer.h"
#include "Indicators.h"
#include "Strategy.h"
#include "PaperTrader.h"

#include <iostream>
#include <vector>
#include <cmath>
#include <stdexcept>

Parameters ParameterOptimizer::optimize(
    const std::vector<Candle>& trainingData
) {
    const double initialCapital = 100000.0;

    const std::vector<Parameters> configurations = {
        {10, -1.5, -3.0, 0.0},
        {10, -2.0, -3.0, 0.0},
        {20, -1.5, -3.0, 0.0},
        {20, -2.0, -3.0, 0.0},
        {30, -1.5, -3.0, 0.0},
        {30, -2.0, -3.0, 0.0}
    };

    if (trainingData.size() < 31) {
        throw std::invalid_argument(
            "Insufficient training data for optimization"
        );
    }

    Parameters bestParameters = configurations[0];
    double bestReturn = -1e100;

    std::cout << "\n========== PARAMETER OPTIMIZATION ==========\n";

    for (const auto& params : configurations) {

        auto indicators = Indicators::calculate(
            trainingData,
            params.window
        );

        PaperTrader trader(
            initialCapital,
            0.10,
            0.001,
            0.0005
        );

        trader.recordEquity(
            trainingData.front().date,
            trainingData.front().close
        );

        for (size_t i = params.window - 1;
             i + 1 < trainingData.size();
             i++) {

            Signal signal = Strategy::generateSignal(
                indicators[i].zScore,
                trader.isHoldingPosition(),
                params.buyThreshold,
                params.riskExitThreshold,
                params.sellThreshold
            );

            trader.processSignal(
                signal,
                trainingData[i + 1].date,
                trainingData[i + 1].open
            );

            if (i + 1 != trainingData.size() - 1) {
                trader.recordEquity(
                    trainingData[i + 1].date,
                    trainingData[i + 1].close
                );
            }
        }

        if (trader.isHoldingPosition()) {
            trader.processSignal(
                Signal::SELL,
                trainingData.back().date,
                trainingData.back().close
            );
        }

        trader.recordEquity(
            trainingData.back().date,
            trainingData.back().close
        );

        double finalEquity =
            trader.getCashBalance();

        double totalReturn =
            ((finalEquity - initialCapital) /
             initialCapital) * 100.0;

        std::cout
            << "Window: " << params.window
            << " | Buy: " << params.buyThreshold
            << " | Return: " << totalReturn << "%\n";

        if (totalReturn > bestReturn) {
            bestReturn = totalReturn;
            bestParameters = params;
        }
    }

    std::cout << "\n========== BEST PARAMETERS ==========\n";

    std::cout << "Window: "
              << bestParameters.window << '\n';

    std::cout << "Buy Threshold: "
              << bestParameters.buyThreshold << '\n';

    std::cout << "Risk Exit: "
              << bestParameters.riskExitThreshold << '\n';

    std::cout << "Sell Threshold: "
              << bestParameters.sellThreshold << '\n';

    std::cout << "Training Return: "
              << bestReturn << "%\n";

    return bestParameters;
}
