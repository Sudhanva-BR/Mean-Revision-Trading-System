#include "Strategy.h"
#include <cmath>

Signal Strategy::generateSignal(
    double zScore,
    bool hasPosition,
    double buyThreshold,
    double riskExitThreshold,
    double sellThreshold
) {
    if (!std::isfinite(zScore))
        return Signal::HOLD;

    if (hasPosition && zScore <= riskExitThreshold)
        return Signal::SELL;

    if (hasPosition && zScore >= sellThreshold)
        return Signal::SELL;

    if (!hasPosition && zScore <= buyThreshold &&
        zScore > riskExitThreshold)
        return Signal::BUY;

    return Signal::HOLD;
}