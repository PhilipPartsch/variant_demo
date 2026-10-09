add_library(vcu STATIC vcu.c energy_display.c power_limit.c hv_shutdown.c door_interlock.c)
target_include_directories(vcu PUBLIC include)
