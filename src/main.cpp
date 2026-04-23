#include <iostream>
#include <kipr/wombat.h>
#include <Wombat-CC/Arm.hpp>
#include <Wombat-CC/Drivetrain.hpp>
#include <Wombat-CC/Utilities.hpp>

int main()
{
    std::cout << "Welcome to your Wombat CC project (C++)" << std::endl;
    std::cout << "Using KIPR libwallaby v" << KIPR_VERSION << std::endl;

    Wombat_CC::Utilities::ActivateKillSwitch();

    return 0;
}
