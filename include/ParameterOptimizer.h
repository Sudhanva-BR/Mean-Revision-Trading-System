
#pragma once

#include "MarketData.h"

struct Parameters {
    int window;
    double buyThreshold;
    double riskExitThreshold;
    double sellThreshold;
};

class ParameterOptimizer {
public:
    static Parameters optimize(
        const std::vector<Candle>& trainingData
    );
};
