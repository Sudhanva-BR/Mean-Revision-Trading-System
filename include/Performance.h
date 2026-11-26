#pragma once

#include "PaperTrader.h"
#include <vector>

class Performance {
public:
    static double calculate(
        const std::vector<EquityPoint>& equityHistory,
        double initialCapital
    );
};