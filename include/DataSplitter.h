#pragma once

#include "MarketData.h"
#include <vector>

struct DataSplit {
    std::vector<Candle> trainingData;
    std::vector<Candle> testingData;
};

class DataSplitter {
public:
    static DataSplit split(
        const std::vector<Candle>& candles,
        double trainingRatio = 0.70
    );
};