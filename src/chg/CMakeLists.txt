add_library(chg STATIC chg.c session.c interface.c mcs.c pantograph.c)
target_include_directories(chg PUBLIC include)
