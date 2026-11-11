// Macro kiểm tra đơn giản cho unit test: sai thì in vị trí và thoát với mã 1.
#ifndef CHECK_H
#define CHECK_H

#include <stdio.h>
#include <stdlib.h>

#define CHECK(cond) \
    do { \
        if (!(cond)) { \
            fprintf(stderr, "%s:%d: CHECK FAILED: %s\n", __FILE__, __LINE__, #cond); \
            exit(1); \
        } \
    } while (0)

#endif
