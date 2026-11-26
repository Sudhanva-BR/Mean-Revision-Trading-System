#include "MarketData.h"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>

namespace {

std::string trim(const std::string& s) {
    size_t start = 0;
    while (start < s.size() && std::isspace(static_cast<unsigned char>(s[start]))) {
        ++start;
    }
    size_t end = s.size();
    while (end > start && std::isspace(static_cast<unsigned char>(s[end - 1]))) {
        --end;
    }
    return s.substr(start, end - start);
}

std::string toLower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return s;
}

std::vector<std::string> splitCSVLine(const std::string& line) {
    std::vector<std::string> fields;
    std::stringstream ss(line);
    std::string field;
    while (std::getline(ss, field, ',')) {
        fields.push_back(trim(field));
    }
    return fields;
}

} // namespace

std::vector<Candle> MarketData::loadCSV(
    const std::string& filename
) {
    std::vector<Candle> candles;

    std::ifstream file(filename);

    if (!file.is_open()) {
        std::cerr << "Could not open: " << filename << '\n';
        return candles;
    }

    std::string headerLine;
    if (!std::getline(file, headerLine)) {
        return candles;
    }

    // Default column indices: Date, Open, High, Low, Close, Volume
    int dateIdx = 0;
    int openIdx = 1;
    int highIdx = 2;
    int lowIdx = 3;
    int closeIdx = 4;
    int volumeIdx = 5;

    // Detect column positions dynamically from CSV header
    auto headers = splitCSVLine(headerLine);
    int detectedDate = -1, detectedOpen = -1, detectedHigh = -1;
    int detectedLow = -1, detectedClose = -1, detectedVolume = -1;

    for (int i = 0; i < static_cast<int>(headers.size()); ++i) {
        std::string col = toLower(headers[i]);
        if (col == "date" || col == "timestamp") detectedDate = i;
        else if (col == "open") detectedOpen = i;
        else if (col == "high") detectedHigh = i;
        else if (col == "low") detectedLow = i;
        else if (col == "close") detectedClose = i;
        else if (col == "volume") detectedVolume = i;
    }

    if (detectedDate >= 0 && detectedOpen >= 0 && detectedHigh >= 0 &&
        detectedLow >= 0 && detectedClose >= 0 && detectedVolume >= 0) {
        dateIdx = detectedDate;
        openIdx = detectedOpen;
        highIdx = detectedHigh;
        lowIdx = detectedLow;
        closeIdx = detectedClose;
        volumeIdx = detectedVolume;
    }

    const int maxIdx = std::max({dateIdx, openIdx, highIdx, lowIdx, closeIdx, volumeIdx});

    std::string line;
    while (std::getline(file, line)) {
        if (trim(line).empty()) {
            continue;
        }

        auto fields = splitCSVLine(line);
        if (static_cast<int>(fields.size()) <= maxIdx) {
            std::cerr << "Skipping incomplete row: " << line << '\n';
            continue;
        }

        Candle candle{};
        try {
            candle.date = fields[dateIdx];
            candle.open = std::stod(fields[openIdx]);
            candle.high = std::stod(fields[highIdx]);
            candle.low = std::stod(fields[lowIdx]);
            candle.close = std::stod(fields[closeIdx]);
            candle.volume = static_cast<long long>(std::stod(fields[volumeIdx]));

            candles.push_back(candle);
        }
        catch (const std::exception&) {
            std::cerr << "Skipping invalid row: "
                      << line << '\n';
        }
    }

    return candles;
}
