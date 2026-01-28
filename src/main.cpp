#include <iostream>
#include <kipr/wombat.h>
#include "../lib/DriveTrain/include/DriveTrain.hpp"

int main()
{
    std::cout << "Hello, World!" << std::endl;
    
    std::cout << "[STARTED]" << " " << "Test Started" << std::endl;
    
    // Initialize the DriveTrain
    DriveTrain bot(1, 2);
    
    // Configure DriveTrain object
    bot.setPerformanceRatings(100, 100);
    bot.setWheelDiameter(7);
    bot.setTrackWidth(15);
    bot.setTicksPerRevolution(1400);
    
    // Drive forward for 20 cm
    bot.moveForward(100, 20);
    
    // Drive backward for 20cm
    bot.moveBackward(100, 20);
    
    // Rotate right for 90 degrees
    bot.rotateClockwise(100, 90);
    
    // Rotate left for 90 degrees
    bot.rotateCounterClockwise(100, 90);
    
    // Print test complete
    std::cout << "[FINISHED]" << " " << "Test Completed" << std::endl;
    
    return 0;
}