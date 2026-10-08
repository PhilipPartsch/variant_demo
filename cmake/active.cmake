# Active copies for the IDE, ubc and the codelinks fallback (K§7 6.6, B§6.2.3).
# build/active/ always describes the product configured last (normally the one
# selected in CMake Tools). build/compile_commands.json is copied by CMake Tools
# (cmake.copyCompileCommands) or tools/build_product.sh.

if(CV_UPDATE_ACTIVE)
  file(MAKE_DIRECTORY "${CV_ACTIVE}")
  file(COPY_FILE "${KCONFIG_OUT}/variants.json" "${CV_ACTIVE}/variants.json" ONLY_IF_DIFFERENT)
  file(COPY_FILE "${KCONFIG_OUT}/autoconf.h" "${CV_ACTIVE}/autoconf.h" ONLY_IF_DIFFERENT)
  file(COPY_FILE "${CV_BMS_FILE}" "${CV_ACTIVE}/bms.needs.json" ONLY_IF_DIFFERENT)
  file(CONFIGURE OUTPUT "${CV_ACTIVE}/VARIANT" CONTENT "${VARIANT}\n")
endif()
cmake_path(GET CV_BMS_FILE FILENAME _bms)
message(STATUS "Product: ${VARIANT} (BMS: ${_bms}, build type: ${CMAKE_BUILD_TYPE})")
