/*
 * Minimal libwallaby header stub for cross-compilation.
 *
 * This stub allows user code that includes <kipr/wombat.h> to compile
 * without the full libwallaby source tree. The real library is already
 * installed on the KIPR Wombat and linked at runtime.
 *
 * To use the full headers instead, fetch them with:
 *   zig fetch --save=libwallaby https://github.com/kipr/libwallaby/archive/refs/tags/v1.0.0.tar.gz
 *
 * Then rebuild — the build system will automatically pick up the
 * dependency's include path.
 */

#ifndef KIPR_WOMBAT_H
#define KIPR_WOMBAT_H

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Motor ---- */
void motor(int port, int speed);
int get_motor_position_counter(int port);
void clear_motor_position_counter(int port);
void set_motor_position_counter(int port, int value);
int get_motor_done(int port);
void move_at_velocity(int port, int velocity);
void move_to_position(int port, int speed, int goal_pos);
void move_relative_position(int port, int speed, int delta_pos);
void freeze(int port);
int motor_power(int port);
void off(int port);
void alloff(void);
void ao(void);

/* ---- Servo ---- */
void enable_servo(int port);
void disable_servo(int port);
void enable_servos(void);
void disable_servos(void);
void set_servo_position(int port, int position);
int get_servo_position(int port);
void set_servo_enabled(int port, int enabled);
int get_servo_enabled(int port);

/* ---- Analog ---- */
int analog(int port);
int analog_et(int port);
int analog10(int port);
int analog12(int port);

/* ---- Digital ---- */
int digital(int port);
void set_digital_value(int port, int value);
void set_digital_output(int port, int value);
int get_digital_value(int port);
int get_digital_pullup(int port);
void set_digital_pullup(int port, int pullup);

/* ---- Time ---- */
void msleep(long msecs);
double seconds(void);
unsigned long systime(void);

/* ---- Botball ---- */
void wait_for_light(int port);
void shut_down_in(double seconds);
void enable_extra_buttons(void);

/* ---- Button ---- */
int a_button(void);
int b_button(void);
int c_button(void);
int side_button(void);
int a_button_clicked(void);
int b_button_clicked(void);
int c_button_clicked(void);
int extra_buttons_show(void);

/* ---- Camera ---- */
int camera_open(void);
int camera_open_at_res(int res);
int camera_load_config(const char *name);
void camera_close(void);
int camera_update(void);
int get_object_count(int channel);
int get_object_area(int channel, int object);
int get_object_center_x(int channel, int object);
int get_object_center_y(int channel, int object);

/* ---- Display ---- */
void display_clear(void);
void display_printf(int col, int row, const char *fmt, ...);

/* ---- Audio ---- */
void beep(void);
void tone(int frequency, int duration);

/* ---- Battery ---- */
int power_level(void);

/* ---- Gyroscope ---- */
void gyro_calibrate(void);
int gyro_x(void);
int gyro_y(void);
int gyro_z(void);

/* ---- Accelerometer ---- */
int accel_x(void);
int accel_y(void);
int accel_z(void);

/* ---- Magneto ---- */
int magneto_x(void);
int magneto_y(void);
int magneto_z(void);

/* ---- Thread ---- */
typedef struct _thread *thread;
thread thread_create(void (*func)(void));
void thread_start(thread t);
void thread_wait(thread t);
void thread_destroy(thread t);
typedef struct _mutex *mutex;
mutex mutex_create(void);
void mutex_lock(mutex m);
int mutex_trylock(mutex m);
void mutex_unlock(mutex m);
void mutex_destroy(mutex m);

#ifdef __cplusplus
}
#endif

#endif /* KIPR_WOMBAT_H */
