#pragma once

#include <string>
#include <vector>

struct Candle {
    std::string date;
    double open;
    double high;
    double low;
    double close;
    long long volume;
};

class MarketData {
public:
    static std::vector<Candle> loadCSV(
        const std::string& filename
        );
};