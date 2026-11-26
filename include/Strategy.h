#pragma once

enum class Signal {
    BUY,
    SELL,
    HOLD
};

class Strategy {
public:
    static Signal generateSignal(
        double zScore,
        bool hasPosition,
        double buyThreshold = -2.0,
        double riskExitThreshold = -3.0,
        double sellThreshold = 0.0
    );
};