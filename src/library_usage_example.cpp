#if __has_include(<DriveTrain.hpp>)
#include <DriveTrain.hpp>

extern "C" void xbot_library_usage_example(void) {
    DriveTrain bot(0, 1);
    bot.setTicksPerRevolution(1400.0f);
    bot.setWheelDiameter(7.0f);
    bot.setTrackWidth(15.0f);
    bot.stop();
}
#else
extern "C" void xbot_library_usage_example(void) {}
#endif
