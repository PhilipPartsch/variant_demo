add_library(eng STATIC eng.c fuel.c torque.c)
target_include_directories(eng PUBLIC include)
