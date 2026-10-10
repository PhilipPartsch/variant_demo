/* Filtered fuel level. */
#include "eng/eng.h"

// @need: Report filtered fuel level, IMPL_ENG_FUEL_LEVEL_REPORT, [SWREQ_ENG_FUEL_LEVEL_REPORT]
int eng_fuel_level_percent(const int *samples, int n, int raw_full)
{
    long sum = 0;
    if (n <= 0 || raw_full <= 0) {
        return 0;
    }
    for (int i = 0; i < n; i++) {
        sum += samples[i];
    }
    return (int)((sum * 100 / n + raw_full / 2) / raw_full);
}
