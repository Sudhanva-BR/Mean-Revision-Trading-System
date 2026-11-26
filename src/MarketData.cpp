#include "MarketData.h"

#include <fstream>
#include <sstream>
#include <iostream>

std::vector<Candle> MarketData::loadCSV(
    const std::string& filename
) {
    std::vector<Candle> candles;

    std::ifstream file(filename);

    if (!file.is_open()) {
        std::cerr << "Could not open: " << filename << '\n';
        return candles;
    }

    std::string line;
    std::getline(file, line); // Skip header

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string field;

        Candle candle{};

        try {
            std::getline(ss, candle.date, ',');

            std::getline(ss, field, ',');
            candle.open = std::stod(field);

            std::getline(ss, field, ',');
            candle.high = std::stod(field);

            std::getline(ss, field, ',');
            candle.low = std::stod(field);

            std::getline(ss, field, ',');
            candle.close = std::stod(field);

            std::getline(ss, field, ',');
            candle.volume = std::stoll(field);

            candles.push_back(candle);
        }
        catch (const std::exception&) {
            std::cerr << "Skipping invalid row: "
                      << line << '\n';
        }
    }

    return candles;
}