# Kconfig -> variant data at configure time (K§7).
# Output: ${KCONFIG_OUT}/{variants.json,autoconf.h,autoconf.cmake,.config};
# every CONFIG_* symbol as a CMake variable (ON / OFF / value).

set(CV_ACTIVE "${CMAKE_SOURCE_DIR}/build/active")

# Remove the active copies, so no tool keeps showing a stale product (K§7 6.6).
function(cv_fail_configure msg)
  if(CV_UPDATE_ACTIVE)
    file(REMOVE "${CV_ACTIVE}/variants.json" "${CV_ACTIVE}/autoconf.h"
                "${CV_ACTIVE}/bms.needs.json" "${CV_ACTIVE}/VARIANT")
  endif()
  message(FATAL_ERROR "${msg}; active copies in build/active/ removed")
endfunction()

if(VARIANT STREQUAL "")
  cv_fail_configure("VARIANT not set: pick a product in CMake Tools or pass -DVARIANT=<product>")
endif()
set(CV_DEFCONFIG "${CMAKE_SOURCE_DIR}/configs/${VARIANT}_defconfig")
if(NOT EXISTS "${CV_DEFCONFIG}")
  cv_fail_configure("Unknown VARIANT '${VARIANT}' (no configs/${VARIANT}_defconfig)")
endif()

find_program(CV_PYTHON NAMES python3 HINTS "${CMAKE_SOURCE_DIR}/.venv/bin" NO_DEFAULT_PATH)
if(NOT CV_PYTHON)
  find_program(CV_PYTHON NAMES python3 REQUIRED)
endif()

set(KCONFIG_OUT "${PROJECT_BINARY_DIR}/kconfig")
file(GLOB_RECURSE _kconfig_files CONFIGURE_DEPENDS "${CMAKE_SOURCE_DIR}/Kconfig" "${CMAKE_SOURCE_DIR}/src/*/Kconfig")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
  ${_kconfig_files} "${CV_DEFCONFIG}" "${CMAKE_SOURCE_DIR}/tools/kconfig2variants.py")

execute_process(
  COMMAND "${CV_PYTHON}" "${CMAKE_SOURCE_DIR}/tools/kconfig2variants.py"
          "${CMAKE_SOURCE_DIR}/Kconfig" "${CV_DEFCONFIG}" "${KCONFIG_OUT}"
  RESULT_VARIABLE _gen_rc)
if(NOT _gen_rc EQUAL 0)
  cv_fail_configure("kconfig2variants failed for ${VARIANT}")
endif()
include("${KCONFIG_OUT}/autoconf.cmake")
