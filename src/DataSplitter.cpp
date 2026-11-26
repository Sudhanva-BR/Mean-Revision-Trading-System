#include "DataSplitter.h"

#include <stdexcept>

DataSplit DataSplitter::split(
    const std::vector<Candle>& candles,
    double trainingRatio
) {
    if (candles.size() < 2 ||
        trainingRatio <= 0.0 ||
        trainingRatio >= 1.0) {
        throw std::invalid_argument("Invalid data split parameters");
        }

    size_t splitIndex = static_cast<size_t>(
        candles.size() * trainingRatio
    );

    if (splitIndex == 0 || splitIndex >= candles.size()) {
        throw std::invalid_argument("Invalid split index");
    }

    DataSplit result;

    result.trainingData.assign(
        candles.begin(),
        candles.begin() + splitIndex
    );

    result.testingData.assign(
        candles.begin() + splitIndex,
        candles.end()
    );

    return result;
}