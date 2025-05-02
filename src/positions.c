#include "../include/positions.h"

/*  */
shoulderPositions shoulderPos = {
    .starting = 1564, //
    .vertical = 1700, //
    .ground = 1498, //
    .PVC = 2000, //
    .strafe = 2040, //
    .potato = 1350,
    .drop = 1756
};

/* Pre-Set Positions on the Elbow Hinge*/
elbowPositions elbowPos = {
    .starting = 2047, //
    .parallelToShoulder = 208, //
    .perpendicularToShoulder = 1580, //
    .ground = 2047, //
    .PVC = 1568, //
    .strafe = 967, //
    .potato = 1818,
    .drop = 308
};

/*  */
wristPositions wristPos = {
    .starting = 33, //
    .parallelToArm = 982, //
    .perpendicularUpwards = 0, //
    .perpedincularDownwards = 2015, //
    .ground = 33, //
    .PVC = 385, //
    .strafe = 250,
    .potato = 463,
    .drop = 1838
};

/*  */
clawPositions clawPos = {
    .open = 500,
    .closedPoms = 1750,
    .closedPotato = 1650,
    .closedBox = 944
}; 

RobotState robotState = {
    .x = 0.0,
    .y = 0.0,
    .theta = 0.0
};