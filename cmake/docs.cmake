# `docs` (sphinx-needs) and `docs_ubc` (ubCode) HTML of the configured product
# into build/site/<product>/{sphinx,ubcode}/ (B§8). Both read build/active/, so
# they need CV_UPDATE_ACTIVE=ON (the default) and the copied compile database.

set(CV_SITE "${CMAKE_SOURCE_DIR}/build/site/${VARIANT}")
find_program(CV_SPHINX NAMES sphinx-build HINTS "${CMAKE_SOURCE_DIR}/.venv/bin")
if(DEFINED ENV{UBC})
  set(_ubc_hint "$ENV{UBC}")
else()
  # Prefer the ubc bundled with the ubCode extension (version-matched to the IDE).
  file(GLOB _ubc_hint LIST_DIRECTORIES false "$ENV{HOME}/.vscode/extensions/useblocks.ubcode-*/server/cli/ubc")
  list(SORT _ubc_hint COMPARE NATURAL ORDER DESCENDING)
  list(POP_FRONT _ubc_hint _ubc_hint)
endif()
find_program(CV_UBC NAMES ubc HINTS ${_ubc_hint})
if(_ubc_hint AND EXISTS "${_ubc_hint}")
  set(CV_UBC "${_ubc_hint}" CACHE FILEPATH "ubc executable" FORCE)
endif()

set(_copy_db "${CMAKE_COMMAND}" -E copy_if_different
  "${PROJECT_BINARY_DIR}/compile_commands.json" "${CMAKE_SOURCE_DIR}/build/compile_commands.json")

if(CV_SPHINX)
  add_custom_target(docs
    COMMAND ${_copy_db}
    COMMAND "${CV_SPHINX}" -E -W --keep-going -b html docs "${CV_SITE}/sphinx"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    USES_TERMINAL
    COMMENT "sphinx-needs HTML for ${VARIANT}")
endif()
if(CV_UBC)
  add_custom_target(docs_ubc
    COMMAND ${_copy_db}
    COMMAND "${CV_UBC}" build html -o "${CV_SITE}/ubcode"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    USES_TERMINAL
    COMMENT "ubCode HTML for ${VARIANT}")
endif()
