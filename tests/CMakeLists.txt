# Tests mirror src/: one executable per built component. Every traced .c file
# must be in the compile database, or codelinks skips it (B§6.2.6).
foreach(component IN ITEMS vcu chg eng)
  if(TARGET ${component})
    add_executable(test_${component} ${component}/test_${component}.c)
    target_link_libraries(test_${component} PRIVATE ${component})
    add_test(NAME test_${component} COMMAND test_${component})
  endif()
endforeach()
