# Build 4 chương trình dạng tĩnh vào build/, `make test` chạy unit test.
CC      = gcc
CFLAGS  = -O2 -Wall -Wextra -std=c11 -D_GNU_SOURCE -Isrc
LDFLAGS = -static

MAINS   = server client attacker guard
HEADERS = $(wildcard src/*.h)
# Các module dùng chung = mọi file .c trong src/ trừ các file có main()
LIB_SRC = $(filter-out $(addprefix src/,$(addsuffix .c,$(MAINS))),$(wildcard src/*.c))
TESTS   = $(patsubst tests/%.c,build/tests/%,$(wildcard tests/test_*.c))

.PHONY: all test clean

all: $(addprefix build/,$(MAINS))

build/tests/%: tests/%.c $(LIB_SRC) $(HEADERS) tests/check.h
	@mkdir -p build/tests
	$(CC) $(CFLAGS) -Itests -o $@ $< $(LIB_SRC)

build/%: src/%.c $(LIB_SRC) $(HEADERS)
	@mkdir -p build
	$(CC) $(CFLAGS) -o $@ $< $(LIB_SRC) $(LDFLAGS)

test: $(TESTS)
	@for t in $(TESTS); do \
		./$$t || exit 1; \
	done

clean:
	rm -rf build
