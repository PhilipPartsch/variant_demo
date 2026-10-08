# CV platform: product selection, variant data, components, docs (K§7, B§6).
#
# The product is the only choice: -DVARIANT=<product> (configs/<product>_defconfig),
# picked in the CMake Tools status bar (.vscode/cmake-variants.json). The build
# type is always Debug and not part of the variant model.
cmake_minimum_required(VERSION 3.24)
project(cv_platform C)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type (fixed: Debug)" FORCE)
endif()
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(VARIANT "" CACHE STRING "Product = configs/<VARIANT>_defconfig")
option(CV_UPDATE_ACTIVE "Refresh build/active/ (the product the IDE and ubc see)" ON)

include(cmake/kconfig.cmake)   # VARIANT -> variant data, CONFIG_* variables
include(cmake/bms.cmake)       # BMS needs of the product's chemistry
include(cmake/active.cmake)    # active copies in build/active/
include(cmake/docs.cmake)      # docs / docs_ubc targets

# --- components (K§7 6.4) ----------------------------------------------------
include_directories("${KCONFIG_OUT}")   # autoconf.h
add_subdirectory(src/vcu)
if(CONFIG_POWERTRAIN__TYPE__BEV)
  add_subdirectory(src/chg)
endif()
if(CONFIG_POWERTRAIN__TYPE__DIESEL)
  add_subdirectory(src/eng)
endif()

# --- tests (CTest); every traced .c file is built (B§6.2.6) ------------------
enable_testing()
add_subdirectory(tests)
