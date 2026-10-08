# BMS needs of the product's chemistry (B§5.3).
# The BMS release is pinned: third_party/bms/<CV_BMS_VERSION>/{nmc,lfp}.needs.json.
# Diesel products get an empty but valid needs.json, so the configuration is the
# same for every product.

set(CV_BMS_VERSION "0.1.0")   # keep in sync with [[needs.external_needs]] base_url (pin check)
set(CV_BMS_DIR "${CMAKE_SOURCE_DIR}/third_party/bms/${CV_BMS_VERSION}")

if(CONFIG_BMS__ENABLED AND CONFIG_BMS__CHEMISTRY__NMC)
  set(CV_BMS_FILE "${CV_BMS_DIR}/nmc.needs.json")
elseif(CONFIG_BMS__ENABLED AND CONFIG_BMS__CHEMISTRY__LFP)
  set(CV_BMS_FILE "${CV_BMS_DIR}/lfp.needs.json")
else()
  set(CV_BMS_FILE "${CMAKE_SOURCE_DIR}/third_party/bms/empty.needs.json")
endif()
if(NOT EXISTS "${CV_BMS_FILE}")
  cv_fail_configure("BMS needs file missing: ${CV_BMS_FILE}")
endif()
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${CV_BMS_FILE}")
