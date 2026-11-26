#include "Indicators.h"

#include <cmath>
#include <numeric>
#include <limits>

std::vector<Indicator> Indicators::calculate(
    const std::vector<Candle>& candles,
    int window
) {
    std::vector<Indicator> result(candles.size());

    const double nan =
        std::numeric_limits<double>::quiet_NaN();

    for (auto& indicator : result) {
        indicator = {nan, nan, nan};
    }

    if (window < 2 || candles.size() < window)
        return result;

    for (int i = window - 1;
         i < static_cast<int>(candles.size()); i++) {

        double sum = 0.0;

        // Calculate SMA
        for (int j = i - window + 1; j <= i; j++) {
            sum += candles[j].close;
        }

        double sma = sum / window;

        // Calculate variance
        double squaredSum = 0.0;

        for (int j = i - window + 1; j <= i; j++) {
            double diff = candles[j].close - sma;
            squaredSum += diff * diff;
        }

        double variance = squaredSum / (window - 1);
        double sd = std::sqrt(variance);

        // Calculate Z-score
        double zScore = nan;

        if (sd > 0.0) {
            zScore = (candles[i].close - sma) / sd;
        }

        result[i] = {sma, sd, zScore};
         }

    return result;
}